# Especificação de Logging - SCTEC

## Visão Geral

O sistema SCTEC implementa dois tipos distintos de logging:

1. **Logs de Aplicação**: Para depuração e rastreamento do fluxo de execução
2. **Logs de Auditoria**: Para registro imutável de eventos de negócio críticos

---

## 1. Logs de Aplicação

### Propósito
Auxiliar desenvolvedores e operadores a entender o fluxo de execução, diagnosticar problemas e monitorar o comportamento do sistema.

### Características
- **Formato**: Texto estruturado
- **Destino**: Console e arquivo `app.log`
- **Níveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Público-alvo**: Desenvolvedores e equipe de operações

### Formato Padrão
```
NIVEL:TIMESTAMP:SERVICO:MENSAGEM
```

### Estrutura dos Campos
- **NIVEL**: Severidade do log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **TIMESTAMP**: Data e hora em UTC no formato ISO 8601 com milissegundos
- **SERVICO**: Identificador do serviço (servico-agendamento, servico-coordenador)
- **MENSAGEM**: Descrição detalhada do evento

### Exemplos de Logs de Aplicação

#### Serviço de Agendamento (Flask)

**Requisições HTTP:**
```
INFO:2025-10-26T18:00:04.500Z:servico-agendamento:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.502Z:servico-agendamento:Requisição recebida para GET /time do IP 192.168.1.10
INFO:2025-10-26T18:00:06.100Z:servico-agendamento:Requisição recebida para POST /agendamentos/123/cancelar
```

**Operações de Lock:**
```
INFO:2025-10-26T18:00:04.505Z:servico-agendamento:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:05.120Z:servico-agendamento:Lock adquirido com sucesso para o recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:04.805Z:servico-agendamento:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
WARNING:2025-10-26T18:00:05.121Z:servico-agendamento:Falha ao adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z, recurso ocupado
INFO:2025-10-26T18:00:05.125Z:servico-agendamento:Liberando lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
```

**Operações de Banco de Dados:**
```
INFO:2025-10-26T18:00:05.122Z:servico-agendamento:Iniciando verificação de conflito no BD
INFO:2025-10-26T18:00:05.123Z:servico-agendamento:Salvando novo agendamento no BD
INFO:2025-10-26T18:00:05.124Z:servico-agendamento:Agendamento 123 salvo com sucesso
DEBUG:2025-10-26T18:00:05.110Z:servico-agendamento:Conexão com o banco de dados estabelecida
DEBUG:2025-10-26T18:00:05.115Z:servico-agendamento:Query executada: SELECT * FROM agendamentos WHERE horario_inicio_utc = '2025-12-01T03:00:00Z'
```

**Validações e Erros:**
```
WARNING:2025-10-26T18:00:04.600Z:servico-agendamento:Validação falhou: duração mínima não atendida
ERROR:2025-10-26T18:00:04.700Z:servico-agendamento:Cientista ID 99 não encontrado no banco de dados
ERROR:2025-10-26T18:00:04.800Z:servico-agendamento:Conflito detectado: horário já reservado pelo agendamento 122
```

#### Serviço Coordenador (Node.js)

```
INFO:2025-10-26T18:00:04.506Z:servico-coordenador:Recebido pedido de lock para recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:04.507Z:servico-coordenador:Lock concedido para recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:04.806Z:servico-coordenador:Recebido pedido de lock para recurso Hubble-Acad_2025-12-01T03:00:00Z
WARNING:2025-10-26T18:00:04.807Z:servico-coordenador:Recurso Hubble-Acad_2025-12-01T03:00:00Z já em uso, negando lock
INFO:2025-10-26T18:00:05.126Z:servico-coordenador:Recebido pedido de unlock para recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:05.127Z:servico-coordenador:Lock liberado para recurso Hubble-Acad_2025-12-01T03:00:00Z
```

### Níveis de Log - Quando Usar

| Nível | Quando Usar | Exemplo |
|-------|-------------|---------|
| DEBUG | Informações detalhadas para diagnóstico | Conexões BD, queries SQL, variáveis internas |
| INFO | Eventos normais do fluxo da aplicação | Requisições recebidas, operações iniciadas/concluídas |
| WARNING | Situações anormais mas recuperáveis | Lock negado, validação falhou |
| ERROR | Erros que impedem uma operação específica | Recurso não encontrado, falha de comunicação |
| CRITICAL | Falhas graves que afetam todo o sistema | Banco de dados inacessível, serviço coordenador offline |

---

## 2. Logs de Auditoria

