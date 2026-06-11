# Regras do projeto

Estas regras devem ser seguidas por pessoas e agentes de IA ao evoluir o projeto.

## Arquitetura

- Preserve a arquitetura hexagonal.
- `domain` não pode importar FastAPI, boto3, OpenAI, Anthropic, PyMilvus ou Serverless.
- `application` coordena casos de uso, mas não deve conhecer detalhes HTTP.
- `infrastructure` implementa integrações externas.
- `api/routes` só traduz HTTP para casos de uso.
- `handlers` só traduz eventos Lambda para casos de uso.

## Código

- Use Python moderno com type hints.
- Prefira dataclasses para entidades de domínio.
- Use Pydantic apenas nas bordas HTTP ou quando fizer sentido para configuração.
- Não duplique lógica de negócio em adapters.
- Não crie abstrações sem necessidade real.
- Mantenha nomes explícitos e legíveis.

## Configuração

- Novas variáveis devem entrar em `.env.example`.
- Configuração em produção deve vir de SSM Parameter Store.
- Segredos nunca devem ser versionados.
- Não coloque chaves em YAML, Dockerfile, README ou testes.

## APIs

- Toda nova rota deve ser documentada em `docs/api-contracts.md`.
- Payloads devem usar camelCase na API pública.
- Internamente, use snake_case.
- Converta DTOs de API para entidades de domínio.

## RAG

- Preserve a busca híbrida dense + sparse/BM25.
- Preserve filtro por `agentId`.
- Preserve `extraFields` para metadados.
- Não acople Milvus aos casos de uso; use porta de vector store.

## LLM

- O usuário deve poder escolher provider e modelo na API.
- Providers LLM devem ser adapters atrás de portas.
- Não coloque lógica específica de OpenAI/Claude em casos de uso.

## AWS

- Preserve deploy via Serverless Framework.
- Preserve Lambda container image.
- Preserve OIDC no GitHub Actions.
- Preserve SQS + DLQ para processamento assíncrono.

## Commits

- Use commits pequenos e descritivos.
- Não misture refactor, feature e documentação no mesmo commit quando for possível separar.
- Antes de commitar, rode pelo menos:

```powershell
py -3.13 -m compileall app
npx serverless print --stage dev
```
