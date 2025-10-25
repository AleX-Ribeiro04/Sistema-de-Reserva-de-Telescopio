# MODELOS.md

## Entidade: Cientista
Representa o pesquisador que solicita tempo de observação.

| Campo | Tipo | Descrição |
|--------|------|-----------|
| id | inteiro | Identificador único do cientista |
| nome | string | Nome completo |
| instituicao | string | Instituição de origem |
| email | string | Contato do pesquisador |

---

## Entidade: Telescopio
Representa um telescópio disponível para agendamento.

| Campo | Tipo | Descrição |
|--------|------|-----------|
| id | inteiro | Identificador único do telescópio |
| nome | string | Nome (ex: Hubble-Acad) |
| localizacao | string | Localização ou código de órbita |
| status | string | "disponível" ou "em manutenção" |

---

## Entidade: Agendamento
Representa a reserva de tempo de observação.

| Campo | Tipo | Descrição |
|--------|------|-----------|
| id | inteiro | Identificador único |
| cientista_id | inteiro | Chave estrangeira para Cientista |
| telescopio_id | inteiro | Chave estrangeira para Telescopio |
| horario_inicio_utc | datetime | Início da observação |
| horario_fim_utc | datetime | Fim da observação |
| criado_em | datetime | Data de criação do registro |
| status | string | “ativo”, “cancelado” |

---
