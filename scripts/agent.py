import grpc
import time
import subprocess
import re
from concurrent import futures
import gnmi_pb2
import gnmi_pb2_grpc

# Comando absoluto para evitar erros
KAMAILIO_CMD = ["/usr/sbin/kamcmd", "htable.dump", "stats"]

class gNMI_Server(gnmi_pb2_grpc.gNMIServicer):
    def Get(self, request, context):
        # Inicializa as variáveis a zero
        stats = {"total_activations": 0, "max_list_size": 0, "active_users": 0}
        
        try:
            # Executa o comando no Kamailio
            res = subprocess.run(KAMAILIO_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = res.stdout
            
            # Regex para apanhar os números da tabela 'stats'
            m1 = re.search(r'name:\s*total_activations.*?value:\s*(\d+)', output, re.DOTALL)
            if m1: stats["total_activations"] = int(m1.group(1))

            m2 = re.search(r'name:\s*max_list_size.*?value:\s*(\d+)', output, re.DOTALL)
            if m2: stats["max_list_size"] = int(m2.group(1))
            
            m3 = re.search(r'name:\s*active_users.*?value:\s*(\d+)', output, re.DOTALL)
            if m3: stats["active_users"] = int(m3.group(1))
            
            print(f"[DEBUG] Dados lidos: {stats}")

        except Exception as e:
            print(f"[ERRO] Falha ao ler dados: {e}")

        # Monta a resposta gNMI
        ts = int(time.time() * 1e9)
        notif = gnmi_pb2.Notification(timestamp=ts)
        notif.prefix.elem.add(name='kamailio')
        notif.prefix.elem.add(name='stats')
        
        up1 = notif.update.add()
        up1.path.elem.add(name='total_activations')
        up1.val.int_val = stats["total_activations"]
        
        up2 = notif.update.add()
        up2.path.elem.add(name='max_list_size')
        up2.val.int_val = stats["max_list_size"]
        
        up3 = notif.update.add()
        up3.path.elem.add(name='active_users')
        up3.val.int_val = stats["active_users"]

        return gnmi_pb2.GetResponse(notification=[notif])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gnmi_pb2_grpc.add_gNMIServicer_to_server(gNMI_Server(), server)
    server.add_insecure_port('[::]:50051')
    print("Agente gNMI pronto e a correr na porta 50051...")
    server.start()
    try:
        while True: time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()