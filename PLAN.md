# Obsidian Local-First RAG Plan

Generated: 2026-04-04

## 1. Goal

Build a local-first RAG system over Obsidian-style Markdown notes that:

- works directly against a vault stored in iCloud Drive
- automatically pulls relevant notes
- automatically finds related notes using semantic similarity and note graph links
- runs with a local small LLM
- starts with one command
- is optimized for context engineering, not only naive vector search

## 2. Recommended Architecture

Recommendation: **graph-assisted local RAG**, not pure vector RAG and not full entity-level GraphRAG in v1.

Reason:

- Obsidian already encodes an explicit knowledge graph through `[[wikilinks]]`, headings, block references, tags, and frontmatter.
- Full GraphRAG with entity extraction is heavier, slower, and less reliable for personal notes in early versions.
- The strongest v1 is: **semantic retrieval + lexical retrieval + explicit note graph expansion + context compiler**.

## 3. Target Request Pipeline

```text
client prompt
-> query normalizer
-> retrieval planner
-> parallel retrieval
   -> semantic search over note chunks
   -> lexical search over note text and titles
   -> graph expansion over wikilinks/backlinks/tags
   -> metadata filters (folder, tags, recency, note type)
-> candidate fusion and reranking
-> context compiler
-> local LLM synthesis
-> cited response
```

Recommended detailed flow:

```text
client prompt
-> prompt classifier
   -> question type
   -> target scope
   -> retrieval depth
-> query rewriting
   -> canonical search query
   -> synonym expansion
   -> graph seeds
-> retrieval planner
   -> choose dense/lexical/graph weights
-> retrieval fan-out
   -> vector search on chunks
   -> FTS/BM25 search on notes
   -> fetch directly linked notes
   -> fetch backlinks
   -> fetch tag/frontmatter neighbors
-> fusion
   -> weighted RRF or custom score merge
-> grouping and deduplication
   -> avoid 10 chunks from one note dominating
-> reranking
   -> note-level then chunk-level
-> context compiler
   -> assemble note summaries
   -> attach evidence snippets
   -> compress to token budget
   -> add provenance
-> local LLM
-> response with citations and suggested related notes
```

## 4. Recommended Stack

### Runtime

- `Python 3.12+`
- `FastAPI` for local API and streaming responses
- `uv` for dependency and run management
- `Makefile` with `make up` as the one-command entrypoint

### Local LLM layer

- `Ollama` for local model serving
- Generation model:
  - default: `qwen3:8b`
  - conservative fallback: `qwen2.5:7b`
  - lighter fallback: `gemma3:4b`
- Embedding model:
  - default: `embeddinggemma`
  - alternative: `nomic-embed-text`
- Reranker model:
  - default: `BAAI/bge-reranker-v2-m3`
  - heavier option: `BAAI/bge-reranker-large`

### Retrieval and indexing

- `Qdrant` in **local mode** for vector search
- `SQLite` for canonical metadata and note graph
- `LlamaIndex` for ingestion/indexing primitives, document parsing, and retrieval orchestration helpers

### File system and sync

- direct read from the Obsidian vault under iCloud Drive
- local index artifacts stored outside the vault in `.local/`
- file watcher for incremental reindex

## 5. Why This Stack

### Why Ollama

- local model serving
- OpenAI-compatible API surface
- supports chat, streaming, embeddings, and model-local context tuning

### Why Qdrant local mode

- persistent embedded local mode without a separate always-on server
- strong metadata filtering
- hybrid and multi-stage query support if needed later
- clean upgrade path to server mode if the project grows

### Why SQLite in addition to Qdrant

Qdrant should not be the canonical truth for your note graph.

Use SQLite for:

- notes table
- chunks table
- links table
- backlinks/materialized graph edges
- tags/frontmatter metadata
- FTS5 lexical search
- ingestion state, hashes, and sync checkpoints

Use Qdrant for:

- dense chunk vectors
- note-level summary vectors
- semantic candidate retrieval

### Why not pure LlamaIndex runtime

LlamaIndex is useful, but the runtime should stay explicit.

Recommendation:

