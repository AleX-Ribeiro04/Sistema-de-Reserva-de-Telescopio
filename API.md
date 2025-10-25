# Especificação da API - SCTEC

## Serviço de Agendamento (Flask - Porta 5000)

### Base URL
```
http://localhost:5000
```

---

## 1. Sincronização de Tempo

### GET /time

Retorna o timestamp atual do servidor para sincronização de relógio do cliente.

**Request:**
```http
GET /time HTTP/1.1
Host: localhost:5000
```

**Response (200 OK):**
```json
{
  "server_time_utc": "2025-10-26T18:00:00.123Z",
  "_links": {
    "self": {
      "href": "/time"
    },
    "agendamentos": {
      "href": "/agendamentos",
      "method": "GET",
      "description": "Listar todos os agendamentos"
    },
    "criar_agendamento": {
      "href": "/agendamentos",
      "method": "POST",
      "description": "Criar um novo agendamento"
    }
  }
}
```

---

## 2. Cientistas

### POST /cientistas

Cria um novo cientista no sistema.

**Request:**
```http
POST /cientistas HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "nome": "Marie Curie",
  "email": "marie.curie@sorbonne.fr",
  "instituicao": "Université Paris Sciences et Lettres",
  "pais": "França"
}
```

**Response (201 Created):**
```json
{
  "id": 7,
  "nome": "Marie Curie",
  "email": "marie.curie@sorbonne.fr",
  "instituicao": "Université Paris Sciences et Lettres",
  "pais": "França",
  "data_cadastro": "2025-10-26T18:00:00Z",
  "_links": {
    "self": {
      "href": "/cientistas/7"
    },
    "agendamentos": {
      "href": "/cientistas/7/agendamentos",
      "method": "GET",
      "description": "Ver agendamentos deste cientista"
    },
    "criar_agendamento": {
      "href": "/agendamentos",
      "method": "POST",
      "description": "Criar novo agendamento"
    }
  }
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Dados inválidos",
  "details": "O campo 'email' é obrigatório",
  "_links": {
    "self": {
      "href": "/cientistas"
    }
  }
}
```

**Response (409 Conflict):**
```json
{
  "error": "Email já cadastrado",
  "details": "Já existe um cientista com o email 'marie.curie@sorbonne.fr'",
  "_links": {
    "self": {
      "href": "/cientistas"
    },
    "cientista_existente": {
      "href": "/cientistas/7"
    }
  }
}
```

---

### GET /cientistas/{id}

Retorna os dados de um cientista específico.

**Request:**
```http
GET /cientistas/7 HTTP/1.1
Host: localhost:5000
```

**Response (200 OK):**
```json
{
  "id": 7,
  "nome": "Marie Curie",
  "email": "marie.curie@sorbonne.fr",
  "instituicao": "Université Paris Sciences et Lettres",
  "pais": "França",
  "data_cadastro": "2025-10-26T18:00:00Z",
  "_links": {
    "self": {
      "href": "/cientistas/7"
    },
    "agendamentos": {
      "href": "/cientistas/7/agendamentos",
      "method": "GET",
      "description": "Ver todos os agendamentos deste cientista"
    },
    "atualizar": {
      "href": "/cientistas/7",
      "method": "PUT",
      "description": "Atualizar dados do cientista"
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Cientista não encontrado",
  "details": "Não existe cientista com ID 7",
  "_links": {
    "cientistas": {
      "href": "/cientistas",
      "method": "GET",
      "description": "Listar todos os cientistas"
    }
  }
}
```

---

### GET /cientistas

Lista todos os cientistas cadastrados.

**Request:**
```http
GET /cientistas HTTP/1.1
Host: localhost:5000
```

