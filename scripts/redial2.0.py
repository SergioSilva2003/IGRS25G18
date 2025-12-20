import sys
import KSR as KSR

ACME_DOM = "acme.operador"

# Mandatory function - module initiation
def mod_init():
    KSR.info("===== Redial 2.0: Modulo Carregado =====\n")
    return kamailio()

def aor_Key():
    return KSR.pv.get("$tU") + "@" + KSR.pv.get("$td")

def deregister(aor):
    expire = KSR.hdr.get("Expires")
    if not expire: return False
    try:
        if int(expire.strip()) != 0: return False
    except: return False
    
    KSR.info("DE-REGISTER DETETADO (Expires: 0)\n")
    KSR.registrar.save("location", 0)
    return True

class kamailio:
    def __init__(self):
        KSR.info('===== kamailio class init =====\n')

    def child_init(self, rank):
        return 0

    # --- Função Auxiliar do Serviço Redial (MESSAGE) ---
    def ksr_redial_service(self, msg):
        if msg.Method != "MESSAGE": return -1
        if KSR.pv.get("$rU") != "redial": return -1

        sender_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
        valor_tabela = KSR.htable.sht_get("redial", sender_aor)

        if valor_tabela is None:
            KSR.sl.send_reply(403, "Forbidden - You must REGISTER first")
            return 1

        body = KSR.pv.get("$rb")
        if body and "ACTIVATE" in body:
            # Remove a palavra ACTIVATE e fica com a lista (ex: "carol dave")
            res = body.replace("ACTIVATE", "").strip()
            if len(res) > 0:
                KSR.htable.sht_sets("redial", sender_aor, res)    
                KSR.sl.send_reply(200, "OK - Updated: " + res)
                KSR.info(f"Redial: Lista de {sender_aor} atualizada para [{res}]\n")
            else:
                KSR.sl.send_reply(400, "Empty List")
            return 1
        
        return 1

    # ---------------------------------------------------------
    # ROTA PRINCIPAL (REQUEST ROUTE)
    # ---------------------------------------------------------
    def ksr_request_route(self, msg):
        
        if KSR.pv.get("$td") != ACME_DOM:
            KSR.sl.send_reply(403, "Forbidden Domain")
            return 1

        # --- MESSAGE ---
        if msg.Method == "MESSAGE":
            if self.ksr_redial_service(msg) == 1:
                return 1
            if KSR.registrar.lookup("location") == 1:
                KSR.tm.t_relay()
                return 1
            KSR.sl.send_reply(404, "Not Found")
            return 1

        # --- REGISTER ---
        if msg.Method == "REGISTER":
            aor = aor_Key()
            if deregister(aor):
                KSR.htable.sht_rm("redial", aor) 
                return 1 

            KSR.registrar.save("location", 0)
            # Cria entrada vazia se não existir
            if KSR.htable.sht_get("redial", aor) is None:
                KSR.htable.sht_sets("redial", aor, "") 
            return 1

        # --- INVITE (Onde a magia começa) ---
        if msg.Method == "INVITE":
            if KSR.registrar.lookup("location") == 1:
                
                # 1. Armar a armadilha de falha
                KSR.tm.t_on_failure("ksr_failure_route_redial")
                
                # 2. Guardar contexto (Quem ligou e reiniciar índice a 0)
                caller_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
                KSR.pv.sets("$avp(caller)", caller_aor)
                KSR.pv.sets("$avp(redial_idx)", "0") 
                
                KSR.rr.record_route()
                KSR.tm.t_relay()
                return 1
            else:
                KSR.sl.send_reply(404, "Not found")
                return 1

        if msg.Method in ["ACK", "BYE", "CANCEL"]:
            KSR.rr.loose_route()
            KSR.tm.t_relay()
            return 1

        KSR.sl.send_reply(405, "Method Not Allowed")
        return 1

    # ---------------------------------------------------------
    # ROTA DE FALHA (Versão "Forçar Execução")
    # ---------------------------------------------------------
    def ksr_failure_route_redial(self, msg):
        caller = str(KSR.pv.get("$avp(caller)"))
        status = str(KSR.pv.get("$rs"))
        
        KSR.info(f"!!! FALHA DETETADA !!! Status: {status} | Caller: {caller}\n")

        # 1. Tentar obter a lista IMEDIATAMENTE (sem 'if' de status)
        redial_list = KSR.htable.sht_get("redial", caller)
        
        # Se a lista estiver vazia ou for None, abortamos
        if redial_list is None or redial_list == "":
            KSR.info(f"REDIAL: {caller} não tem lista de remarcação ativa. Fim.\n")
            return 1
            
        KSR.info(f"REDIAL DEBUG: Lista encontrada -> '{redial_list}'\n")

        # 2. Processar a lista
        targets = redial_list.split()
        
        idx_val = KSR.pv.get("$avp(redial_idx)")
        if idx_val is not None:
            # Garante que é tratado como inteiro
            try:
                idx = int(idx_val)
            except:
                idx = 0
        else:
            idx = 0
        
        if idx < len(targets):
            next_user = targets[idx]
            next_uri = "sip:" + next_user + "@" + ACME_DOM
            
            KSR.info(f"REDIAL AÇÃO: Remarcando para {next_uri}\n")
            
            KSR.pv.sets("$ru", next_uri)
            KSR.pv.sets("$avp(redial_idx)", str(idx + 1))
            
            # Rearmar a falha para o próximo da lista
            KSR.tm.t_on_failure("ksr_failure_route_redial")
            KSR.tm.t_relay()
            return 1
        else:
            KSR.info("REDIAL: Fim da lista. Ninguém atendeu.\n")

        return 1
        