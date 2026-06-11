# Regras para continuidade com IA

Este arquivo é pensado para agentes de IA que precisam continuar o projeto sem perder contexto.

## Antes de alterar

1. Leia `README.md`.
2. Leia `AGENTS.md`.
3. Leia `docs/sdd/architecture.md`.
4. Leia `docs/sdd/api-contracts.md` se a tarefa envolver endpoint.
5. Leia `docs/sdd/coding-standards.md` antes de alterar código.

## Como responder a uma demanda

- Se for uma nova API, crie ou atualize DTO, entidade, caso de uso, porta/adapters e documentação.
- Se for uma nova integração externa, crie uma porta em `domain/ports` e um adapter em `infrastructure`.
- Se for mudança de RAG, preserve compatibilidade de payload sempre que possível.
- Se for mudança de deploy, valide com `npx serverless print`.

## O que evitar

- Criar lógica de negócio dentro de rota.
- Criar cliente OpenAI, Anthropic, boto3 ou Milvus em `domain`.
- Retornar objetos crus de SDK diretamente pela API.
- Criar variáveis sem atualizar `.env.example`.
- Fazer mudanças destrutivas de Git.
- Ignorar validações locais.

## Critério de pronto

Uma alteração está pronta quando:

- O código compila.
- A arquitetura continua respeitada.
- A documentação afetada foi atualizada.
- Não há segredo versionado.
- O `serverless print` passa se a mudança afetar deploy/configuração.
