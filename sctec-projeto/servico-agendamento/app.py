import logging
import json
from datetime import datetime, timezone
# send_from_directory para servir o index.html
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import time 
import os
import requests # Para chamar o Coordenador

# --- 1. CONFIGURAÇÃO DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:servico-agendamento:%(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S', 
    handlers=[
        logging.FileHandler('app.log'), # Escreve em app.log
        logging.StreamHandler()      # Escreve no console
    ]
)
# Altera o formato de data do logger para UTC
logging.Formatter.converter = time.gmtime

# Logger customizado para auditoria
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO) 
audit_handler = logging.FileHandler('audit.log') # Arquivo separado 'audit.log'
audit_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.propagate = False # Evita que logs de auditoria apareçam no app.log

def log_audit(event_type, user_details, details, metadata=None):
    """
    Registra um evento de auditoria no formato JSON.
    """
    try:
        audit_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "level": "AUDIT",
            "event_type": event_type,
            "service": "servico-agendamento",
            "user": user_details,
            "details": details,
            "metadata": metadata or {}
        }
        audit_logger.info(json.dumps(audit_entry, ensure_ascii=False))
    except Exception as e:
        logging.error(f"Falha ao escrever log de auditoria: {e}")

# --- 2. CONFIGURAÇÃO DO FLASK E BANCO DE DADOS ---
app = Flask(__name__)
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    logging.error(f"Erro ao criar diretório 'instance': {e}")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- IMPORTANTE: ADAPTAR AQUI SE ESTIVER NA ETAPA 5 (DOCKER) ---
# Se estiver rodando sem Docker (Etapa 4), use 127.0.0.1
URL_COORDENADOR = "http://servico-coordenador:3000"
# Se estiver rodando COM Docker (Etapa 5), use o nome do serviço
# URL_COORDENADOR = "http://servico-coordenador:3000" 

# --- 3. MODELOS ---
class Cientista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    instituicao = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100)) 
    data_cadastro = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cientista_id = db.Column(db.Integer, db.ForeignKey('cientista.id'), nullable=False)
    horario_inicio_utc = db.Column(db.DateTime, nullable=False)
    horario_fim_utc = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='confirmado')
    objeto_observacao = db.Column(db.String(100))
    descricao = db.Column(db.String(200))
    data_criacao = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    cientista = db.relationship('Cientista', backref=db.backref('agendamentos', lazy=True))

# --- 4. ROTAS DA API ---

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/time', methods=['GET'])
def get_time():
    logging.info(f"Requisição recebida em GET /time do IP {request.remote_addr}")
    server_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return jsonify({
        "server_time_utc": server_time,
        "_links": {
            "self": {"href": "/time"},
            "agendamentos": {"href": "/agendamentos", "method": "GET"},
            "criar_agendamento": {"href": "/agendamentos", "method": "POST"}
        }
    })

@app.route('/agendamentos', methods=['GET'])
def get_agendamentos():
    logging.info("Requisição recebida para GET /agendamentos")
    agendamentos_db = Agendamento.query.filter_by(status='confirmado').all()
    agendamentos_json = []
    for ag in agendamentos_db:
        ag_data = {
            "id": ag.id,
            "cientista_id": ag.cientista_id,
            "horario_inicio_utc": ag.horario_inicio_utc.isoformat().replace('+00:00', 'Z'),
            "status": ag.status,
            "objeto_observacao": ag.objeto_observacao,
            "_links": {
                "self": {"href": f"/agendamentos/{ag.id}"},
                "cientista": {"href": f"/cientistas/{ag.cientista_id}"},
                "cancelar": {
                    "href": f"/agendamentos/{ag.id}/cancelar",
                    "method": "POST",
                    "description": "Cancelar este agendamento"
                }
            }
        }
        agendamentos_json.append(ag_data)
    return jsonify({"total": len(agendamentos_json), "agendamentos": agendamentos_json})