### Propósito
Criar uma trilha imutável e juridicamente válida de todas as ações críticas de negócio. Esses logs são fundamentais para:
- Resolver disputas entre cientistas
- Investigar incidentes
- Cumprir requisitos regulatórios
- Provar quem fez o quê e quando

### Características
- **Formato**: JSON estruturado
- **Destino**: Arquivo `audit.log` (separado do app.log)
- **Nível**: AUDIT (customizado)
- **Imutabilidade**: Logs nunca devem ser modificados ou deletados
- **Público-alvo**: Auditores, gestores, equipe jurídica

### Formato Padrão JSON

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.123Z",
  "level": "AUDIT",
  "event_type": "TIPO_DO_EVENTO",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 7,
    "cientista_nome": "Marie Curie",
    "cientista_email": "marie.curie@sorbonne.fr"
  },
  "details": {
    // Campos específicos do evento
  },
  "metadata": {
    "ip_address": "192.168.1.10",
    "user_agent": "Mozilla/5.0...",
    "request_id": "req-abc123"
  }
}
```

### Estrutura dos Campos

#### Campos Obrigatórios
- **timestamp_utc**: Timestamp exato do evento em UTC (ISO 8601 com milissegundos)
- **level**: Sempre "AUDIT"
- **event_type**: Tipo de evento de negócio (ver lista abaixo)
- **service**: Nome do serviço que gerou o log

#### Campos Contextuais
- **user**: Informações do cientista que executou a ação
  - `cientista_id`: ID do cientista
  - `cientista_nome`: Nome completo
  - `cientista_email`: Email
- **details**: Dados específicos do evento (varia por tipo)
- **metadata**: Informações técnicas adicionais
  - `ip_address`: IP de origem da requisição
  - `user_agent`: Navegador/cliente usado
  - `request_id`: ID único da requisição (para correlação)

---

## 3. Tipos de Eventos de Auditoria

### CIENTISTA_CRIADO

Registrado quando um novo cientista é cadastrado no sistema.

```json
{
  "timestamp_utc": "2025-10-26T18:00:00.123Z",
  "level": "AUDIT",
  "event_type": "CIENTISTA_CRIADO",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 7,
    "cientista_nome": "Marie Curie",
    "cientista_email": "marie.curie@sorbonne.fr"
  },
  "details": {
    "instituicao": "Université Paris Sciences et Lettres",
    "pais": "França"
  },
  "metadata": {
    "ip_address": "192.168.1.10",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "request_id": "req-abc123"
  }
}
```

---

### AGENDAMENTO_CRIADO

Registrado quando um novo agendamento é criado com sucesso.

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.123Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CRIADO",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 7,
    "cientista_nome": "Marie Curie",
    "cientista_email": "marie.curie@sorbonne.fr"
  },
  "details": {
    "agendamento_id": 123,
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:30:00Z",
    "duracao_minutos": 30,
    "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
    "descricao": "Observação da estrutura de braços espirais",
    "status": "confirmado"
  },
  "metadata": {
    "ip_address": "192.168.1.10",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "request_id": "req-def456",
    "lock_acquired_at": "2025-10-26T18:00:05.120Z",
    "lock_duration_ms": 3
  }
}
```

---

### AGENDAMENTO_CANCELADO

Registrado quando um agendamento é cancelado.

```json
{
  "timestamp_utc": "2025-10-26T18:10:30.456Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CANCELADO",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 7,
    "cientista_nome": "Marie Curie",
    "cientista_email": "marie.curie@sorbonne.fr"
  },
  "details": {
    "agendamento_id": 123,
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:30:00Z",
    "status_anterior": "confirmado",
    "status_novo": "cancelado",
    "motivo": "Cancelamento solicitado pelo cientista"
  },
  "metadata": {
    "ip_address": "192.168.1.10",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "request_id": "req-ghi789"
  }
}
```

---

### AGENDAMENTO_TENTATIVA_FALHA

