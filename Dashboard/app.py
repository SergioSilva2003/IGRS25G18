import streamlit as st
import grpc
import gnmi_pb2
import gnmi_pb2_grpc
import time
import pandas as pd

st.set_page_config(page_title="Kamailio Dashboard", layout="wide")
st.title("📡 Monitorização Kamailio em Tempo Real")

# Espaço para as métricas
col1, col2, col3 = st.columns(3)
chart_spot = st.empty()

# Inicializar histórico
if "historico" not in st.session_state:
    st.session_state.historico = []

def get_data():
    try:
        # Tenta ligar ao localhost:50051 (onde o Docker expôs a porta)
        channel = grpc.insecure_channel('localhost:50051')
        stub = gnmi_pb2_grpc.gNMIStub(channel)
        
        path = gnmi_pb2.Path(elem=[gnmi_pb2.PathElem(name='kamailio'), gnmi_pb2.PathElem(name='stats')])
        response = stub.Get(gnmi_pb2.GetRequest(path=[path]))
        
        updates = response.notification[0].update
        dados = {}
        for up in updates:
            dados[up.path.elem[0].name] = up.val.int_val
        return dados
    except:
        return None

# Loop Infinito (Atualiza a cada 1 segundo)
while True:
    data = get_data()
    
    if data:
        # Métricas Grandes
        col1.metric("Ativações de Serviço", data.get('total_activations', 0))
        col2.metric("Utilizadores Ativos", data.get('active_users', 0))
        col3.metric("Tamanho da Lista", data.get('max_list_size', 0))

        # Atualizar Gráfico
        st.session_state.historico.append({
            "time": time.strftime("%H:%M:%S"),
            "Ativos": data.get('active_users', 0),
            "Lista": data.get('max_list_size', 0)
        })
        # Manter só os últimos 30 segundos
        if len(st.session_state.historico) > 30:
            st.session_state.historico.pop(0)
            
        df = pd.DataFrame(st.session_state.historico)
        if not df.empty:
            with chart_spot.container():
                st.line_chart(df.set_index("time"))
    else:
        st.warning("A tentar ligar ao Kamailio...")
    
    time.sleep(1)