**Response (200 OK):**
```json
{
  "total": 2,
  "cientistas": [
    {
      "id": 7,
      "nome": "Marie Curie",
      "email": "marie.curie@sorbonne.fr",
      "instituicao": "Université Paris Sciences et Lettres",
      "pais": "França",
      "_links": {
        "self": {
          "href": "/cientistas/7"
        }
      }
    },
    {
      "id": 8,
      "nome": "Albert Einstein",
      "email": "einstein@princeton.edu",
      "instituicao": "Princeton University",
      "pais": "Estados Unidos",
      "_links": {
        "self": {
          "href": "/cientistas/8"
        }
      }
    }
  ],
  "_links": {
    "self": {
      "href": "/cientistas"
    },
    "criar": {
      "href": "/cientistas",
      "method": "POST",
      "description": "Criar novo cientista"
    }
  }
}
```

---

## 3. Agendamentos

### POST /agendamentos

Cria um novo agendamento. Este endpoint implementa exclusão mútua via coordenador.

**Request:**
```http
POST /agendamentos HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "cientista_id": 7,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
  "descricao": "Observação da estrutura de braços espirais"
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "cientista_id": 7,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "status": "confirmado",
  "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
  "descricao": "Observação da estrutura de braços espirais",
  "data_criacao": "2025-10-26T18:00:05Z",
  "data_atualizacao": "2025-10-26T18:00:05Z",
  "_links": {
    "self": {
      "href": "/agendamentos/123"
    },
    "cientista": {
      "href": "/cientistas/7",
      "description": "Ver dados do cientista"
    },
    "cancelar": {
      "href": "/agendamentos/123/cancelar",
      "method": "POST",
      "description": "Cancelar este agendamento"
    },
    "todos_agendamentos": {
      "href": "/agendamentos",
      "method": "GET",
      "description": "Listar todos os agendamentos"
    }
  }
}
```

**Response (400 Bad Request - Validação):**
```json
{
  "error": "Dados inválidos",
  "details": "A duração mínima do agendamento é de 5 minutos",
  "_links": {
    "self": {
      "href": "/agendamentos"
    },
    "documentacao": {
      "href": "/docs/regras-agendamento"
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Cientista não encontrado",
  "details": "Não existe cientista com ID 7",
  "_links": {
    "cientistas": {
      "href": "/cientistas",
      "method": "GET"
    }
  }
}
```

**Response (409 Conflict - Horário Ocupado):**
```json
{
  "error": "Horário não disponível",
  "details": "Já existe um agendamento para este horário",
  "agendamento_conflitante": {
    "id": 122,
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:30:00Z"
  },
  "_links": {
    "self": {
      "href": "/agendamentos"
    },
    "agendamento_conflitante": {
      "href": "/agendamentos/122"
    },
    "horarios_disponiveis": {
      "href": "/agendamentos/disponiveis?data=2025-12-01",
      "method": "GET",
      "description": "Ver horários disponíveis nesta data"
    }
  }
}
```

**Response (409 Conflict - Lock Não Adquirido):**
```json
{
  "error": "Recurso em uso",
  "details": "Outro usuário está tentando agendar este horário simultaneamente. Tente novamente.",
  "_links": {
    "self": {
      "href": "/agendamentos"
    },
    "retry": {
      "href": "/agendamentos",
      "method": "POST",
      "description": "Tentar novamente"
    }
  }
}
```

---

### GET /agendamentos/{id}

Retorna os detalhes de um agendamento específico.

**Request:**
```http
GET /agendamentos/123 HTTP/1.1
Host: localhost:5000
```

**Response (200 OK - Status: confirmado):**
```json
{
  "id": 123,
  "cientista_id": 7,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "status": "confirmado",
  "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
  "descricao": "Observação da estrutura de braços espirais",
  "data_criacao": "2025-10-26T18:00:05Z",
  "data_atualizacao": "2025-10-26T18:00:05Z",
  "_links": {
    "self": {
      "href": "/agendamentos/123"
    },
    "cientista": {
      "href": "/cientistas/7"
    },
    "cancelar": {
      "href": "/agendamentos/123/cancelar",
      "method": "POST",
      "description": "Cancelar este agendamento"
    },
    "atualizar": {
      "href": "/agendamentos/123",
      "method": "PUT",
      "description": "Atualizar descrição ou objeto de observação"
    }
  }
}
```