@app.route('/agendamentos/<int:id>/cancelar', methods=['POST'])
def cancelar_agendamento(id):
    logging.info(f"Requisição recebida para POST /agendamentos/{id}/cancelar")
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({"error": "Agendamento não encontrado"}), 404
    if agendamento.status != 'confirmado':
        return jsonify({"error": "Não é possível cancelar um agendamento que não está 'confirmado'"}), 400

    agendamento.status = 'cancelado'
    agendamento.data_atualizacao = datetime.now(timezone.utc)
    db.session.commit()
    
    try:
        cientista = agendamento.cientista
        user_details = {"cientista_id": cientista.id, "cientista_nome": cientista.nome, "cientista_email": cientista.email}
    except Exception:
        user_details = {"cientista_id": agendamento.cientista_id}

    log_audit(
        event_type="AGENDAMENTO_CANCELADO", user_details=user_details,
        details={
            "agendamento_id": agendamento.id,
            "horario_inicio_utc": agendamento.horario_inicio_utc.isoformat().replace('+00:00', 'Z'),
            "status_anterior": "confirmado", "status_novo": "cancelado"
        }
    )
    
    response_body = {
        "id": agendamento.id, "status": agendamento.status,
        "_links": {
            "self": {"href": f"/agendamentos/{agendamento.id}"},
            "cientista": {"href": f"/cientistas/{agendamento.cientista_id}"},
            "criar_novo": {"href": "/agendamentos", "method": "POST"}
        }
    }
    return jsonify(response_body), 200

