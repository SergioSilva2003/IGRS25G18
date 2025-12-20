import sys
import KSR as KSR

ACME_DOM = "acme.operador"
MAX_REDIALS = 5

# Mandatory function - module initiation
def mod_init():
    KSR.info("===== from Python mod init\n")
    return kamailio()

# guarda o AOR no formato user@domain
def aor_Key():
    return KSR.pv.get("$tU") + "@" + KSR.pv.get("$td")

def deregister(aor):
    expire = KSR.hdr.get("Expires")
    if not expire:
        return False
    try:
        if int(expire.strip()) != 0:
            return False
    except:
        return False
   
    KSR.info("DE-REGISTER DETETADO (Expires: 0)\n")
    KSR.registrar.save("location", 0)
    return True

class kamailio:
    def __init__(self):
        KSR.info('===== kamailio.__init__\n')

    def child_init(self, rank):
        KSR.info('===== kamailio.child_init(%d)\n' % rank)
        return 0

    # ---------------------------------------------------------
    # 1. SERVIÇO: ACTIVATE (e verificação geral)
    # ---------------------------------------------------------
    def ksr_redial_service(self, msg):
        # 1. Se não for MESSAGE, ignora
        if msg.Method != "MESSAGE":
            return -1

        # 2. Se não for para o "redial", ignora (permite chat normal)
        if KSR.pv.get("$rU") != "redial" or KSR.pv.get("$rd") != ACME_DOM:
            return -1

        # --- A PARTIR DAQUI É O SERVIÇO REDIAL ---
        sender_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")

        # 3. Verificar se quem envia está registado
        valor_tabela = KSR.htable.sht_get("redial", sender_aor)

        KSR.info(f"Debug Redial: Valor na tabela para {sender_aor} é: '{valor_tabela}'\n")

        if valor_tabela is None:
            KSR.sl.send_reply(403, "Forbidden - You must REGISTER first")
            KSR.info(f"Redial: Tentativa de {sender_aor} rejeitada (Não registado)\n")
            return 1 # Parar script (já respondemos)

        # 4. Lógica do ACTIVATE
        body = KSR.pv.get("$rb")
        if body and body.startswith("ACTIVATE"):
            res = body.replace("ACTIVATE", "").strip()

            if len(res.split()) > 0:
                KSR.htable.sht_sets("redial", sender_aor, res)    
                KSR.sl.send_reply(200, "OK - Service Activated")
                KSR.info(f"Redial ATIVADO para {sender_aor}. Lista: {res}\n")
            else:
                KSR.sl.send_reply(400, "Bad Request - List is empty")

            return 1 # IMPORTANTE: Retorna 1 para parar o script

        return 1

    # ---------------------------------------------------------
    # 2. SERVIÇO: DEACTIVATE
    # ---------------------------------------------------------
    def ksr_redial_service_deactivate(self, msg):
        # 1. Verificações de segurança
        if msg.Method != "MESSAGE":
            return -1
        if KSR.pv.get("$rU") != "redial" or KSR.pv.get("$rd") != ACME_DOM:
            return -1

        sender_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
       
        # 2. DEBUG DO BODY
        body = KSR.pv.get("$rb")
        KSR.info(f"DEBUG BODY DEACTIVATE: Recebi exatamente: '{body}' de {sender_aor}\n")

        # 3. Limpar a tabela
        KSR.htable.sht_sets("redial", sender_aor, "")
       
        # 4. Ler de volta para confirmar (Debug)
        val_check = KSR.htable.sht_get("redial", sender_aor)

        # 5. ENVIAR A RESPOSTA
        KSR.sl.send_reply(200, "OK - Deactivated")
       
        KSR.info(f"Redial DESATIVADO para {sender_aor}. Tabela agora: '{val_check}'\n")
       
        return 1


    # ---------------------------------------------------------
    # ROTA PRINCIPAL (REQUEST ROUTE)
    # ---------------------------------------------------------
    def ksr_request_route(self, msg):
       
        # 1. Verificação de Domínio Global (Segurança)
        if KSR.pv.get("$td") != ACME_DOM:
            KSR.sl.send_reply(403, "Forbidden Domain")
            KSR.info("Domínio errado: " + KSR.pv.get("$td") + "\n")
            return 1

        # --- Lógica de MESSAGE ---
        if msg.Method == "MESSAGE":

            body = KSR.pv.get("$rb")

            # A. Lógica do DEACTIVATE
            # Verifica se existe body e se começa com DEACTIVATE
            if body and body.strip().startswith("DEACTIVATE"):
                if self.ksr_redial_service_deactivate(msg) == 1:
                    return 1

            # B. Se NÃO for Deactivate (é Activate ou erro), chama a função normal
            # Repara que este IF agora está fora do IF do Deactivate (Correção Importante)
            if self.ksr_redial_service(msg) == 1:
                return 1
           
            # C. Se nenhuma das funções acima "agarrou" a mensagem (retornaram -1),
            # então é chat normal.
            if KSR.registrar.lookup("location") == 1:
                KSR.tm.t_relay()
                return 1
           
            KSR.sl.send_reply(404, "Not Found")
            return 1

        # --- Lógica de REGISTER ---
        if msg.Method == "REGISTER":
            KSR.info("REGISTER R-URI: " + KSR.pv.get("$ru") + "\n")
           
            aor = aor_Key()
           
            if deregister(aor):
                KSR.htable.sht_rm("redial", aor)
                return 1

            KSR.registrar.save("location", 0)
           
            # Inicializar com string vazia
            KSR.htable.sht_sets("redial", aor, "")
            KSR.info("Registo e HTABLE atualizados para: " + aor + "\n")
            return 1

        # --- Lógica de INVITE ---
        if msg.Method == "INVITE":
            if KSR.registrar.lookup("location") == 1:
                KSR.rr.record_route()
                KSR.tm.t_relay()
                return 1
            else:
                KSR.sl.send_reply(404, "Not found")
                return 1

        # --- Lógica de ACK, BYE, CANCEL ---
        if msg.Method in ["ACK", "BYE", "CANCEL"]:
            KSR.rr.loose_route()
            KSR.tm.t_relay()
            return 1

        # Método não permitido
        KSR.sl.send_reply(405, "Method Not Allowed")
        return 1

    # Function called for REPLY messages received
    def ksr_reply_route(self, msg):
        KSR.info("===== reply_route - from kamailio python script: ")
        KSR.info("  Status is:"+ str(KSR.pv.get("$rs")) + "\n")
        return 1

    # Function called for messages sent/transit
    def ksr_onsend_route(self, msg):
        KSR.info("===== onsend route - from kamailio python script:")
        KSR.info("   %s\n" %(msg.Type))
        return 1