**Response (200 OK - Status: cancelado):**
```json
{
  "id": 123,
  "cientista_id": 7,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "status": "cancelado",
  "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
  "descricao": "Observação da estrutura de braços espirais",
  "data_criacao": "2025-10-26T18:00:05Z",
  "data_atualizacao": "2025-10-26T18:10:30Z",
  "_links": {
    "self": {
      "href": "/agendamentos/123"
    },
    "cientista": {
      "href": "/cientistas/7"
    },
    "criar_novo": {
      "href": "/agendamentos",
      "method": "POST",
      "description": "Criar novo agendamento"
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Agendamento não encontrado",
  "details": "Não existe agendamento com ID 123",
  "_links": {
    "agendamentos": {
      "href": "/agendamentos",
      "method": "GET"
    }
  }
}
```

---

### GET /agendamentos

Lista todos os agendamentos com filtros opcionais.

**Request:**
```http
GET /agendamentos?status=confirmado&data_inicio=2025-12-01 HTTP/1.1
Host: localhost:5000
```

**Query Parameters:**
- `status` (opcional): Filtrar por status (confirmado, cancelado, concluido)
- `data_inicio` (opcional): Filtrar agendamentos a partir desta data (formato: YYYY-MM-DD)
- `cientista_id` (opcional): Filtrar por cientista

**Response (200 OK):**
```json
{
  "total": 2,
  "filtros_aplicados": {
    "status": "confirmado",
    "data_inicio": "2025-12-01"
  },
  "agendamentos": [
    {
      "id": 123,
      "cientista_id": 7,
      "horario_inicio_utc": "2025-12-01T03:00:00Z",
      "horario_fim_utc": "2025-12-01T03:30:00Z",
      "status": "confirmado",
      "_links": {
        "self": {
          "href": "/agendamentos/123"
        }
      }
    },
    {
      "id": 124,
      "cientista_id": 8,
      "horario_inicio_utc": "2025-12-01T10:00:00Z",
      "horario_fim_utc": "2025-12-01T11:00:00Z",
      "status": "confirmado",
      "_links": {
        "self": {
          "href": "/agendamentos/124"
        }
      }
    }
  ],
  "_links": {
    "self": {
      "href": "/agendamentos?status=confirmado&data_inicio=2025-12-01"
    },
    "criar": {
      "href": "/agendamentos",
      "method": "POST",
      "description": "Criar novo agendamento"
    },
    "todos": {
      "href": "/agendamentos",
      "method": "GET",
      "description": "Ver todos os agendamentos sem filtros"
    }
  }
}
```

---

### POST /agendamentos/{id}/cancelar

Cancela um agendamento existente.

**Request:**
```http
POST /agendamentos/123/cancelar HTTP/1.1
Host: localhost:5000
```

**Response (200 OK):**
```json
{
  "id": 123,
  "cientista_id": 7,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:30:00Z",
  "status": "cancelado",
  "objeto_observacao": "NGC 1300 - Galáxia Espiral Barrada",
  "descricao": "Observação da estrutura de braços espirais",
  "data_criacao": "2025-10-26T18:00:05Z",
  "data_atualizacao": "2025-10-26T18:10:30Z",
  "_links": {
    "self": {
      "href": "/agendamentos/123"
    },
    "cientista": {
      "href": "/cientistas/7"
    },
    "criar_novo": {
      "href": "/agendamentos",
      "method": "POST",
      "description": "Criar novo agendamento"
    },
    "agendamentos_cientista": {
      "href": "/cientistas/7/agendamentos",
      "method": "GET"
    }
  }
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Operação inválida",
  "details": "Não é possível cancelar um agendamento que já foi cancelado",
  "_links": {
    "self": {
      "href": "/agendamentos/123"
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": "Agendamento não encontrado",
  "details": "Não existe agendamento com ID 123",
  "_links": {
    "agendamentos": {
      "href": "/agendamentos",
      "method": "GET"
    }
  }
}
```

---

### GET /cientistas/{id}/agendamentos

Lista todos os agendamentos de um cientista específico.

**Request:**
```http
GET /cientistas/7/agendamentos HTTP/1.1
Host: localhost:5000
```