@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    logging.info("Requisição recebida para POST /agendamentos")
    data = request.get_json()
    user_details = {"cientista_id": data.get('cientista_id')}
    
    try:
        cientista_id = data['cientista_id']
        horario_inicio_str = data['horario_inicio_utc'] 
        horario_fim_str = data['horario_fim_utc']
        horario_inicio_utc = datetime.fromisoformat(horario_inicio_str.replace('Z', '+00:00'))
        horario_fim_utc = datetime.fromisoformat(horario_fim_str.replace('Z', '+00:00'))
        
        cientista = db.session.get(Cientista, cientista_id)
        if not cientista:
            logging.warning(f"Cientista ID {cientista_id} não encontrado")
            return jsonify({"error": "Cientista não encontrado"}), 404
        
        user_details = {"cientista_id": cientista.id, "cientista_nome": cientista.nome, "cientista_email": cientista.email}
        
        resource_id = f"Hubble-Acad_{horario_inicio_str}"
        lock_adquirido = False
        
        try:
            logging.info(f"Tentando adquirir lock para o recurso {resource_id}")
            try:
                lock_response = requests.post(f"{URL_COORDENADOR}/lock", json={"resource_id": resource_id}, timeout=5)
            except requests.exceptions.ConnectionError:
                logging.error(f"Falha ao conectar no Serviço Coordenador em {URL_COORDENADOR}")
                return jsonify({"error": "Serviço de coordenação indisponível"}), 503

            if lock_response.status_code == 200:
                logging.info(f"Lock adquirido com sucesso para {resource_id}")
                lock_adquirido = True
                
                logging.info(f"Iniciando verificação de conflito no BD para {horario_inicio_utc}")
                conflito = Agendamento.query.filter(
                    (Agendamento.horario_inicio_utc < horario_fim_utc) &
                    (Agendamento.horario_fim_utc > horario_inicio_utc) &
                    (Agendamento.status == 'confirmado')
                ).first()

                if conflito:
                    logging.warning(f"Conflito detectado no BD: Agendamento {conflito.id}")
                    return jsonify({"error": "Horário não disponível"}), 409

                logging.info("Salvando novo agendamento no BD")
                novo_agendamento = Agendamento(
                    cientista_id=cientista_id, horario_inicio_utc=horario_inicio_utc, horario_fim_utc=horario_fim_utc,
                    objeto_observacao=data.get('objeto_observacao'), descricao=data.get('descricao'), status='confirmado'
                )
                db.session.add(novo_agendamento)
                db.session.commit() 

                log_audit(
                    event_type="AGENDAMENTO_CRIADO", user_details=user_details,
                    details={"agendamento_id": novo_agendamento.id, "horario_inicio_utc": horario_inicio_str, "horario_fim_utc": horario_fim_str, "status": novo_agendamento.status}
                )
                
                logging.info(f"Agendamento {novo_agendamento.id} criado com sucesso")

                response_body = {
                    "id": novo_agendamento.id, "cientista_id": novo_agendamento.cientista_id,
                    "horario_inicio_utc": novo_agendamento.horario_inicio_utc.isoformat().replace('+00:00', 'Z'),
                    "horario_fim_utc": novo_agendamento.horario_fim_utc.isoformat().replace('+00:00', 'Z'),
                    "status": novo_agendamento.status,
                    "_links": {
                        "self": {"href": f"/agendamentos/{novo_agendamento.id}"},
                        "cientista": {"href": f"/cientistas/{novo_agendamento.cientista_id}"},
                        "cancelar": {"href": f"/agendamentos/{novo_agendamento.id}/cancelar", "method": "POST"},
                    }
                }
                return jsonify(response_body), 201
            
            elif lock_response.status_code == 409:
                logging.warning(f"Falha ao adquirir lock para {resource_id}, recurso ocupado")
                log_audit(
                    event_type="AGENDAMENTO_TENTATIVA_FALHA", user_details=user_details,
                    details={"horario_inicio_utc": horario_inicio_str, "horario_fim_utc": horario_fim_str, "motivo_falha": "Recurso em uso - lock não adquirido"}
                )
                return jsonify({"error": "Recurso em uso"}), 409
            else:
                logging.error(f"Erro inesperado do Serviço Coordenador: {lock_response.status_code}")
                return jsonify({"error": "Erro interno no serviço de coordenação"}), 500
        finally:
            if lock_adquirido:
                logging.info(f"Liberando lock para o recurso {resource_id}")
                try:
                    requests.post(f"{URL_COORDENADOR}/unlock", json={"resource_id": resource_id}, timeout=2)
                except Exception as e:
                    logging.error(f"Falha CRÍTICA ao liberar o lock para {resource_id}: {e}")
                    
    except Exception as e:
        logging.error(f"Erro inesperado em POST /agendamentos: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

# --- 5. ROTA /setup (ATUALIZADA PARA 10 CIENTISTAS) ---
@app.route('/setup', methods=['POST'])
def setup_database():
    """
    Cria 10 cientistas de teste (Joao, Paulo, etc.) se eles não existirem.
    IDs serão 1, 2, 3...
    """
    
    # Lista de 10 nomes de cientistas
    NOMES_CIENTISTAS = [
        "Joao Silva", "Paulo Santos", "Ana Oliveira", "Beatriz Costa", "Carlos Pereira",
        "Daniela Ferreira", "Eduardo Almeida", "Fernanda Lima", "Gustavo Martins", "Helena Rocha"
    ]
    
    try:
        # Garante que as tabelas estão criadas
        db.create_all() 
        
        cientistas_criados = []
        for nome_completo in NOMES_CIENTISTAS:
            # Cria um email simples (ex: joao@email.com)
            email = f"{nome_completo.split(' ')[0].lower()}@email.com"
            
            # Verifica se o cientista já existe
            cientista = Cientista.query.filter_by(email=email).first()
            
            if not cientista:
                # Cria o novo cientista
                novo_cientista = Cientista(
                    nome=nome_completo,
                    email=email,
                    instituicao="Instituto de Teste",
                    pais="Brasil"
                )
                db.session.add(novo_cientista)
                cientistas_criados.append(nome_completo)
        
        # Salva todos os novos cientistas no banco
        if cientistas_criados:
            db.session.commit()
            logging.info(f"Setup: Criados {len(cientistas_criados)} novos cientistas.")
        
        # Mensagem de sucesso atualizada
        return jsonify({
            "message": f"Banco de dados inicializado. {len(cientistas_criados)} novos cientistas criados.",
            "cientistas_na_base": len(NOMES_CIENTISTAS)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Falha no setup: {e}")
        return jsonify({"error": f"Falha no setup: {e}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True, port=5000)