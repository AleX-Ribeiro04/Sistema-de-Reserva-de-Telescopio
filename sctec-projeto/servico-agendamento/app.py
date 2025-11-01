import logging
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import time 
import os # <-- 1. ADICIONADO IMPORT

# --- 1. CONFIGURAÇÃO DE LOGGING (Exatamente do seu LOGGING.md) ---

# Configuração do logger de aplicação
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

# Logger customizado para auditoria
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO) 
audit_handler = logging.FileHandler('audit.log') 
audit_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.propagate = False 

def log_audit(event_type, user_details, details, metadata=None):
    """
    Registra um evento de auditoria no formato JSON.
    Baseado no seu LOGGING.md.
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

# --- 2.1. CORREÇÃO DO ERRO: Garantir que a pasta 'instance' exista ---
# app.instance_path é o caminho absoluto para a pasta /instance
try:
    os.makedirs(app.instance_path, exist_ok=True)
    logging.info(f"Diretório 'instance' verificado/criado em: {app.instance_path}")
except OSError as e:
    logging.error(f"Erro ao criar diretório 'instance': {e}")
# --- FIM DA CORREÇÃO ---

# Configuração do SQLite conforme PDF, agora usando o caminho absoluto
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 3. MODELOS (Baseado no seu MODELOS.md) ---

class Cientista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    instituicao = db.Column(db.String(100), nullable=False)
    # No seu MODELOS.md, 'pais' era obrigatório, mas não estava no seu API.md (POST /cientistas)
    # Adicionando 'pais' aqui para bater com o MODELOS.md
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

# --- 4. ROTAS DA API (Baseado no seu API.md) ---

@app.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    logging.info("Requisição recebida para POST /agendamentos")
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Payload JSON inválido"}), 400

    try:
        cientista_id = data['cientista_id']
        horario_inicio_utc = datetime.fromisoformat(data['horario_inicio_utc'].replace('Z', '+00:00'))
        horario_fim_utc = datetime.fromisoformat(data['horario_fim_utc'].replace('Z', '+00:00'))
        
        cientista = db.session.get(Cientista, cientista_id)
        if not cientista:
            logging.warning(f"Cientista ID {cientista_id} não encontrado")
            return jsonify({"error": "Cientista não encontrado"}), 404

        logging.info(f"Iniciando verificação de conflito no BD para {horario_inicio_utc}")
        
        conflito = Agendamento.query.filter(
            (Agendamento.horario_inicio_utc < horario_fim_utc) &
            (Agendamento.horario_fim_utc > horario_inicio_utc) &
            (Agendamento.status == 'confirmado')
        ).first()

        if conflito:
            logging.warning(f"Conflito detectado no BD: Agendamento {conflito.id} já existe para este horário")
            # Payload de erro conforme seu API.md
            response_conflito = {
                "error": "Horário não disponível",
                "details": "Já existe um agendamento para este horário",
                "agendamento_conflitante": {
                    "id": conflito.id,
                    "horario_inicio_utc": conflito.horario_inicio_utc.isoformat().replace('+00:00', 'Z'),
                    "horario_fim_utc": conflito.horario_fim_utc.isoformat().replace('+00:00', 'Z')
                },
                "_links": {
                    "self": {"href": "/agendamentos"},
                    "agendamento_conflitante": {"href": f"/agendamentos/{conflito.id}"}
                }
            }
            return jsonify(response_conflito), 409

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

        # Log de AUDITORIA (A Prova da Falha!)
        log_audit(
            event_type="AGENDAMENTO_CRIADO",
            user_details={
                "cientista_id": cientista.id,
                "cientista_nome": cientista.nome,
                "cientista_email": cientista.email
            },
            details={
                "agendamento_id": novo_agendamento.id,
                "horario_inicio_utc": novo_agendamento.horario_inicio_utc.isoformat().replace('+00:00', 'Z'),
                "horario_fim_utc": novo_agendamento.horario_fim_utc.isoformat().replace('+00:00', 'Z'),
                "objeto_observacao": novo_agendamento.objeto_observacao,
                "status": novo_agendamento.status
            }
        )
        
        logging.info(f"Agendamento {novo_agendamento.id} criado com sucesso")

        response_body = {
            "id": novo_agendamento.id,
            "cientista_id": novo_agendamento.cientista_id,
            "horario_inicio_utc": novo_agendamento.horario_inicio_utc.isoformat().replace('+00:00', 'Z'),
            "horario_fim_utc": novo_agendamento.horario_fim_utc.isoformat().replace('+00:00', 'Z'),
            "status": novo_agendamento.status,
            "objeto_observacao": novo_agendamento.objeto_observacao,
            "descricao": novo_agendamento.descricao,
            "data_criacao": novo_agendamento.data_criacao.isoformat().replace('+00:00', 'Z'),
            "data_atualizacao": novo_agendamento.data_atualizacao.isoformat().replace('+00:00', 'Z'),
            "_links": {
                "self": {"href": f"/agendamentos/{novo_agendamento.id}"},
                "cientista": {"href": f"/cientistas/{novo_agendamento.cientista_id}"},
                "cancelar": {"href": f"/agendamentos/{novo_agendamento.id}/cancelar", "method": "POST"},
                "todos_agendamentos": {"href": "/agendamentos", "method": "GET"}
            }
        }
        return jsonify(response_body), 201

    except Exception as e:
        logging.error(f"Erro inesperado em POST /agendamentos: {e}")
        db.session.rollback()
        return jsonify({"error": "Erro interno do servidor"}), 500

# --- 5. Rota de Setup (Para facilitar os testes) ---
@app.route('/setup', methods=['POST'])
def setup_database():
    try:
        # db.create_all() não é mais necessário aqui, 
        # pois é chamado no 'if __name__ == "__main__":'
        
        cientista_teste = Cientista.query.filter_by(email="marie.curie@sorbonne.fr").first()
        if not cientista_teste:
            cientista_teste = Cientista(
                id=7, 
                nome="Marie Curie",
                email="marie.curie@sorbonne.fr",
                instituicao="Université Paris Sciences et Lettres",
                pais="França" # Adicionado conforme MODELOS.md
            )
            db.session.add(cientista_teste)
            db.session.commit()
            
        return jsonify({
            "message": "Banco de dados inicializado com sucesso",
            "cientista_teste": {
                "id": cientista_teste.id,
                "nome": cientista_teste.nome
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Falha no setup: {e}")
        return jsonify({"error": f"Falha no setup: {e}"}), 500

if __name__ == '__main__':
    with app.app_context():
        # Cria as tabelas (e o arquivo .db) se não existirem
        db.create_all() 
    app.run(debug=True, port=5000)