- use LlamaIndex for ingestion pipeline and selected retrieval utilities
- keep the core retrieval planner, graph traversal, score fusion, and context compiler in your own code

That preserves maximum control for context engineering.

## 5.1 Reranking Layer

This should be treated as a **required stage in v1**, not a future optimization.

Reason:

- vector retrieval is optimized for recall, not final precision
- lexical retrieval catches exact terms but still returns noisy candidates
- graph expansion intentionally broadens the candidate set
- without reranking, too many mediocre chunks reach the context compiler

Recommended pattern:

```text
retrieval fan-out
-> candidate fusion
-> top 20-50 chunk candidates
-> cross-encoder reranker
-> top 3-8 chunks and top 2-5 notes
-> context compiler
```

Recommended local implementation:

- use `FlagEmbedding`
- default local reranker: `BAAI/bge-reranker-v2-m3`
- score pairs as `(query, chunk_text)`
- optionally rerank both:
  - chunk candidates
  - note summaries

Operational guidance:

- retrieve wide, rerank narrow
- candidate recall set: `20-50`
- final context set: usually `3-8` chunks across `2-5` notes
- on CPU-only machines keep rerank candidate count smaller

If latency becomes a problem, make reranking configurable, but keep it enabled by default.

## 6. Obsidian-Specific Design

Important inference: Obsidian's graph view is useful as a product concept, but for your system you should build your **own graph model** from Markdown and metadata instead of depending on any internal graph API.

Parse and store:

- note path
- note title
- YAML/frontmatter properties
- tags
- aliases
- headings
- block references
- outbound `[[wikilinks]]`
- embedded references
- backlinks as derived edges
- modification time
- folder path

Graph edge types:

- `links_to`
- `links_to_heading`
- `links_to_block`
- `shares_tag`
- `same_folder`
- `alias_of`
- `temporal_neighbor`

This matters because “related notes” in personal knowledge bases are often not just semantically similar. They are often:

- explicitly linked
- in the same project folder
- tagged together
- created around the same time
- connected through one bridging note

## 7. Data Model

### SQLite

Core tables:

- `notes`
  - `note_id`
  - `path`
  - `title`
  - `mtime`
  - `hash`
  - `frontmatter_json`
  - `summary`
- `chunks`
  - `chunk_id`
  - `note_id`
  - `heading_path`
  - `block_ref`
  - `chunk_text`
  - `token_count`
  - `chunk_order`
- `links`
  - `src_note_id`
  - `dst_note_id`
  - `edge_type`
  - `anchor`
- `tags`
  - `note_id`
  - `tag`
- `aliases`
  - `note_id`
  - `alias`
- `ingestion_state`
  - `path`
  - `hash`
  - `last_indexed_at`

Optional:

- `note_embeddings`
- `chunk_scores_cache`
- `sessions`
- `prompt_profiles`

### Qdrant payload

For each chunk, store payload like:

- `note_id`
- `path`
- `title`
- `heading_path`
- `chunk_order`
- `tags`
- `folder`
- `mtime`
- `note_type`

## 8. Retrieval Strategy

### Retrieval layers

1. Dense semantic retrieval
- semantic chunk similarity

2. Lexical retrieval
- title match
- exact term match
- acronym/project code match
- rare keyword match

3. Graph retrieval
- outbound linked notes
- backlinks
- 2-hop expansion with decay
- tag-neighbor notes

4. Metadata retrieval
- recency windows
- folder scoping
- note-class filtering

### Fusion

Use weighted fusion:

- semantic score
- lexical score
- graph proximity score
- recency prior
- title hit bonus

Start with simple weighted RRF or weighted normalized sum.

### Reranking

After fusion, apply a dedicated reranker before context assembly.

Recommended sequence:

1. semantic + lexical + graph retrieval
2. weighted fusion
3. group by `note_id`
4. rerank top fused candidates with cross-encoder reranker
5. keep final shortlist for context compiler

Why this order:

- fusion maximizes recall across different retrieval signals
- reranking restores precision before the LLM sees context

Suggested scoring model:

```text
final_retrieval_score
= fused_recall_score * alpha
+ reranker_score * beta
+ recency_prior * gamma
```

