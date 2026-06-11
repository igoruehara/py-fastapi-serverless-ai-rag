# Workflow: RAG com Milvus

Este workflow documenta o fluxo real de ingestão, busca híbrida e chat com RAG.

## Endpoints

```text
POST /api/rag/create-collection
POST /api/rag/create-index
POST /api/rag/add-documents
POST /api/rag/embedding-create
POST /api/rag/search-hybrid
POST /api/rag/chat-llm-rag
```

Arquivo:

```text
app/api/routes/rag.py
```

## Fluxo de criação da collection

```text
CreateCollectionRequest
  -> RagUseCase.create_collection
  -> RagVectorStorePort
  -> MilvusRagVectorStore.create_collection
```

Campos criados no Milvus:

```text
id              Int64 autoID primary key
embeddingName   VarChar
agentId         VarChar
embeddingId     VarChar
extraFields     JSON
text            VarChar com analyzer
dense           FloatVector
sparse          SparseFloatVector gerado por BM25
```

Dimensão padrão:

```text
MILVUS_EMBEDDING_DIM=3072
```

## Fluxo de criação de índices

```text
CreateIndexRequest
  -> RagUseCase.create_index
  -> MilvusRagVectorStore.create_index
```

Índices:

```text
dense  -> HNSW + COSINE
sparse -> SPARSE_INVERTED_INDEX + BM25
```

## Fluxo de ingestão

```text
AddDocumentsRequest
  -> RagDocument
  -> RagUseCase.add_documents
  -> TextChunker
  -> normalize_extra_fields
  -> OpenAiEmbeddingAdapter
  -> MilvusRagVectorStore.add_chunks
```

Arquivos envolvidos:

```text
app/application/use_cases/rag.py
app/domain/entities/rag.py
app/domain/ports/embeddings.py
app/domain/ports/vector_store.py
app/infrastructure/text/chunker.py
app/infrastructure/text/extra_fields.py
app/infrastructure/llm/openai_adapter.py
app/infrastructure/rag/milvus_store.py
```

Parâmetros de ingestão:

```text
chunkSize
chunkOverlap
batchSize
deduplicate
noSplit
noHeader
```

Metadados:

```text
extraFields
```

Os metadados são normalizados para converter strings numéricas e booleanas.

## Fluxo de busca híbrida

```text
SearchHybridRequest
  -> RagUseCase.search_hybrid
  -> OpenAiEmbeddingAdapter.embed_text
  -> MilvusRagVectorStore.search_hybrid
  -> dense search
  -> sparse/BM25 search
  -> fusão de resultados
```

Parâmetros principais:

```text
k
denseWeight
sparseWeight
useHybrid
relevanceBoost
candidateMultiplier
candidateTopK
denseEfSearch
sparseDropRatioSearch
fusionStrategy
rrfK
maxChunksPerDocument
```

Filtro obrigatório:

```text
agentId
```

Filtros opcionais:

```text
extraFields
```

Estratégias de fusão:

```text
rrf
weighted_score
```

## Fluxo de chat com RAG

```text
ChatLlmRagRequest
  -> RagUseCase.chat
  -> RagUseCase.search_hybrid
  -> contexto textual dos documentos
  -> ChatUseCase
  -> OpenAI ou Claude
```

O provider e o modelo continuam sendo escolhidos no payload:

```text
provider = openai | claude
model    = modelo desejado
```

## Configuração necessária

```text
OPENAI_API_KEY
OPENAI_EMBEDDING_MODEL
MILVUS_URI
MILVUS_TOKEN
MILVUS_USERNAME
MILVUS_PASSWORD
MILVUS_COLLECTION_NAME
MILVUS_EMBEDDING_DIM
ANTHROPIC_API_KEY
ANTHROPIC_DEFAULT_MODEL
```

## Validações

```powershell
py -3.13 -m compileall app
```

## Pontos de manutenção

- Para trocar Milvus, implemente outro adapter para `RagVectorStorePort`.
- Para trocar embeddings, implemente outro adapter para `EmbeddingPort`.
- Para ajustar qualidade de busca, altere defaults em `RagSearchOptions` e documente em `docs/sdd/api-contracts.md`.
- Preserve `agentId` como filtro obrigatório para isolamento entre agentes.
