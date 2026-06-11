# Skill: criar-skill-api

Use esta skill quando a tarefa for criar ou alterar uma API HTTP no projeto.

## Objetivo

Criar endpoints FastAPI respeitando a arquitetura hexagonal:

```text
api/routes
  -> application/use_cases
    -> domain/entities + domain/ports
      -> infrastructure/adapters
```

## Antes de começar

Leia:

- `AGENTS.md`
- `docs/sdd/architecture.md`
- `docs/sdd/api-contracts.md`
- `docs/sdd/coding-standards.md`
- `docs/ai/rules.md`

## Passo a passo

1. Entenda o contrato desejado da API.
2. Crie ou atualize DTOs Pydantic em `app/api/routes`.
3. Crie ou atualize entidades em `app/domain/entities`.
4. Se houver dependência externa, crie uma porta em `app/domain/ports`.
5. Crie ou atualize o caso de uso em `app/application/use_cases`.
6. Implemente adapters externos em `app/infrastructure`, se necessário.
7. Registre dependências em `app/application/container.py`.
8. Inclua a rota em `app/main.py`, se for um novo router.
9. Atualize `docs/sdd/api-contracts.md`.
10. Atualize `.env.example`, se houver nova configuração.

## Regras

- Não coloque regra de negócio em `api/routes`.
- Não importe SDKs externos em `domain`.
- Não retorne objetos crus de SDK.
- Payload público deve usar camelCase.
- Código interno deve usar snake_case.
- Erros de validação devem retornar HTTP 400.
- Erros de configuração devem retornar HTTP 500.

## Validação

Rode:

```powershell
py -3.13 -m compileall app
```

Se a alteração envolver deploy/configuração:

```powershell
npx serverless print --stage dev
```

## Critério de pronto

- Endpoint documentado.
- Caso de uso criado.
- Camadas respeitadas.
- Código compilando.
- Sem segredos versionados.
