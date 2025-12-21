import sys
import KSR as KSR
import time

ACME_DOM = "acme.operador"
MAX_REDIALS = 5
REDIAL_DELAY = 2

def mod_init():
    KSR.info("===== from Python mod init\n")
    # Inicializa a zero
    KSR.htable.sht_sets("stats", "total_activations", "0")
    KSR.htable.sht_sets("stats", "active_users", "0")
    KSR.htable.sht_sets("stats", "max_list_size", "0")
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
        KSR.info('===== kamailio.__init__\n')

    def child_init(self, rank):
        KSR.info('===== kamailio.child_init(%d)\n' % rank)
        return 0

   
    # FUNÇÕES DE ESTATÍSTICA (KPIs) 
    def log_current_stats(self, context):
        total = KSR.htable.sht_get("stats", "total_activations")
        active = KSR.htable.sht_get("stats", "active_users")
        max_s = KSR.htable.sht_get("stats", "max_list_size")
        
        p_total = total if total else "0"
        p_active = active if active else "0"
        p_max = max_s if max_s else "0"

        KSR.info(f"STATS FINAL [{context}]: Total={p_total}, Ativos={p_active}, MaxLista={p_max}\n")

    def update_kpis_activate(self, sender_aor, list_content):
        # Total Activations
        val_total = KSR.htable.sht_get("stats", "total_activations")
        if val_total is None: 
            new_total = 1
        else: 
            new_total = int(val_total) + 1    
        KSR.htable.sht_sets("stats", "total_activations", str(new_total))

        # Max List Size
        current_size = len(list_content.split())
        max_size_str = KSR.htable.sht_get("stats", "max_list_size")
        max_size = int(max_size_str) if max_size_str else 0

        if current_size > max_size:
            KSR.htable.sht_sets("stats", "max_list_size", str(current_size))
            KSR.info(f"STATS: Novo recorde de lista! Tamanho: {current_size}\n")

        # Active Users (check if was already active)
        old_val = KSR.htable.sht_get("redial", sender_aor)
        
        if old_val is None or old_val == "":
            val_active = KSR.htable.sht_get("stats", "active_users")
            current_active = int(val_active) if val_active else 0
            KSR.htable.sht_sets("stats", "active_users", str(current_active + 1))
        
        self.log_current_stats("After ACTIVATE")

    def update_kpis_deactivate(self, sender_aor):
        old_val = KSR.htable.sht_get("redial", sender_aor)
        
        if old_val and old_val != "":
            val_active = KSR.htable.sht_get("stats", "active_users")
            if val_active:
                current_active = int(val_active)
                new_active = current_active - 1
                if new_active < 0: new_active = 0 
                KSR.htable.sht_sets("stats", "active_users", str(new_active))
            else:
                KSR.htable.sht_sets("stats", "active_users", "0")
            
        self.log_current_stats("After DEACTIVATE")

    
    #ACTIVATE/DEACTIVATE
    def ksr_redial_service(self, msg):
        if msg.Method != "MESSAGE": return -1
        if KSR.pv.get("$rU") != "redial" or KSR.pv.get("$rd") != ACME_DOM: return -1

        sender_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
        
       
        # Verifica se o utilizador já validou o PIN antes de deixar ativar
        is_auth = KSR.htable.sht_get("redial", sender_aor + "::auth")
        if is_auth is None:
            KSR.sl.send_reply(403, "Forbidden - Please send PIN first to 'validar'")
            KSR.info(f"SECURITY: {sender_aor} tentou ativar sem PIN.\n")
            return 1

        valor_tabela = KSR.htable.sht_get("redial", sender_aor)
        KSR.info(f"Debug Redial: Valor na tabela para {sender_aor} é: '{valor_tabela}'\n")

        body = KSR.pv.get("$rb")
        if body and body.startswith("ACTIVATE"):
            res = body.replace("ACTIVATE", "").strip()
            if len(res.split()) > 0:
                self.update_kpis_activate(sender_aor, res) # KPI UPDATE
                KSR.htable.sht_sets("redial", sender_aor, res)    
                KSR.sl.send_reply(200, "OK - Service Activated")
                KSR.info(f"Redial ATIVADO para {sender_aor}. Lista: {res}\n")
            else:
                KSR.sl.send_reply(400, "Bad Request - List is empty")
            return 1 
        return 1

    def ksr_redial_service_deactivate(self, msg):
        if msg.Method != "MESSAGE": return -1
        if KSR.pv.get("$rU") != "redial" or KSR.pv.get("$rd") != ACME_DOM: return -1

        sender_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
        
        self.update_kpis_deactivate(sender_aor) # KPI UPDATE

        KSR.htable.sht_sets("redial", sender_aor, "")
        
        val_check = KSR.htable.sht_get("redial", sender_aor)
        KSR.sl.send_reply(200, "OK - Service Deactivated")
        KSR.info(f"Redial DESATIVADO para {sender_aor}. Valor na tabela agora: '{val_check}'\n")
        return 1 

   
    # LÓGICA DO SERVIÇO (REDIAL 2.0)
    
    def ksr_redial_logic(self, msg):
        status = KSR.pv.get("$T_reply_code")
        if status: status = int(status)
        else: return 1

        KSR.info(f"REDIAL LOGIC: Falha detetada (Code {status}) para {KSR.pv.get('$ru')}\n")

        if status in [486, 408, 480]:
            count = KSR.pv.get("$avp(redial_count)")
            if count is None: count = 0
            else: count = int(count)

            if count < MAX_REDIALS:
                count += 1
                KSR.pv.sets("$avp(redial_count)", str(count))
                KSR.info(f"REDIAL LOGIC: Tentativa {count} de {MAX_REDIALS}...\n")
                time.sleep(REDIAL_DELAY)
                KSR.tm.t_on_failure("ksr_redial_logic")
                if KSR.registrar.lookup("location") == 1:
                    KSR.tm.t_relay()
                    return 1
                else:
                    KSR.info("REDIAL ERROR: Utilizador desapareceu do registo.\n")
                    return 1
            else:
                KSR.info("REDIAL LOGIC: Limite atingido.\n")
        return 1

    
    # ROTA PRINCIPAL (REQUEST ROUTE)
    def ksr_request_route(self, msg):
        if KSR.pv.get("$td") != ACME_DOM:
            KSR.sl.send_reply(403, "Forbidden Domain")
            return 1

        if msg.Method == "MESSAGE":
            
           
            
            if KSR.pv.get("$rU") == "validar":
                body = KSR.pv.get("$rb")
                
                if body and body.strip() == "0000":
                    sender = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
                    
                    # Guarda na tabela 'redial' com sufixo especial
                    KSR.htable.sht_sets("redial", sender + "::auth", "1")
                    
                    KSR.sl.send_reply(200, "PIN Aceite - Autenticado")
                    KSR.info(f"PIN VALIDATION: Sucesso para {sender}\n")
                    return 1
                else:
                    KSR.sl.send_reply(403, "Forbidden - PIN Incorreto")
                    KSR.info(f"PIN VALIDATION: Falha (PIN errado)\n")
                    return 1
            

            body = KSR.pv.get("$rb")
            if body and body.strip().startswith("DEACTIVATE"):
                if self.ksr_redial_service_deactivate(msg) == 1: return 1
            if self.ksr_redial_service(msg) == 1: return 1
            if KSR.registrar.lookup("location") == 1:
                KSR.tm.t_relay()
                return 1
            KSR.sl.send_reply(404, "Not Found")
            return 1

        if msg.Method == "REGISTER":
            aor = aor_Key()
            if deregister(aor):
                KSR.htable.sht_rm("redial", aor) 
                KSR.htable.sht_rm("redial", aor + "::auth")
                return 1 
            
            KSR.registrar.save("location", 0)
            
            # Inicializa tabela vazia
            KSR.htable.sht_sets("redial", aor, "") 
            KSR.info("Registo e HTABLE atualizados para: " + aor + "\n")
            return 1

        if msg.Method == "INVITE":
            sender_aor = KSR.pv.get("$fU") + "@" + KSR.pv.get("$fd")
            target_user = KSR.pv.get("$tU")
            lista_redial = KSR.htable.sht_get("redial", sender_aor)
            
            if lista_redial and target_user in lista_redial.split():
                KSR.info(f"REDIAL: Monitorizando chamada de {sender_aor} para {target_user}\n")
                KSR.pv.sets("$avp(redial_count)", "0")
                KSR.tm.t_on_failure("ksr_redial_logic")
            
            if KSR.registrar.lookup("location") == 1:
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

    def ksr_reply_route(self, msg):
        KSR.info("===== reply_route - from kamailio python script: ")
        KSR.info("  Status is:"+ str(KSR.pv.get("$rs")) + "\n")
        return 1

    def ksr_onsend_route(self, msg):
        KSR.info("===== onsend route - from kamailio python script:")
        KSR.info("   %s\n" %(msg.Type))
        return 1