Use the reranker score as the dominant term in the final shortlist stage.

### Grouping

Group by `note_id` before final context assembly so one long note cannot monopolize the prompt.

## 9. Context Engineering Layer

This is the part that will matter most.

The system should not just dump top-k chunks into the model.

### Context compiler responsibilities

- deduplicate overlapping chunks
- promote note summaries before raw snippets
- preserve source hierarchy:
  - note
  - heading
  - block
- keep explicit citations
- cap per-note chunk count
- inject graph context separately from evidence snippets
- reserve token budget for answer generation

### Recommended compiled context shape

```text
SYSTEM PROFILE
USER QUERY
RETRIEVAL SUMMARY
TOP NOTES
  - note summary
  - why selected
  - key headings
EVIDENCE SNIPPETS
GRAPH CONTEXT
  - directly linked notes
  - backlinks
  - related tags
ANSWER INSTRUCTIONS
```

### Retrieval modes

Support at least 4 modes:

- `precise`: fewer chunks, more exactness
- `explore`: wider graph expansion
- `timeline`: recency-biased retrieval
- `synthesis`: note-summary-heavy retrieval for long-form answers

### Context budget policy

Recommended defaults:

- reserve 25-35% of the context window for generation
- reserve 10-15% for system and control instructions
- use the remainder for compiled evidence
- cap contribution from a single note unless the query explicitly targets that note

### Future context features

- personal writing style memory
- project-scoped personas
- query templates
- note importance priors
- conversation-aware retrieval
- scratchpad note injection

## 10. iCloud and Local-First Constraints

Use the vault directory directly from iCloud Drive, but treat iCloud as a sync transport, not as a database.

Design rules:

- never store index artifacts inside the vault
- keep indexes in `.local/`
- debounce file watcher events
- hash file contents to avoid duplicate indexing
- handle temporary sync conflicts and partial availability
- maintain a repair command: `make reindex`

Important operational risk:

- iCloud may surface files before sync is fully stable
- iCloud may evict older notes from local disk, making some files temporarily unavailable
- therefore ingestion should be idempotent and resilient to transient read failures

Additional safeguards:

- classify file access failures as retryable first
- keep last known metadata for temporarily unavailable files
- avoid deleting index entries immediately on a single missing-file event
- add a reconciliation pass for stale iCloud states

## 11. One-Command UX

Target command:

```bash
make up
```

What `make up` should do:

1. validate vault path
2. validate Ollama availability
3. pull required models if missing
4. create local directories
5. run initial indexing if needed
6. start API server
7. optionally start a small local web UI or TUI

Other commands:

- `make reindex`
- `make test`
- `make dev`
- `make models`
- `make doctor`

## 12. Suggested Repository Layout

```text
app/
  api/
  core/
  ingest/
  retrieve/
  synth/
  prompts/
  storage/
  ui/
tests/
  unit/
  integration/
  e2e/
config/
.local/
Makefile
pyproject.toml
```

Suggested modules:

- `app/core/config.py`
- `app/ingest/parser.py`
- `app/ingest/graph_builder.py`
- `app/ingest/indexer.py`
- `app/storage/sqlite_store.py`
- `app/storage/qdrant_store.py`
- `app/retrieve/planner.py`
- `app/retrieve/hybrid.py`
- `app/retrieve/graph_expand.py`
- `app/retrieve/fusion.py`
- `app/synth/context_compiler.py`
- `app/synth/respond.py`
- `app/api/main.py`

## 13. Testing Plan

Required:

### Unit tests

- markdown parsing
- wikilink resolution
- heading/block extraction
- graph edge generation
- chunking
- score fusion
- context compilation

### Integration tests

- vault ingestion end-to-end
- reindex after note edit
- hybrid retrieval over fixture vault
- graph expansion correctness
- reranker shortlist quality
- citation generation

### E2E tests

- ask a question, receive cited answer
- edit a note, re-ask, confirm updated answer
- request related notes, confirm graph-assisted results

Coverage target:

- `80%+`

## 13.1 Evaluation Metrics

Tests alone are not enough. The system needs an explicit RAG evaluation loop.

