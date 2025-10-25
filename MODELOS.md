# Modelos de Dados - SCTEC

## 1. Cientista

Representa um pesquisador registrado no sistema que pode realizar agendamentos.

### Atributos:
- **id** (integer, PK): Identificador único do cientista
- **nome** (string, obrigatório): Nome completo do cientista
- **email** (string, obrigatório, único): Email institucional
- **instituicao** (string, obrigatório): Instituição de pesquisa vinculada
- **pais** (string, obrigatório): País de origem
- **data_cadastro** (datetime, UTC): Data e hora do cadastro no sistema

### Exemplo:
```json
{
  "id": 7,
  "nome": "Marie Curie",
  "email": "marie.curie@sorbonne.fr",
  "instituicao": "Université Paris Sciences et Lettres",
  "pais": "França",
  "data_cadastro": "2025-01-15T10:30:00Z"
}
```

---

## 2. Agendamento

Representa uma reserva de tempo de observação no telescópio espacial.

### Atributos:
- **id** (integer, PK): Identificador único do agendamento
- **cientista_id** (integer, FK, obrigatório): Referência ao cientista que fez a reserva
- **horario_inicio_utc** (datetime, obrigatório): Horário de início da observação (UTC)
- **horario_fim_utc** (datetime, obrigatório): Horário de término da observação (UTC)
- **status** (string, obrigatório): Status atual do agendamento
  - Valores possíveis: `"confirmado"`, `"cancelado"`, `"concluido"`
- **objeto_observacao** (string, opcional): Nome do objeto celeste a ser observado
- **descricao** (string, opcional): Descrição do propósito científico da observação
- **data_criacao** (datetime, UTC): Timestamp de quando o agendamento foi criado
- **data_atualizacao** (datetime, UTC): Timestamp da última atualização

### Regras de Negócio:
1. **Duração mínima**: 5 minutos
2. **Duração máxima**: 2 horas por agendamento
3. **Slots de tempo**: Devem começar em múltiplos de 5 minutos (03:00, 03:05, 03:10...)
4. **Não sobreposição**: Não pode haver dois agendamentos com horários conflitantes
5. **Antecedência mínima**: Agendamentos devem ser feitos com pelo menos 24h de antecedência
6. **Cancelamento**: Só podem ser cancelados agendamentos com status "confirmado"

### Exemplo:
```json
{
  "id": 123,
  "cientista_id": 7,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "status": "confirmado",
  "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
  "descricao": "Observação da estrutura de braços espirais para estudo de formação estelar",
  "data_criacao": "2025-11-15T14:22:10Z",
  "data_atualizacao": "2025-11-15T14:22:10Z"
}
```

---

## 3. Recurso de Lock (Coordenador)

Este não é persistido em banco de dados, mas mantido em memória pelo Serviço Coordenador.

### Estrutura:
- **resource_id** (string): Identificador único do recurso sendo travado
  - Formato: `"Hubble-Acad_{horario_inicio_utc}"`
  - Exemplo: `"Hubble-Acad_2025-12-01T03:00:00Z"`
- **locked_at** (timestamp): Momento em que o lock foi adquirido
- **locked** (boolean): Se o recurso está travado ou não

### Exemplo (estrutura interna do coordenador):
```javascript
{
  "Hubble-Acad_2025-12-01T03:00:00Z": {
    "locked": true,
    "locked_at": 1732468820500
  }
}
```

---

## 4. Diagrama de Relacionamento

```
┌─────────────────┐
│   Cientista     │
│                 │
│ - id (PK)       │
│ - nome          │
│ - email         │
│ - instituicao   │
│ - pais          │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│  Agendamento    │
│                 │
│ - id (PK)       │
│ - cientista_id  │───── FK para Cientista
│ - horario_inicio│
│ - horario_fim   │
│ - status        │
│ - objeto_obs    │
│ - descricao     │
└─────────────────┘
```

---

## Observações Importantes

1. **Timezone**: Todos os timestamps devem estar em UTC (ISO 8601)
2. **Validação de horários**: O sistema deve validar que `horario_fim_utc > horario_inicio_utc`
3. **Identificador de recurso**: Para operações de lock, o identificador será construído como: `f"Hubble-Acad_{horario_inicio_utc}"`
4. **Atomicidade**: As operações de criação de agendamento devem ser atômicas (transacionais)