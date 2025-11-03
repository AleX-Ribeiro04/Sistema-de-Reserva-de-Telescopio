import logging
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import time 
import os
import requests # <-- 1. IMPORTAR REQUESTS

# --- 1. CONFIGURAÇÃO DE LOGGING (Sem mudanças) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(asctime)s:servico-agendamento:%(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S', 
    handlers=[
        logging.FileHandler('app.log'), 
        logging.StreamHandler()      
    ]
)
logging.Formatter.converter = time.gmtime
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO) 
audit_handler = logging.FileHandler('audit.log') 
audit_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.propagate = False 

def log_audit(event_type, user_details, details, metadata=None):
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

# --- 2. CONFIGURAÇÃO DO FLASK E BANCO DE DADOS (Sem mudanças) ---

app = Flask(__name__)
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    logging.error(f"Erro ao criar diretório 'instance': {e}")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2.1. URL DO COORDENADOR ---
URL_COORDENADOR = "http://127.0.0.1:3000" # Porta 3000, conforme API.md

# --- 3. MODELOS (Sem mudanças) ---

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

# --- 4. ROTAS DA API (MODIFICADA) ---

@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    logging.info("Requisição recebida para POST /agendamentos")
    data = request.get_json()
    if not data:
        return jsonify({"error": "Payload JSON inválido"}), 400

    # Detalhes do usuário para auditoria (coletados cedo)
    user_details = {"cientista_id": data.get('cientista_id')}
    
    try:
        cientista_id = data['cientista_id']
        horario_inicio_str = data['horario_inicio_utc'] # '2025-12-01T03:00:00Z'
        horario_fim_str = data['horario_fim_utc']
        
        horario_inicio_utc = datetime.fromisoformat(horario_inicio_str.replace('Z', '+00:00'))
        horario_fim_utc = datetime.fromisoformat(horario_fim_str.replace('Z', '+00:00'))
        
        cientista = db.session.get(Cientista, cientista_id)
        if not cientista:
            logging.warning(f"Cientista ID {cientista_id} não encontrado")
            return jsonify({"error": "Cientista não encontrado"}), 404
        
        # Atualiza detalhes do usuário para auditoria
        user_details = {
            "cientista_id": cientista.id,
            "cientista_nome": cientista.nome,
            "cientista_email": cientista.email
        }
        
        # --- 4.1. LÓGICA DE LOCK (Etapa 3) ---
        
        # Formato do resource_id (conforme MODELOS.md)
        resource_id = f"Hubble-Acad_{horario_inicio_str}"
        lock_adquirido = False
        
        try:
            # 1. Tentar adquirir o lock 
            logging.info(f"Tentando adquirir lock para o recurso {resource_id}") # 
            
            try:
                lock_response = requests.post(
                    f"{URL_COORDENADOR}/lock", 
                    json={"resource_id": resource_id},
                    timeout=5 # Timeout de 5 segundos
                )
            except requests.exceptions.ConnectionError:
                logging.error(f"Falha ao conectar no Serviço Coordenador em {URL_COORDENADOR}")
                return jsonify({"error": "Serviço de coordenação indisponível"}), 503

            if lock_response.status_code == 200:
                logging.info(f"Lock adquirido com sucesso para {resource_id}") # 
                lock_adquirido = True
                
                # --- 4.2. SEÇÃO CRÍTICA (Se o lock foi adquirido) ---
                
                # 2. Verificar o banco de dados (agora dentro da seção crítica)
                logging.info(f"Iniciando verificação de conflito no BD para {horario_inicio_utc}")
                conflito = Agendamento.query.filter(
                    (Agendamento.horario_inicio_utc < horario_fim_utc) &
                    (Agendamento.horario_fim_utc > horario_inicio_utc) &
                    (Agendamento.status == 'confirmado')
                ).first()

                if conflito:
                    logging.warning(f"Conflito detectado no BD: Agendamento {conflito.id} já existe para este horário")
                    response_conflito = {
                        "error": "Horário não disponível", 
                        "details": "Já existe um agendamento para este horário",
                        # ... (Restante da resposta 409 do API.md)
                    }
                    return jsonify(response_conflito), 409

                # 3. Salvar no banco
                logging.info("Salvando novo agendamento no BD")
                novo_agendamento = Agendamento(
                    cientista_id=cientista_id,
                    horario_inicio_utc=horario_inicio_utc,
                    horario_fim_utc=horario_fim_utc,
                    objeto_observacao=data.get('objeto_observacao'),
                    descricao=data.get('descricao'),
                    status='confirmado'
                )
                db.session.add(novo_agendamento)
                db.session.commit() 

                # 4. Log de Auditoria (SUCESSO)
                log_audit(
                    event_type="AGENDAMENTO_CRIADO",
                    user_details=user_details,
                    details={
                        "agendamento_id": novo_agendamento.id,
                        "horario_inicio_utc": horario_inicio_str,
                        "horario_fim_utc": horario_fim_str,
                        "status": novo_agendamento.status
                    }
                )
                
                logging.info(f"Agendamento {novo_agendamento.id} criado com sucesso")

                # 5. Preparar resposta de sucesso 201
                response_body = {
                    "id": novo_agendamento.id,
                    "cientista_id": novo_agendamento.cientista_id,
                    # ... (Restante da resposta 201 do API.md)
                    "_links": {
                        "self": {"href": f"/agendamentos/{novo_agendamento.id}"},
                        "cientista": {"href": f"/cientistas/{novo_agendamento.cientista_id}"},
                        "cancelar": {"href": f"/agendamentos/{novo_agendamento.id}/cancelar", "method": "POST"},
                    }
                }
                return jsonify(response_body), 201
            
            elif lock_response.status_code == 409:
                # O lock NÃO foi adquirido
                logging.warning(f"Falha ao adquirir lock para {resource_id}, recurso ocupado") # 
                
                # Log de Auditoria (FALHA) - Conforme LOGGING.md
                log_audit(
                    event_type="AGENDAMENTO_TENTATIVA_FALHA",
                    user_details=user_details,
                    details={
                        "horario_inicio_utc": horario_inicio_str,
                        "horario_fim_utc": horario_fim_str,
                        "motivo_falha": "Recurso em uso - lock não adquirido"
                    }
                )
                
                # Resposta 409 (conforme API.md)
                return jsonify({
                    "error": "Recurso em uso",
                    "details": "Outro usuário está tentando agendar este horário simultaneamente. Tente novamente.",
                    "_links": {"self": {"href": "/agendamentos"}}
                }), 409
            else:
                # Outro erro do coordenador
                logging.error(f"Erro inesperado do Serviço Coordenador: {lock_response.status_code}")
                return jsonify({"error": "Erro interno no serviço de coordenação"}), 500

        finally:
            # 6. Liberar o lock (SEMPRE, se foi adquirido)
            if lock_adquirido:
                logging.info(f"Liberando lock para o recurso {resource_id}")
                try:
                    requests.post(
                        f"{URL_COORDENADOR}/unlock", 
                        json={"resource_id": resource_id},
                        timeout=2
                    )
                except Exception as e:
                    # Se o unlock falhar, apenas logamos. A operação principal já foi feita.
                    logging.error(f"Falha CRÍTICA ao liberar o lock para {resource_id}: {e}")
                    
    except Exception as e:
        logging.error(f"Erro inesperado em POST /agendamentos: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

# --- 5. Rota de Setup (Sem mudanças) ---
@app.route('/setup', methods=['POST'])
def setup_database():
    try:
        cientista_teste = Cientista.query.filter_by(email="marie.curie@sorbonne.fr").first()
        if not cientista_teste:
            cientista_teste = Cientista(
                id=7, 
                nome="Marie Curie",
                email="marie.curie@sorbonne.fr",
                instituicao="Université Paris Sciences et Lettres",
                pais="França"
            )
            db.session.add(cientista_teste)
            db.session.commit()
            
        return jsonify({
            "message": "Banco de dados inicializado com sucesso",
            "cientista_teste": { "id": cientista_teste.id, "nome": cientista_teste.nome }
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Falha no setup: {e}")
        return jsonify({"error": f"Falha no setup: {e}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True, port=5000)