Registrado quando há tentativa de criar um agendamento mas ocorre conflito ou outro erro de negócio.

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.121Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_TENTATIVA_FALHA",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 8,
    "cientista_nome": "Albert Einstein",
    "cientista_email": "einstein@princeton.edu"
  },
  "details": {
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:30:00Z",
    "motivo_falha": "Recurso em uso - lock não adquirido",
    "agendamento_conflitante_id": 123
  },
  "metadata": {
    "ip_address": "192.168.1.20",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "request_id": "req-jkl012",
    "lock_attempt_at": "2025-10-26T18:00:04.805Z",
    "lock_denied_at": "2025-10-26T18:00:05.121Z"
  }
}
```

---

### CIENTISTA_ATUALIZADO

Registrado quando dados de um cientista são atualizados.

```json
{
  "timestamp_utc": "2025-10-26T19:00:00.789Z",
  "level": "AUDIT",
  "event_type": "CIENTISTA_ATUALIZADO",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 7,
    "cientista_nome": "Marie Curie",
    "cientista_email": "marie.curie@sorbonne.fr"
  },
  "details": {
    "campos_atualizados": ["instituicao"],
    "valores_anteriores": {
      "instituicao": "Université Paris Sciences et Lettres"
    },
    "valores_novos": {
      "instituicao": "Sorbonne Université"
    }
  },
  "metadata": {
    "ip_address": "192.168.1.10",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "request_id": "req-mno345"
  }
}
```

---

## 4. Fluxo de Logging em Operações Críticas

### Cenário: Criação de Agendamento com Sucesso

```
# 1. Log de Aplicação - Requisição recebida
INFO:2025-10-26T18:00:04.500Z:servico-agendamento:Requisição recebida para POST /agendamentos

# 2. Log de Aplicação - Tentativa de lock
INFO:2025-10-26T18:00:04.505Z:servico-agendamento:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z

# 3. Log de Aplicação no Coordenador - Lock recebido
INFO:2025-10-26T18:00:04.506Z:servico-coordenador:Recebido pedido de lock para recurso Hubble-Acad_2025-12-01T03:00:00Z

# 4. Log de Aplicação no Coordenador - Lock concedido
INFO:2025-10-26T18:00:04.507Z:servico-coordenador:Lock concedido para recurso Hubble-Acad_2025-12-01T03:00:00Z

# 5. Log de Aplicação - Lock adquirido
INFO:2025-10-26T18:00:05.120Z:servico-agendamento:Lock adquirido com sucesso para o recurso Hubble-Acad_2025-12-01T03:00:00Z

# 6. Log de Aplicação - Verificação BD
INFO:2025-10-26T18:00:05.122Z:servico-agendamento:Iniciando verificação de conflito no BD

# 7. Log de Aplicação - Salvamento
INFO:2025-10-26T18:00:05.123Z:servico-agendamento:Salvando novo agendamento no BD

# 8. LOG DE AUDITORIA - Evento de negócio crítico
{
  "timestamp_utc": "2025-10-26T18:00:05.123Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CRIADO",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 7,
    "cientista_nome": "Marie Curie",
    "cientista_email": "marie.curie@sorbonne.fr"
  },
  "details": {
    "agendamento_id": 123,
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:30:00Z"
  }
}

# 9. Log de Aplicação - Liberação de lock
INFO:2025-10-26T18:00:05.125Z:servico-agendamento:Liberando lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z

# 10. Log de Aplicação no Coordenador - Unlock
INFO:2025-10-26T18:00:05.126Z:servico-coordenador:Recebido pedido de unlock para recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:05.127Z:servico-coordenador:Lock liberado para recurso Hubble-Acad_2025-12-01T03:00:00Z
```

### Cenário: Requisição Concorrente (Lock Negado)

```
# 1. Log de Aplicação - Segunda requisição chega
INFO:2025-10-26T18:00:04.800Z:servico-agendamento:Requisição recebida para POST /agendamentos

# 2. Log de Aplicação - Tentativa de lock
INFO:2025-10-26T18:00:04.805Z:servico-agendamento:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z

# 3. Log de Aplicação no Coordenador - Pedido recebido
INFO:2025-10-26T18:00:04.806Z:servico-coordenador:Recebido pedido de lock para recurso Hubble-Acad_2025-12-01T03:00:00Z

# 4. Log de Aplicação no Coordenador - Lock negado
WARNING:2025-10-26T18:00:04.807Z:servico-coordenador:Recurso Hubble-Acad_2025-12-01T03:00:00Z já em uso, negando lock

# 5. Log de Aplicação - Lock negado
WARNING:2025-10-26T18:00:05.121Z:servico-agendamento:Falha ao adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z, recurso ocupado

# 6. LOG DE AUDITORIA - Tentativa falhou (importante para análise!)
{
  "timestamp_utc": "2025-10-26T18:00:05.121Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_TENTATIVA_FALHA",
  "service": "servico-agendamento",
  "user": {
    "cientista_id": 8,
    "cientista_nome": "Albert Einstein",
    "cientista_email": "einstein@princeton.edu"
  },
  "details": {
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:30:00Z",
    "motivo_falha": "Recurso em uso - lock não adquirido"
  }
}
```

---

## 5. Configuração de Logging

### Python/Flask (Serviço de Agendamento)

```python
import logging
import json
from datetime import datetime

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