Recommendation:

- add `Ragas` as the evaluation framework

Track at least:

- `faithfulness`
- `answer_correctness`
- `context_precision`
- `context_recall`

What to evaluate:

- baseline retrieval without reranking
- retrieval with reranking
- different chunk sizes
- different overlap values
- semantic vs heading-aware chunking
- different retrieval mode presets

Evaluation dataset design:

- curate a small gold dataset from your own vault
- each sample should include:
  - query
  - expected source notes
  - expected answer or answer rubric
  - allowed related notes

Use this eval set to compare architecture choices before locking defaults.

## 14. Phased Implementation Plan

### Phase 0. Bootstrap

- initialize Python project with `uv`
- add FastAPI, SQLite layer, Qdrant client, Ollama client, LlamaIndex
- add Makefile and config
- define local directory layout

Exit criteria:

- `make up` starts a health-checked local service

### Phase 1. Ingestion

- read vault path from config
- parse markdown files
- extract frontmatter, tags, headings, wikilinks
- split into chunks with overlap
- prefer heading-aware and paragraph-aware chunking for Markdown
- evaluate semantic chunking as an optional mode
- store notes/chunks/links in SQLite
- compute embeddings and store in Qdrant

Exit criteria:

- full vault indexed locally
- incremental indexing works

Chunking defaults for first implementation:

- start with heading-aware chunking
- target chunk size: `600-1000` tokens
- overlap: `10-15%`
- preserve heading path in metadata

Fallback rule:

- if a section is too large, split by paragraph and then by sentence

### Phase 2. Retrieval Core

- implement semantic retrieval
- implement FTS/BM25 retrieval
- implement graph expansion
- implement candidate fusion and grouping
- implement reranking over fused candidates

Exit criteria:

- query returns ranked notes and chunks with explanations
- reranker improves precision on the eval set

### Phase 3. Context Compiler and Answering

- implement context budgets
- compile structured context
- call Ollama for answer synthesis
- return citations and related notes

Exit criteria:

- end-to-end QA works with provenance
- answer faithfulness reaches target threshold on the eval set

### Phase 4. UX

- add local web UI or terminal UI
- add retrieval mode selector
- add “why this note?” inspection
- add vault status and indexing dashboard

Exit criteria:

- comfortable daily use

### Phase 5. Advanced Context Engineering

- conversation memory
- query intent routing
- note-level summarization cache
- project-specific prompt profiles
- long-context compression
- note importance priors

Exit criteria:

- noticeably better answers on multi-note synthesis tasks

### Phase 6. Optional v2 Extensions

- entity extraction layer
- true GraphRAG over entities and relations
- spaced-repetition or resurfacing workflows
- local agent workflows over notes

## 15. Final Recommendation

If the goal is to build the strongest practical system fastest, start here:

- **Python + FastAPI**
- **Ollama**
- **SQLite for canonical note graph and FTS**
- **Qdrant local mode for vectors**
- **LlamaIndex for ingestion helpers, not as the full runtime abstraction**
- **graph-assisted hybrid retrieval**

That gives the best balance of:

- local-first operation
- iCloud compatibility
- one-command startup
- controllable architecture
- maximum room for context engineering

## 16. Key Sources

- LlamaIndex docs on markdown parsing, ingestion pipelines, and Ollama integration:
  - https://developers.llamaindex.ai/python/
  - https://context7.com/run-llama/llama_index
- FlagEmbedding docs on local reranking:
  - https://context7.com/flagopen/flagembedding
- Ragas docs on RAG evaluation:
  - https://context7.com/vibrantlabsai/ragas
- Ollama docs on OpenAI compatibility and embeddings:
  - https://docs.ollama.com/api/openai-compatibility
  - https://docs.ollama.com/api/embed
- Qdrant docs on local mode, filtering, and hybrid queries:
  - https://github.com/qdrant/qdrant-client
  - https://qdrant.tech/documentation/concepts/filtering
  - https://qdrant.tech/documentation/concepts/hybrid-queries
- Obsidian docs on internal links and properties:
  - https://help.obsidian.md/links
  - https://help.obsidian.md/properties