**Response (200 OK):**
```json
{
  "cientista_id": 7,
  "total": 3,
  "agendamentos": [
    {
      "id": 123,
      "horario_inicio_utc": "2025-12-01T03:00:00Z",
      "horario_fim_utc": "2025-12-01T03:30:00Z",
      "status": "confirmado",
      "_links": {
        "self": {
          "href": "/agendamentos/123"
        }
      }
    },
    {
      "id": 125,
      "horario_inicio_utc": "2025-12-02T15:00:00Z",
      "horario_fim_utc": "2025-12-02T16:00:00Z",
      "status": "confirmado",
      "_links": {
        "self": {
          "href": "/agendamentos/125"
        }
      }
    },
    {
      "id": 120,
      "horario_inicio_utc": "2025-11-28T08:00:00Z",
      "horario_fim_utc": "2025-11-28T09:00:00Z",
      "status": "cancelado",
      "_links": {
        "self": {
          "href": "/agendamentos/120"
        }
      }
    }
  ],
  "_links": {
    "self": {
      "href": "/cientistas/7/agendamentos"
    },
    "cientista": {
      "href": "/cientistas/7"
    },
    "criar_agendamento": {
      "href": "/agendamentos",
      "method": "POST"
    }
  }
}
```

---

## Serviço Coordenador (Node.js - Porta 3000)

### Base URL
```
http://localhost:3000
```

---

### POST /lock

Adquire um lock para um recurso específico.

**Request:**
```http
POST /lock HTTP/1.1
Host: localhost:3000
Content-Type: application/json

{
  "resource_id": "Hubble-Acad_2025-12-01T03:00:00Z"
}
```

**Response (200 OK - Lock adquirido):**
```json
{
  "success": true,
  "resource_id": "Hubble-Acad_2025-12-01T03:00:00Z",
  "locked_at": "2025-10-26T18:00:05.100Z",
  "message": "Lock adquirido com sucesso"
}
```

**Response (409 Conflict - Recurso já travado):**
```json
{
  "success": false,
  "resource_id": "Hubble-Acad_2025-12-01T03:00:00Z",
  "message": "Recurso já está em uso",
  "locked_since": "2025-10-26T18:00:04.500Z"
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "resource_id é obrigatório"
}
```

---

### POST /unlock

Libera um lock de um recurso específico.

**Request:**
```http
POST /unlock HTTP/1.1
Host: localhost:3000
Content-Type: application/json

{
  "resource_id": "Hubble-Acad_2025-12-01T03:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "resource_id": "Hubble-Acad_2025-12-01T03:00:00Z",
  "message": "Lock liberado com sucesso"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "resource_id": "Hubble-Acad_2025-12-01T03:00:00Z",
  "message": "Nenhum lock encontrado para este recurso"
}
```

---

## Códigos de Status HTTP Utilizados

| Código | Significado | Uso no Sistema |
|--------|-------------|----------------|
| 200 | OK | Requisição bem-sucedida (GET, POST cancelar, POST unlock) |
| 201 | Created | Recurso criado com sucesso (POST cientista, POST agendamento) |
| 400 | Bad Request | Dados de entrada inválidos ou regras de validação violadas |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Conflito de recursos (horário já ocupado, lock não adquirido, email duplicado) |
| 500 | Internal Server Error | Erro inesperado no servidor |

---

## Princípios HATEOAS

Todas as respostas da API incluem um objeto `_links` que contém:

1. **self**: Link para o recurso atual
2. **Ações disponíveis**: Links para as próximas ações possíveis baseadas no estado do recurso
3. **Recursos relacionados**: Links para recursos relacionados (cientista, agendamentos, etc.)
4. **method**: Método HTTP a ser usado
5. **description**: Descrição legível da ação

### Exemplo de Navegação HATEOAS:

```
1. Cliente faz GET /time
2. Resposta inclui link para "criar_agendamento"
3. Cliente usa esse link para POST /agendamentos
4. Resposta inclui link para "cancelar"
5. Cliente pode usar esse link para cancelar se necessário
```

Isso permite que o cliente descubra dinamicamente as ações disponíveis sem conhecimento prévio da estrutura da API.