# Logger customizado para auditoria
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(audit_handler)

def log_audit(event_type, user, details, metadata=None):
    """
    Registra um evento de auditoria.
    """
    audit_entry = {
        "timestamp_utc": datetime.utcnow().isoformat() + 'Z',
        "level": "AUDIT",
        "event_type": event_type,
        "service": "servico-agendamento",
        "user": user,
        "details": details,
        "metadata": metadata or {}
    }
    audit_logger.info(json.dumps(audit_entry, ensure_ascii=False))
```

### Node.js/Express (Serviço Coordenador)

```javascript
// Função auxiliar para logging estruturado
function log(level, message) {
    const timestamp = new Date().toISOString();
    console.log(`${level}:${timestamp}:servico-coordenador:${message}`);
}

// Exemplos de uso
log('INFO', 'Recebido pedido de lock para recurso X');
log('WARNING', 'Recurso X já em uso, negando lock');
```

---

## 6. Boas Práticas de Logging

### DO (Faça)
✅ **Sempre use UTC** para timestamps  
✅ **Inclua request_id** para correlacionar logs entre serviços  
✅ **Log de auditoria para TODAS as ações de negócio** críticas  
✅ **Use níveis apropriados** (INFO para fluxo normal, WARNING para situações anormais)  
✅ **Seja específico** nas mensagens (inclua IDs de recursos)  
✅ **Log antes e depois** de operações críticas  
✅ **Sanitize dados sensíveis** (não logue senhas, tokens)  

### DON'T (Não faça)
❌ **Não logue informações sensíveis** (senhas, tokens de autenticação)  
❌ **Não use timestamps locais** (sempre UTC)  
❌ **Não omita logs de auditoria** mesmo em caso de falha  
❌ **Não faça log excessivo** de operações triviais no nível INFO  
❌ **Não modifique logs de auditoria** depois de criados  
❌ **Não logue objetos complexos** sem estruturação (use JSON para auditoria)  

---

## 7. Análise de Logs

### Provando uma Condição de Corrida (Entrega 2)

Ao executar o teste de estresse SEM o coordenador, você verá:

```
# Múltiplos logs de APLICAÇÃO entrelaçados
INFO:2025-10-26T18:00:04.500Z:servico-agendamento:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.501Z:servico-agendamento:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.502Z:servico-agendamento:Requisição recebida para POST /agendamentos

# Múltiplos logs de AUDITORIA para o MESMO horário (PROVA DA FALHA!)
{"timestamp_utc": "2025-10-26T18:00:05.123Z", "event_type": "AGENDAMENTO_CRIADO", "details": {"agendamento_id": 123, "horario_inicio_utc": "2025-12-01T03:00:00Z"}}
{"timestamp_utc": "2025-10-26T18:00:05.124Z", "event_type": "AGENDAMENTO_CRIADO", "details": {"agendamento_id": 124, "horario_inicio_utc": "2025-12-01T03:00:00Z"}}
{"timestamp_utc": "2025-10-26T18:00:05.125Z", "event_type": "AGENDAMENTO_CRIADO", "details": {"agendamento_id": 125, "horario_inicio_utc": "2025-12-01T03:00:00Z"}}
```

### Provando a Exclusão Mútua (Entrega 3)

Com o coordenador implementado, você verá:

```
# Apenas UM log de auditoria de sucesso
{"timestamp_utc": "2025-10-26T18:00:05.123Z", "event_type": "AGENDAMENTO_CRIADO", "details": {"agendamento_id": 123}}

# Múltiplos logs de auditoria de FALHA (isso é correto!)
{"timestamp_utc": "2025-10-26T18:00:05.121Z", "event_type": "AGENDAMENTO_TENTATIVA_FALHA", "details": {"motivo_falha": "Recurso em uso"}}
{"timestamp_utc": "2025-10-26T18:00:05.122Z", "event_type": "AGENDAMENTO_TENTATIVA_FALHA", "details": {"motivo_falha": "Recurso em uso"}}
```

---

## Resumo

O sistema de logging do SCTEC é projetado para:

1. **Depuração**: Logs de aplicação ajudam a entender o fluxo
2. **Auditoria**: Logs de auditoria provam ações de negócio
3. **Observabilidade**: Permite rastrear requisições entre microserviços
4. **Compliance**: Atende requisitos regulatórios e jurídicos
5. **Diagnóstico**: Facilita identificação e resolução de problemas