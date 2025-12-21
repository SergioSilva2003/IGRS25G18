# IGRS25G18
# Repositório do Projeto de IGRS 2025-2026 realizado pelo grupo 18.

Elementos do grupo:

Marcos Figueiredo, 111159;

Sérgio Silva, 111052;

Tiago Inácio, 110890.

<ins>Os fluxogramas e os diagramas de sequência, bem como o product backlog estão também disponíveis na plataforma Trello.</ins>

## **Product backlog**:

-->Epic - Disponibilizar o REDIAL2.0:
```
Como: Operador

Quero: Disponibilizar o serviço REDIAL2.0

Para: Aumentar o número de chamadas com sucesso e enriquecer o portfólio para aumentar os lucros.
```
-->User Story - Controlar chamadas:
```
Como: Operador

Quero: Controlar chamadas com ajuda do protocolo SIP e das listas de remarcação.

Para: Disponibilizar o serviço
```
-->User Story - Disponibilização de funcionalidades de gestão:
```
Como: Operador

Quero: Disponibilizar funcionalidades de gestão com recurso a uma base de dados, nomeadamente para gerir a ativação/desativação do serviço.

Para: Disponibilizar o serviço
```
-->User Story - Gerir registos:
```
Como: Operador

Quero: Gerir registos (registo/deregisto dos clientes), com recurso a uma base de dados.

Para: Disponibilizar o serviço REDIAL2.0.
```
-->User Story - Garantir segurança do serviço (Operador):
```
Como: Operador

Quero: Validar acessos (através do domínio ou código PIN, este último com ajuda do protocolo SIP)

Para: Garantir que disponibilizo um serviço seguro.
```
-->User Story - Monitorizar desempenho:
```
Como: Operador

Quero: Monitorizar o desempenho através de KPI´s utilizando uma interface baseada no protocolo gNMI.

Para: Disponibilizar o serviço REDIAL2.0.
```
-->Epic - Utilizar o REDIAL2.0:
```
Como: Cliente Jovem/Idoso

Quero: Utilizar o REDIAL2.0 (ou seja fazer remarcações automáticas para destinos pertencentes à lista de remarcação).

Para: Aumentar a probabilidade de ser atendido (Jovem)/Garantir que sou atendido (Idoso).
```
-->User Story - Acesso a um terminal:
```
Como: Cliente

Quero: Ter acesso a um terminal com conexão e assinatura válida.

Para: Utilizar o REDIAL2.0
```
-->User Story - Gerir o serviço (Cliente):
```
Como: Cliente

Quero: Gerir o serviço

Para: Ter uma lista de destinos para os quais quero efetuar remarcações de chamadas e para ativar/desativar o serviço.
```
-->User Story - Utilizar um serviço seguro:
```
Como: Cliente

Quero: Ter uma assinatura válida

Para: Ter segurança na utilização do serviço
```
-->User story - Utilizar o serviço através de múltiplas plataformas:
```
Como: Cliente

Quero: Utilizar o serviço REDIAL2.0 através de múltiplas plataformas, utilizando os protocolos SIP e gNMI.

Para: Utilizar o serviço REDIAL2.0.
```
## **Fluxogramas**:

-->Registo/deregisto de utilizadores:

<img width="653" height="496" alt="image" src="https://github.com/user-attachments/assets/41ac70e4-d205-4806-86ac-d7e46b85edff" />

-->Realização de uma chamada:

<img width="432" height="733" alt="image" src="https://github.com/user-attachments/assets/ed4d48a6-10a3-4f23-9d0c-f7120ff6821e" />


## **Diagramas de sequência (simplificados)**:

-->Registo de utilizador do domínio acme.operador:

<img width="491" height="384" alt="image" src="https://github.com/user-attachments/assets/5b4e4869-30cb-402d-98ed-5d08ebd37748" />

-->Registo de utilizador (falhado) de um outro domínio:

<img width="518" height="394" alt="image" src="https://github.com/user-attachments/assets/3a038529-01ce-49d0-a59d-10a6114f3e5b" />

-->Deregisto de um utilizador:

<img width="468" height="388" alt="image" src="https://github.com/user-attachments/assets/4857a46f-33d3-43aa-9db6-615cdc1b87b0" />

-->Ativação do serviço por parte de um utilizador:

<img width="503" height="491" alt="image" src="https://github.com/user-attachments/assets/b8dc7e87-91bf-46e9-8281-3589726d595c" />

-->Desativação do serviço por parte de um utilizador:

<img width="398" height="378" alt="image" src="https://github.com/user-attachments/assets/4c42e5a0-20ec-4204-9e90-b00a14220d67" />

-->Comportamento de uma chamada básica, com **CVM**:

<img width="818" height="644" alt="image" src="https://github.com/user-attachments/assets/0071ddcf-c42a-4f23-a631-b814ba72b49b" />

-->Comportamento de remarcação automática quando o destino está ocupado:

<img width="725" height="490" alt="image" src="https://github.com/user-attachments/assets/d29f2ddf-e763-43c9-b183-b386389c7e6c" />

-->Comportamento de remarcação automática quando o destino não responde:

<img width="751" height="273" alt="image" src="https://github.com/user-attachments/assets/d06e86cf-1d16-46fd-9910-3f9c622b28cc" />














