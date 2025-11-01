import requests
import threading
import time

# A URL do Serviço de Agendamento (Flask) [cite: 328]
URL_AGENDAMENTO = "http://127.0.0.1:5000/agendamentos"

# Número de requisições simultâneas [cite: 330]
NUMERO_DE_REQUISICOES = 10

# Os dados EXATOS que todas as requisições tentarão criar [cite: 332]
# Payload baseado no seu API.md e MODELOS.md
PAYLOAD_CONFLITANTE = {
  "cientista_id": 7, # ID que criamos na rota /setup
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "objeto_observacao": "NGC 1300 (Teste de Concorrência)",
  "descricao": "Teste de condição de corrida"
}

# Lista para armazenar os códigos de status
resultados = []

def fazer_requisicao_agendamento(thread_num):
    """
    Função que será executada por cada thread.
    Envia uma única requisição POST.
    """
    print(f"[Thread {thread_num}]: Iniciando requisição...")
    try:
        response = requests.post(URL_AGENDAMENTO, json=PAYLOAD_CONFLITANTE)
        
        print(f"[Thread {thread_num}]: Resposta recebida! "
              f"Status Code: {response.status_code}, "
              f"Body: {response.text[:100]}...") # [cite: 344-346]
        
        resultados.append(response.status_code)

    except requests.exceptions.ConnectionError as e:
        print(f"[Thread {thread_num}]: Erro de conexão. O servidor Flask está rodando? Erro: {e}")
        resultados.append(None)
    except Exception as e:
        print(f"[Thread {thread_num}]: Erro inesperado: {e}")
        resultados.append(None)

if __name__ == "__main__":
    print(f"Disparando {NUMERO_DE_REQUISICOES} requisições simultâneas para {URL_AGENDAMENTO}")
    print(f"Payload: {PAYLOAD_CONFLITANTE}\n")
    
    threads = []
    start_time = time.time()

    for i in range(NUMERO_DE_REQUISICOES):
        t = threading.Thread(target=fazer_requisicao_agendamento, args=(i+1,))
        threads.append(t)
        t.start() # [cite: 360]

    for t in threads:
        t.join() # [cite: 362]

    end_time = time.time()
    
    print("\n--- TESTE CONCLUÍDO ---")
    print(f"Tempo total: {end_time - start_time:.2f} segundos")
    
    # Contagem dos resultados
    sucessos = resultados.count(201)
    conflitos_bd = resultados.count(409)
    outros_erros = len(resultados) - sucessos - conflitos_bd
    
    print(f"Resultados (Status Code):")
    print(f"  201 Created: {sucessos}")
    print(f"  409 Conflict: {conflitos_bd}")
    print(f"  Outros Erros: {outros_erros}")
    
    print("\n--- VALIDAÇÃO (Etapa 2) ---")
    if sucessos > 1:
        print(f"FALHA COMPROVADA: {sucessos} agendamentos foram criados com sucesso para o mesmo horário.")
        print("Isto é uma condição de corrida!")
    elif sucessos == 1:
        print("SUCESSO (Inesperado para Etapa 2): Apenas 1 agendamento foi criado. Tente aumentar o número de requisições.")
    else:
        print("ERRO: Nenhum agendamento foi criado. Verifique o servidor.")