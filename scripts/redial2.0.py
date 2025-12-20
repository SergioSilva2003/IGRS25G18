import sys
import KSR as KSR

ACME_DOM = "acme.operador"
MAX_REDIAL = 5

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

    # ---------------------------------------------------------
    # ROTA PRINCIPAL (REQUEST ROUTE)
    # ---------------------------------------------------------
    def ksr_request_route(self, msg):
        
        # 1. Verificacao de Dominio
        if KSR.pv.get("$td") != ACME_DOM:
            KSR.sl.send_reply(403, "Forbidden Domain")
            return 1

        # ---------------------------------------------------------
        # PROCESSAR MENSAGENS (ACTIVATE/DEACTIVATE) + KPIs
        # ---------------------------------------------------------
        if msg.Method == "MESSAGE":
            if KSR.pv.get("$rU") != "redial":
                KSR.sl.send_reply(404, "Unknown User")
                return 1

            # Ler corpo da mensagem de forma segura
            body = KSR.pv.get("$rb")
            if body is None:
                KSR.sl.send_reply(400, "Empty Body")
                return 1

            if body.startswith("ACTIVATE"):
                parts = body.split()
                targets = parts[1:] 
                
                if len(targets) > 0:
                    user_list_str = " ".join(targets)
                    caller = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
                    
                    # --- KPI: Verificar estado anterior ---
                    old_list = KSR.htable.sht_get("redial", caller)
                    is_new_activation = (old_list is None or old_list == "")
                    
                    KSR.htable.sht_sets("redial", caller, user_list_str)
                    
                    # --- ATUALIZAÇÃO DOS KPIs ---
                    # KPI 1: Total de Ativações
                    total = KSR.htable.sht_get("redial", "KPI_TOTAL_ACTIVATIONS")
                    new_total = int(total) + 1 if total else 1
                    KSR.htable.sht_sets("redial", "KPI_TOTAL_ACTIVATIONS", str(new_total))
                    
                    # KPI 2: Utilizadores Ativos
                    if is_new_activation:
                        active = KSR.htable.sht_get("redial", "KPI_CURRENT_ACTIVE")
                        new_active = int(active) + 1 if active else 1
                        KSR.htable.sht_sets("redial", "KPI_CURRENT_ACTIVE", str(new_active))
                    
                    # KPI 3: Tamanho Máximo
                    current_len = len(targets)
                    max_len_val = KSR.htable.sht_get("redial", "KPI_MAX_LIST_SIZE")
                    max_len = int(max_len_val) if max_len_val else 0
                    
                    if current_len > max_len:
                        KSR.htable.sht_sets("redial", "KPI_MAX_LIST_SIZE", str(current_len))
                        KSR.info(f"KPI UPDATE: Novo maximo: {current_len}\n")

                    KSR.sl.send_reply(200, f"OK - Activated. List size: {current_len}")
                    return 1
                else:
                    KSR.sl.send_reply(400, "Bad Request - Empty List")
                    return 1

            elif body.startswith("DEACTIVATE"):
                caller = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
                old_list = KSR.htable.sht_get("redial", caller)
                
                if old_list and old_list != "":
                    KSR.htable.sht_sets("redial", caller, "")
                    
                    # KPI 2: Decrementar
                    active = KSR.htable.sht_get("redial", "KPI_CURRENT_ACTIVE")
                    if active and int(active) > 0:
                        new_active = int(active) - 1
                        KSR.htable.sht_sets("redial", "KPI_CURRENT_ACTIVE", str(new_active))
                        
                    KSR.sl.send_reply(200, "OK - Deactivated")
                else:
                    KSR.sl.send_reply(200, "OK - Was not active")
                return 1
            
            KSR.sl.send_reply(200, "OK")
            return 1

        # --- REGISTER ---
        if msg.Method == "REGISTER":
            aor = aor_Key()
            if deregister(aor):
                KSR.htable.sht_rm("redial", aor) 
                return 1 

            KSR.registrar.save("location", 0)
            if KSR.htable.sht_get("redial", aor) is None:
                KSR.htable.sht_sets("redial", aor, "") 
            return 1

        # --- INVITE ---
        if msg.Method == "INVITE":
            if KSR.registrar.lookup("location") == 1:
                KSR.tm.t_on_failure("ksr_failure_route_redial")
                
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
    # ROTA DE FALHA
    # ---------------------------------------------------------
    def ksr_failure_route_redial(self, msg):
        caller = str(KSR.pv.get("$avp(caller)"))
        status = str(KSR.pv.get("$rs"))
        
        KSR.info(f"!!! FALHA DETETADA !!! Status: {status} | Caller: {caller}\n")

        redial_list = KSR.htable.sht_get("redial", caller)
        
        if redial_list is None or redial_list == "":
            KSR.info(f"REDIAL: {caller} nao tem lista ativa.\n")
            return 1
            
        targets = redial_list.split()
        
        idx_val = KSR.pv.get("$avp(redial_idx)")
        if idx_val is not None:
            try:
                idx = int(idx_val)
            except:
                idx = 0
        else:
            idx = 0
        
        # Verifica fim da lista e limite maximo
        if idx < len(targets) and idx < MAX_REDIAL:
            next_user = targets[idx]
            next_uri = "sip:" + next_user + "@" + ACME_DOM
            
            KSR.info(f"REDIAL ACAO: Remarcando para {next_uri}\n")
            
            KSR.pv.sets("$ru", next_uri)
            KSR.pv.sets("$avp(redial_idx)", str(idx + 1))
            
            KSR.tm.t_on_failure("ksr_failure_route_redial")
            KSR.tm.t_relay()
            return 1
        else:
            KSR.info("REDIAL: Fim da lista ou limite atingido.\n")

        return 1