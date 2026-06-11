# AGENTS.md

Este arquivo orienta pessoas e agentes de IA que forem evoluir este projeto.

O objetivo é manter o código previsível, seguro e coerente com a arquitetura hexagonal.

## Contexto do projeto

Este repositório é um backend em Python com FastAPI para aplicações de IA generativa.

Ele combina:

- FastAPI.
- AWS Lambda Container.
- Serverless Framework.
- API Gateway HTTP e WebSocket.
- SQS + DLQ.
- DynamoDB para conexões WebSocket.
- SSM Parameter Store para configuração.
- OpenAI e Claude como provedores LLM.
- Milvus para RAG com busca híbrida.
- Arquitetura hexagonal.

## Regra principal

Não coloque regra de negócio nas rotas FastAPI, handlers Lambda ou adapters externos.

Use sempre este fluxo:

```text
api/routes ou handlers
  -> application/use_cases
    -> domain/entities + domain/ports
      -> infrastructure/adapters
```

## Camadas

### `domain/`

Contém entidades e portas. Não deve depender de FastAPI, boto3, OpenAI, Claude, Milvus ou qualquer SDK externo.

Use para:

- Entidades puras.
- Protocolos/ports.
- Tipos de domínio.
- Regras que não precisam de infraestrutura.

### `application/`

Contém casos de uso. Pode orquestrar portas do domínio, validar fluxo e coordenar adapters via interfaces.

Use para:

- Orquestração de chat.
- Orquestração de RAG.
- Enfileiramento de conversa.
- Processamento de mensagens.

### `infrastructure/`

Contém adapters concretos.

Use para:

- OpenAI.
- Claude.
- Milvus.
- SQS.
- Conversão de payloads externos.
- Chunking e normalização técnica.

### `api/`

Contém apenas entrada HTTP com FastAPI.

Use para:

- DTOs de entrada e saída.
- Mapeamento para entidades de domínio.
- Tratamento HTTP de erros.
- Chamada de casos de uso.

### `handlers/`

Contém entradas Lambda fora do HTTP.

Use para:

- SQS.
- WebSocket.
- Eventos diretos.

## Regras para novas features

Ao criar uma nova feature:

1. Atualize ou crie a entidade em `app/domain/entities`.
2. Crie portas em `app/domain/ports` se houver dependência externa.
3. Crie o caso de uso em `app/application/use_cases`.
4. Implemente adapters em `app/infrastructure`.
5. Exponha a entrada em `app/api/routes` ou `app/handlers`.
6. Registre dependências em `app/application/container.py`.
7. Atualize `docs/api-contracts.md` se houver novo endpoint.
8. Atualize `docs/architecture.md` se houver decisão arquitetural relevante.
9. Atualize `.env.example` se houver nova configuração.

## Regras para IA

Ao usar Codex, Cursor, Claude Code, Copilot ou outro agente:

- Leia `README.md`, `docs/architecture.md` e `docs/coding-standards.md` antes de alterar código.
- Não invente uma arquitetura paralela.
- Não mova regras para `api/routes`.
- Não importe SDKs externos dentro de `domain`.
- Não commite `.env`, chaves, tokens ou credenciais.
- Não remova OIDC do GitHub Actions.
- Não substitua SSM por variáveis hardcoded.
- Não misture código de infraestrutura AWS com regra de domínio.
- Prefira mudanças pequenas e documentadas.
- Rode validações antes de concluir.

## Validações recomendadas

```powershell
py -3.13 -m compileall app
npx serverless print --stage dev
```

Se o ambiente virtual estiver configurado:

```powershell
pytest
ruff check .
```

## Onde documentar

- Arquitetura: `docs/architecture.md`
- Contratos HTTP: `docs/api-contracts.md`
- Padrões de código: `docs/coding-standards.md`
- Workflows de negócio: `docs/workflows/`
- Regras para agentes: `AGENTS.md` e `rules/`
- Skills locais para agentes: `.agents/skills/`
