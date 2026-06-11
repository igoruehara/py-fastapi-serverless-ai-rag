# Skill: revisar-arquitetura

Use esta skill quando a tarefa for revisar se uma mudança respeita a arquitetura do projeto.

## Objetivo

Detectar violações de arquitetura, acoplamentos indevidos e riscos de evolução.

## Antes de começar

Leia:

- `AGENTS.md`
- `docs/architecture.md`
- `rules/project-rules.md`
- `rules/ai-continuation-rules.md`

## Checklist

### Domain

- `domain` não importa FastAPI.
- `domain` não importa boto3.
- `domain` não importa OpenAI, Anthropic ou PyMilvus.
- Entidades de domínio são simples e sem dependência externa.
- Ports usam `Protocol`.

### Application

- Casos de uso não dependem de HTTP.
- Casos de uso não instanciam SDK externo.
- Validações de fluxo ficam em casos de uso.
- Orquestração é clara e testável.

### Infrastructure

- SDKs externos estão isolados em adapters.
- Respostas externas são convertidas para objetos simples.
- Erros de configuração são claros.

### API

- Rotas apenas validam payload, chamam caso de uso e formatam resposta.
- DTOs Pydantic não vazam para `domain`.
- Payloads públicos usam camelCase.

### Configuração

- Novas variáveis estão em `.env.example`.
- Não há segredo versionado.
- SSM continua sendo o caminho de produção.

### Deploy

- `serverless.yaml` continua válido.
- `yml/provider.yml`, `yml/environment.yml` e `yml/custom.yml` seguem separados.
- GitHub Actions continua usando OIDC.

## Como reportar achados

Ordene por severidade:

1. Crítico.
2. Alto.
3. Médio.
4. Baixo.

Para cada achado, informe:

- Arquivo.
- Linha aproximada.
- Problema.
- Impacto.
- Sugestão de correção.

## Validação

Rode:

```powershell
py -3.13 -m compileall app
npx serverless print --stage dev
```

## Critério de pronto

A revisão está pronta quando:

- Violações arquiteturais foram identificadas ou descartadas.
- Riscos foram explicados.
- Testes/validações executados foram informados.
