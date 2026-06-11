# Padrões de código

Este documento define padrões para manter o projeto simples, testável e fácil de evoluir com IA.

## Linguagem

- Código em inglês para nomes de classes, funções, variáveis e arquivos.
- Documentação pode ser em português.
- Mensagens de erro podem ser em inglês quando forem internas ou técnicas.

## Python

- Use type hints.
- Use `dataclass` para entidades de domínio.
- Use `Protocol` para portas.
- Evite herança desnecessária.
- Prefira funções pequenas e explícitas.
- Não adicione comentários óbvios.

## FastAPI

- Use Pydantic para DTOs de entrada e saída.
- Payload público deve usar camelCase.
- Código interno deve usar snake_case.
- Rotas devem converter DTOs para entidades de domínio.
- Rotas não devem conter regra de negócio.

## Application

- Casos de uso devem orquestrar portas.
- Casos de uso podem validar regras do fluxo.
- Casos de uso não devem instanciar SDK externo diretamente.

## Domain

- Não importar frameworks.
- Não importar boto3.
- Não importar OpenAI, Anthropic ou PyMilvus.
- Não depender de variáveis de ambiente.

## Infrastructure

- SDKs externos devem ficar aqui.
- Adapters devem converter respostas externas para objetos simples.
- Erros de configuração podem levantar `RuntimeError`.
- Evite vazar objetos crus de SDK para `application`.

## Configuração

- Use `app/core/config.py`.
- Novas variáveis devem entrar em `.env.example`.
- Em AWS, use SSM.
- Nunca versionar `.env`.

## Testes

Ao adicionar testes:

- Testes unitários devem focar em `application` e `domain`.
- Use mocks/fakes para portas.
- Não chame OpenAI, Claude, AWS ou Milvus em teste unitário.
- Testes de integração devem ser separados e marcados.

Sugestão de estrutura futura:

```text
tests/
  unit/
    application/
    domain/
  integration/
    infrastructure/
```

## Validações locais

```powershell
py -3.13 -m compileall app
npx serverless print --stage dev
```

Quando dependências estiverem instaladas:

```powershell
ruff check .
pytest
```

## Git

- Commits devem ser pequenos e descritivos.
- Não commitar arquivos gerados.
- Não commitar secrets.
- Não commitar `node_modules`, `.serverless`, `.venv` ou `__pycache__`.

## Documentação

Atualize a documentação quando:

- Criar endpoint.
- Alterar payload.
- Alterar fluxo arquitetural.
- Adicionar variável de ambiente.
- Adicionar integração externa.
