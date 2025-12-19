import sys
import KSR as KSR

ACME_DOM = "acme.operador"

# Mandatory function - module initiation
def mod_init():
    KSR.info("===== from Python mod init\n")
    return kamailio()

# guarda o AOR no formato user@domain para depois se associar uma lista vazia
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

    # é deregister
    KSR.info("DE-REGISTER DETETADO (Expires: 0)\n")
    KSR.registrar.save("location", 0)
    return True



class kamailio:
    # Mandatory function - Kamailio class initiation
    def __init__(self):
        KSR.info('===== kamailio.__init__\n')

    # Mandatory function - Kamailio subprocesses
    def child_init(self, rank):
        KSR.info('===== kamailio.child_init(%d)\n' % rank)
        return 0

    def ksr_request_route(self, msg):
        
        # 1. Verificação de Domínio Global (Segurança)
        if KSR.pv.get("$td") != ACME_DOM:
            KSR.sl.send_reply(403, "Forbidden Domain")
            KSR.info("Domínio errado: " + KSR.pv.get("$td") + "\n")
            return 1

       # --- Lógica de REGISTER ---
        if msg.Method == "REGISTER":
            KSR.info("REGISTER R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.info("To: " + KSR.pv.get("$tu") + " Contact: " + KSR.hdr.get("Contact") + "\n")
            
            aor = aor_Key()
            
            # Verificar desregisto
            if deregister(aor):
                # CORREÇÃO: Usar sht_rm (verifica se esta função existe na tua versão, geralmente é sht_rm ou sht_rm_name_key)
                KSR.htable.sht_rm("redial", aor) 
                return 1 

            # Registo normal
            KSR.registrar.save("location", 0)
            
            # Inicializar lista redial
            # CORREÇÃO: Mudar de 'sht_set' para 'sht_sets' (String)
            KSR.htable.sht_sets("redial", aor, "") 
            
            KSR.info("Registo e HTABLE atualizados para: " + aor + "\n")
            return 1

        # --- Lógica de INVITE ---
        if msg.Method == "INVITE":
            KSR.info("INVITE R-URI: " + KSR.pv.get("$ru") + "\n")
            KSR.info("From: " + KSR.pv.get("$fu") + " To: " + KSR.pv.get("$tu") +"\n")

            
            if KSR.registrar.lookup("location") == 1:
                # Utilizador encontrado e R-URI atualizado para o IP do cliente
                KSR.rr.record_route()
                KSR.tm.t_relay()
                return 1
            else:
                # Utilizador não encontrado
                KSR.sl.send_reply(404, "Not found")
                return 1

        # --- Lógica de ACK, BYE, CANCEL ---
        if msg.Method == "ACK":
            KSR.rr.loose_route()
            KSR.tm.t_relay()
            return 1

        if msg.Method == "BYE":
            KSR.rr.loose_route()
            KSR.tm.t_relay()
            return 1

        if msg.Method == "CANCEL":
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