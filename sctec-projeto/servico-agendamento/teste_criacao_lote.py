import requests
import time
from datetime import datetime, timedelta, timezone

# --- IMPORTANTE ---
# Defina a URL base do seu servidor Flask
# Se estiver no Codespaces, use a URL da porta 5000
# Ex: "https://seu-workspace-url.app.github.dev"
BASE_URL = "http://127.0.0.1:5000"

URL_SETUP = f"{BASE_URL}/setup"
URL_AGENDAMENTO = f"{BASE_URL}/agendamentos"


# Lista dos 10 cientistas que o /setup deve criar
NOMES_CIENTISTAS = [
    "Joao Silva", "Paulo Santos", "Ana Oliveira", "Beatriz Costa", "Carlos Pereira",
    "Daniela Ferreira", "Eduardo Almeida", "Fernanda Lima", "Gustavo Martins", "Helena Rocha"
]
NUMERO_DE_AGENDAMENTOS = len(NOMES_CIENTISTAS)

def executar_teste_completo():
    """
    Executa o fluxo completo:
    1. Chama o /setup para criar os cientistas.
    2. Cria 10 agendamentos (1 por cientista).
    """
    
    # --- PASSO 1: CHAMAR O /SETUP ---
    print(f"--- PASSO 1: Garantindo que os {NUMERO_DE_AGENDAMENTOS} cientistas existem ---")
    print(f"Chamando {URL_SETUP}...")
    try:
        setup_response = requests.post(URL_SETUP)
        if setup_response.status_code == 200:
            print(f"SUCESSO (Setup): {setup_response.json().get('message')}")
        else:
            print(f"FALHA (Setup): {setup_response.status_code} - {setup_response.text}")
            print("O servidor Flask (app.py) está rodando com a rota /setup atualizada?")
            return # Para o script se o setup falhar
            
    except requests.exceptions.ConnectionError as e:
        print(f"ERRO DE CONEXÃO: Não foi possível conectar ao Flask em {BASE_URL}.")
        print("Verifique se o Terminal 1 (python app.py) está rodando.")
        return

    print("\n--- PASSO 2: Criando 10 agendamentos únicos ---")
    
    # Define um horário base para o primeiro agendamento
    base_time = datetime(2025, 12, 10, 10, 0, 0, tzinfo=timezone.utc)
    sucessos = 0
    
    for i in range(NUMERO_DE_AGENDAMENTOS):
        start_time = base_time + timedelta(hours=i)
        end_time = start_time + timedelta(minutes=30)

        nome_cientista = NOMES_CIENTISTAS[i]
        # Assume que o /setup criou os cientistas com IDs 1, 2, 3...
        cientista_id = i + 1 

        payload = {
          "cientista_id": cientista_id,
          "horario_inicio_utc": start_time.isoformat().replace('+00:00', 'Z'),
          "horario_fim_utc": end_time.isoformat().replace('+00:00', 'Z'),
          "objeto_observacao": f"Observação de {nome_cientista.split(' ')[0]}",
          "descricao": f"Agendamento do cientista ID {cientista_id} ({nome_cientista})"
        }

        print(f"\n[Request {i+1}]: {nome_cientista} (ID {cientista_id}) está criando o agendamento...")
        
        try:
            response = requests.post(URL_AGENDAMENTO, json=payload)
            
            if response.status_code == 201:
                print(f"  -> SUCESSO (201 Created): ID {response.json()['id']}")
                sucessos += 1
            else:
                # Se der 409 (Conflito de Horário), é porque o banco não estava limpo
                if response.status_code == 409:
                    print(f"  -> FALHA (409): {response.json().get('error')}. (Você limpou o database.db antes de rodar?)")
                else:
                    print(f"  -> FALHA ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"  -> ERRO Inesperado: {e}")
        
        time.sleep(0.1) # Pequena pausa

    print("\n--- CRIAÇÃO EM LOTE CONCLUÍDA ---")
    print(f"Total de agendamentos criados com sucesso: {sucessos}")

if __name__ == "__main__":
    # Garante que os servidores estão rodando e o banco limpo
    print("Iniciando teste...")
    print("Certifique-se de que os servidores Flask e Node estão rodando.")
    print("Para melhores resultados, delete o arquivo 'database.db' antes de começar.")
    input("Pressione Enter para começar o teste...")
    
    executar_teste_completo()