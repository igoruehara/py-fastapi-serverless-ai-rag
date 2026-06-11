# Workflow: Deploy Serverless AWS

Este workflow documenta como o projeto é empacotado e publicado na AWS.

## Componentes

```text
FastAPI
  -> Mangum
  -> Lambda container image
  -> ECR
  -> API Gateway HTTP
  -> API Gateway WebSocket
  -> SQS + DLQ
  -> DynamoDB
  -> SSM Parameter Store
```

## Arquivos principais

```text
Dockerfile
serverless.yaml
yml/custom.yml
yml/environment.yml
yml/provider.yml
.github/workflows/aws.yml
```

## Docker

Imagem base:

```text
public.ecr.aws/lambda/python:3.14
```

Comando da Lambda:

```text
app.lambda_handler.handler
```

O Dockerfile instala `requirements.txt` e copia `app/`.

## Serverless

Entrada principal:

```text
serverless.yaml
```

Arquivos separados:

```text
yml/custom.yml       -> prefixo SSM
yml/environment.yml  -> variáveis da Lambda
yml/provider.yml     -> provider AWS, ECR, IAM, CORS
```

Eventos da função:

```text
HTTP API ANY /
HTTP API ANY /{proxy+}
WebSocket $connect
WebSocket $disconnect
WebSocket $default
SQS NlpConversationQueue
```

Recursos criados:

```text
NlpConversationQueue
NlpConversationDLQ
ConnectionsTable
```

## Lambda dispatcher

Arquivo:

```text
app/lambda_handler.py
```

Tipos de evento detectados:

```text
http
sqs
sns
scheduled
warmup
direct
wsConnect
wsDisconnect
wsDefault
unknown
```

HTTP é enviado para FastAPI via Mangum.

SQS é enviado para `app/handlers/sqs.py`.

WebSocket é enviado para `app/handlers/websocket.py`.

## Configuração por SSM

Em AWS:

```text
APP_CONFIG_SOURCE=ssm
APP_SSM_PREFIX=/${service}/${stage}
```

O código carrega parâmetros por path em:

```text
app/core/config.py
```

Parâmetro operacional:

```text
/dev-fastapi-serverless/dev/OPENAI_API_KEY
```

Vira:

```text
OPENAI_API_KEY
```

## CI/CD

Workflow:

```text
.github/workflows/aws.yml
```

Branches:

```text
main    -> dev
homolog -> hml
prd     -> prd
```

Autenticação AWS:

```text
GitHub Actions OIDC -> IAM Role -> STS temporary credentials
```

Secrets necessários:

```text
AWS_DEPLOY_ROLE_ARN
SERVERLESS_ACCESS_KEY
```

Variável opcional:

```text
AWS_REGION
```

## Comandos locais

Instalar dependências Node:

```powershell
npm install
```

Validar Serverless:

```powershell
npx serverless print --stage dev
```

Deploy manual:

```powershell
npx serverless deploy --stage dev
```

## Validações antes de deploy

```powershell
py -3.13 -m compileall app
npx serverless print --stage dev
```

## Pontos de manutenção

- Altere variáveis de Lambda em `yml/environment.yml`.
- Altere permissões IAM em `yml/provider.yml`.
- Altere recursos AWS em `serverless.yaml`.
- Não coloque secrets no YAML.
- Use SSM para chaves de OpenAI, Claude e Milvus.
