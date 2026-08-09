# Understanding — What We Have Learned

This file records concepts that have actually been introduced and implemented in the project so far.

> Rule: only concepts introduced in code may be documented here. Unintroduced topics (agents, MCP, Redis, Docker, deployment) are excluded until their phase introduces them.

## Project Source of Truth

The actual source code and verified tests are the primary source of truth.

Documentation must reflect the actual implementation.

Future plans must never be treated as implemented features.

If documentation and code disagree:

1. Inspect the actual code.
2. Determine the real implementation.
3. Report the inconsistency.
4. Correct the documentation.

---

## Client vs Server

### What is it?

The client is anything that makes a request (browser, curl, Postman). The server is a program that listens for requests and returns responses.

### Why do we need it?

Separating the two lets many clients talk to one shared service over a network instead of each client owning its own data.

### How does it work?

The client sends an HTTP request to the server's address. The server processes it and sends back an HTTP response.

### How is it used in this project?

There is no frontend. The client is you — a browser, curl, or Postman hitting `http://127.0.0.1:8000`. The server is the FastAPI app served by Uvicorn.

### Important implementation details

Client and server talk only through HTTP — neither can call functions in the other's process.

### Common mistakes

Building UI before the API contract is stable; expecting the server to know client state.

### Interview questions

What does "client-server architecture" mean? Where does business logic live — client or server?

---

## HTTP

### What is it?

HTTP (HyperText Transfer Protocol) is the application-level protocol clients and servers use to communicate on the web.

### Why do we need it?

It gives a standard, language-agnostic way for any client and any server to exchange structured messages.

### How does it work?

A client opens a request with a method, a path, and optionally a body; the server replies with a status code and a body.

### How is it used in this project?

Uvicorn is an HTTP server that hands each incoming HTTP request to the FastAPI app and sends back the returned response.

### Important implementation details

HTTP is stateless: each request is independent; the server does not remember a client between requests.

### Common mistakes

Assuming the server keeps per-client state; ignoring that requests can arrive in any order.

### Interview questions

Is HTTP stateless? What layers sit below HTTP (TCP/IP)?

---

## File Upload

### What is it?

The process of transmitting binary or text file contents from a client to a server over HTTP.

### Why do we need it?

Documents (PDFs, DOCX files) are binary objects that cannot be sent via standard text JSON bodies without heavy encoding overhead.

### How does it work?

The client selects a local file and sends an HTTP POST request formatted with a multipart boundary payload containing the file bytes.

### How is it used in this project?

`POST /documents/upload` receives document files via `UploadFile = File(...)`.

### Important implementation details

FastAPI handles incoming byte streams asynchronously and exposes an `UploadFile` interface for reading contents into memory or saving to disk.

### Common mistakes

Attempting to pass raw binary files directly inside JSON request payloads.

### Interview questions

How does a file upload differ from a standard JSON API request?

---

## Multipart/Form-Data

### What is it?

An HTTP request encoding format (`multipart/form-data`) designed for transmitting binary files and form fields in boundary-delimited sections.

### Why do we need it?

It allows sending raw file bytes and associated metadata in a single, efficient HTTP payload.

### How does it work?

The HTTP header defines a unique `boundary` string. The body separates fields into sections delimited by this boundary string.

### How is it used in this project?

FastAPI uses `python-multipart` to parse `multipart/form-data` requests in `POST /documents/upload`.

### Important implementation details

Requires installing `python-multipart` in the Python virtual environment.

### Common mistakes

Forgetting to specify `multipart/form-data` in API testing clients like Postman or curl (`-F "file=@doc.pdf"`).

### Interview questions

What is `multipart/form-data` and how does HTTP boundary separation work?

---

## File Validation

### What is it?

Checking an uploaded file's properties (extension, size, non-emptiness, structural validity) before saving or processing it.

### Why do we need it?

Prevents saving malicious, unsupported, oversized, or corrupt files that could crash the application or waste storage.

### How does it work?

The upload endpoint checks the file extension (`.pdf`, `.docx`), reads byte size (rejecting 0 bytes or >10MB), and validates text extraction.

### How is it used in this project?

`POST /documents/upload` enforces allowed extensions (`ALLOWED_EXTENSIONS = {'.pdf', '.docx'}`), maximum size (10MB), and non-empty byte payloads.

### Important implementation details

Fails early with explicit HTTP error status codes (`400 Bad Request`, `413 Payload Too Large`, `415 Unsupported Media Type`).

### Common mistakes

Relying solely on client-side validation or trusting raw file extensions without server-side validation.

### Interview questions

What key validations should be performed on file uploads in web services?

---

## File Storage

### What is it?

Saving binary file payloads to a dedicated storage location outside the relational database.

### Why do we need it?

Storing raw binary BLOBs inside PostgreSQL bloats database size and degrades query performance. Saving files to disk keeps PostgreSQL clean and fast.

### How does it work?

File bytes are written to a project storage folder (`backend/storage/`) using unique filenames generated via UUIDs.

### How is it used in this project?

`upload_document` generates a unique UUID filename (e.g. `b1a2c3d4.pdf`) and saves the uploaded file in `backend/storage/`.

### Important implementation details

Original filenames are preserved in PostgreSQL metadata while storage paths use non-colliding UUID filenames.

### Common mistakes

Using original filenames directly for disk storage, leading to path collisions and security risks.

### Interview questions

Why store binary files on a disk/object store rather than directly inside a relational database table?

---

## File Metadata

### What is it?

Structured informational attributes describing a stored file (filename, storage path, file type, file size, creation timestamp, processing status).

### Why do we need it?

Allows searching, filtering, and managing uploaded documents efficiently in SQL queries without opening binary files.

### How does it work?

Stored as column attributes in the PostgreSQL `documents` table.

### How is it used in this project?

The `Document` SQLAlchemy model tracks `name`, `stored_file_path`, `file_type`, `file_size`, `created_at`, `processing_status`, and `extracted_text`.

### Important implementation details

Stored paths use relative references (`storage/<uuid>.<ext>`) to avoid leaking absolute server paths to clients.

### Common mistakes

Exposing internal filesystem directory structures (`C:\Users\...` or `/var/www/...`) in public API responses.

### Interview questions

What metadata fields are necessary for tracking user-uploaded documents?

---

## MIME Types & File Types

### What is it?

Standardized identifiers (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`) indicating file formats.

### Why do we need it?

Enables system components to determine the correct parser and text extractor for each document.

### How does it work?

Extracted from file extensions or header inspection and normalized to concise format strings (`pdf`, `docx`).

### How is it used in this project?

Normalizes extensions to `pdf` or `docx` and routes files to the appropriate extractor in `backend/extractor.py`.

### Important implementation details

The `file_type` string in PostgreSQL determines whether `pypdf` or `python-docx` handles text extraction.

### Common mistakes

Assuming all uploaded files match their declared extensions without verification.

### Interview questions

What is a MIME type? How do MIME types differ from file extension strings?

---

## PDF Text Extraction

### What is it?

Parsing PDF document internal page structures, fonts, and content streams to extract readable plain text.

### Why do we need it?

Unlocks textual content inside PDF documents so it can be stored, searched, and processed by downstream RAG pipelines.

### How does it work?

`pypdf.PdfReader` opens the PDF file, iterates over each page object, calls `extract_text()`, and concatenates page text.

### How is it used in this project?

`extractor.extract_text_from_pdf()` processes stored PDF files in `backend/extractor.py`.

### Important implementation details

Handles multi-page documents and skips empty/image-only pages without crashing.

### Common mistakes

Expecting raw text extraction from scanned image-only PDFs without OCR.

### Interview questions

How does PDF text extraction work under the hood? What are its limitations?

---

## DOCX Text Extraction

### What is it?

Parsing Microsoft Word (`.docx`) OpenXML zip packages to extract text from paragraph elements.

### Why do we need it?

Enables extracting structured text content from Word document files.

### How does it work?

`docx.Document` opens the `.docx` file, iterates through the document paragraphs (`doc.paragraphs`), and collects `paragraph.text`.

### How is it used in this project?

`extractor.extract_text_from_docx()` processes stored Word files in `backend/extractor.py`.

### Important implementation details

Strips whitespace and joins non-empty paragraph strings with double newlines.

### Common mistakes

Failing to handle corrupt zip archives or malformed XML structures inside DOCX files.

### Interview questions

What underlying file format is a `.docx` file? How does `python-docx` parse it?

---

## Processing States

### What is it?

Tracking the operational lifecycle state of an uploaded document using an explicit status indicator.

### Why do we need it?

Document processing involves multiple steps (upload, disk write, parsing, extraction). An explicit status makes progress observable.

### How does it work?

The database status transitions through defined enum states: `UPLOADED` → `PROCESSING` → `COMPLETED` (or `FAILED`).

### How is it used in this project?

`ProcessingStatus` Enum is declared in `schemas.py` and saved in the `documents` table's `processing_status` column.

### Important implementation details

If text extraction fails due to a corrupt file or error, the status is explicitly updated to `FAILED`.

### Common mistakes

Marking a document as `COMPLETED` before text extraction has finished or succeeded.

### Interview questions

Why should asynchronous or multi-step operations have explicit state tracking in database schemas?

---

## Error Handling During Processing

### What is it?

Catching failures during file upload, storage, or text extraction and recording errors without crashing the server.

### Why do we need it?

Ensures server stability, provides feedback to API clients, and marks invalid documents as `FAILED` in PostgreSQL.

### How does it work?

Upload validation uses `HTTPException`; text extraction is wrapped in `try...except` blocks that set `status = FAILED` upon error.

### How is it used in this project?

In `main.py`, file validation raises HTTP error codes (`400`, `413`, `415`), while extraction errors update `processing_status` to `FAILED`.

### Important implementation details

Log error details internally while returning clean, sanitized HTTP responses to clients.

### Common mistakes

Exposing raw Python tracebacks or sensitive server file paths in API error responses.

### Interview questions

How do you handle file processing failures in web APIs?

---

## Storage vs Metadata

### What is it?

The architectural separation between binary file content storage (disk/object store) and structured relational metadata (PostgreSQL).

### Why do we need it?

Combines high-performance file I/O for raw documents with fast indexing and relational query capabilities in SQL.

### How does it work?

Binary files live in `backend/storage/`; PostgreSQL stores `stored_file_path`, `name`, `file_size`, `processing_status`, and `extracted_text`.

### How is it used in this project?

`main.py` saves file bytes to disk and writes metadata records to PostgreSQL via `crud.py`.

### Important implementation details

Deleting a document record also cleans up its corresponding file from `backend/storage/`.

### Common mistakes

Deleting database records without removing orphaned binary files from disk storage.

### Interview questions

What are the benefits of decoupling binary storage from metadata databases?

---

## Synchronous Processing

### What is it?

Executing file upload, disk storage, and text extraction sequentially within the single HTTP request lifecycle.

### Why do we need it?

Keeps Phase 2 implementation simple, readable, and easy to test before introducing complex background workers or queues.

### How does it work?

The HTTP client waits while FastAPI saves the file, extracts text, updates PostgreSQL, and returns the response.

### How is it used in this project?

`POST /documents/upload` handles validation, storage, and text extraction synchronously in the route handler.

### Important implementation details

Appropriate for development and small files; future phases can offload heavy processing to background workers.

### Common mistakes

Over-engineering early learning phases with Celery/Redis before basic synchronous workflows are established.

### Interview questions

What are the trade-offs between synchronous and asynchronous background file processing?

---

## Text Chunking

### What is it?

The process of splitting a long extracted document text into smaller, overlapping segments called chunks.

### Why do we need it?

Embedding models have token limits (typically 512–8 192 tokens). A single embedding of a 50-page document loses granularity — a short user query cannot be meaningfully matched against a single averaged vector. Chunks let each part of the document be embedded and retrieved independently.

### How does it work?

The chunker uses a character-size target and searches backward near that target for a paragraph boundary, then a sentence boundary, then whitespace. The next chunk begins near the requested overlap at a word boundary.

### How is it used in this project?

`backend/chunker.py` exposes `chunk_text(text, chunk_size, chunk_overlap)`. `backend/ingestion.py` calls it after text extraction and before embedding.

### Important implementation details

Defaults are `CHUNK_SIZE=1000` characters and `CHUNK_OVERLAP=200` characters, stored in `config.py` and overridable via environment variables. They are starting values to evaluate, not universal optimal values.

### Common mistakes

Hardcoding chunk parameters inside the route handler; making chunks so large they exceed embedding model token limits; making chunks so small they carry no context.

### Interview questions

Why is chunking needed before embedding? What happens if chunks are too large or too small?

---

## Chunk Size

### What is it?

The maximum number of characters (or tokens) contained in a single chunk.

### Why do we need it?

Controls the granularity of retrieval: smaller chunks are more precise but carry less context; larger chunks carry more context but may dilute the embedding signal.

### How does it work?

In `chunker.py`, `chunk_size` is a target maximum window; the implementation prefers a natural boundary at or before that target.

### How is it used in this project?

Defaulted to `1000` characters, tunable via the `CHUNK_SIZE` environment variable.

### Important implementation details

Characters are not tokens. The 1,000-character baseline normally creates a compact passage for the default model, but tokenization and language affect the true input length.

### Common mistakes

Assuming characters == tokens; the actual token count depends on the tokeniser used by the embedding model.

### Interview questions

What factors influence the optimal chunk size for a RAG system?

---

## Chunk Overlap

### What is it?

The number of characters shared between adjacent chunks, preserving context at chunk boundaries.

### Why do we need it?

Without overlap, a sentence that falls exactly on a boundary is split across two chunks, degrading retrieval quality for queries covering that boundary.

### How does it work?

After choosing a natural end boundary, the next chunk starts near `chunk_overlap` characters before it, moving forward to a whitespace boundary so it does not start mid-word.

### How is it used in this project?

Defaulted to `200` characters, tunable via `CHUNK_OVERLAP` env variable.

### Important implementation details

Overlap must be strictly less than chunk_size; the project enforces this with a `ValueError` in `chunk_text()`.

### Common mistakes

Setting overlap equal to or larger than chunk_size, causing infinite loops or `ValueError`.

### Interview questions

What is the purpose of chunk overlap? How does overlap affect the total number of chunks?

---

## Embeddings

### What is it?

A dense, fixed-length numeric vector produced by an embedding model from a text input.

### Why do we need it?

Raw text cannot be compared mathematically. Embeddings map text into a geometric space where semantically similar phrases are close together, enabling vector similarity search.

### How does it work?

The configured embedding model (by default `all-MiniLM-L6-v2`) maps each chunk to a fixed-size numeric vector (384 dimensions for the default model).

### How is it used in this project?

`backend/embedding_service.py` loads the local sentence-transformer once per process and explicitly generates normalized embeddings before `vector_store.py` writes them to ChromaDB. The model is configured via `EMBEDDING_MODEL` in `config.py`.

### Important implementation details

Embeddings are generated in the embedding service, before vector replacement. `EMBEDDING_DIMENSIONS` validates that the loaded model matches the configured 384-dimensional collection expectation.

### Common mistakes

Using an LLM (GPT-4 etc.) as an embedding model — LLMs are generative, not bi-encoder retrievers; confusing embedding dimensions between different models.

### Interview questions

What is the difference between a generative LLM and an embedding model?

---

## Embedding Dimensions

### What is it?

The number of elements in an embedding vector — the size of the geometric space.

### Why do we need it?

The dimensionality must be consistent for all vectors stored in the same ChromaDB collection. Mixing models with different dimensions causes errors.

### How does it work?

`all-MiniLM-L6-v2` produces 384-dimensional vectors. ChromaDB stores the supplied vectors and indexes them with its configured cosine HNSW space.

### How is it used in this project?

The default model and `EMBEDDING_DIMENSIONS=384` are configured together. The embedding service rejects a mismatch before ChromaDB is changed.

### Important implementation details

Changing to a model with another dimension requires a fresh collection and a full re-index; existing vectors cannot be mixed with a new dimension.

### Common mistakes

Swapping embedding models mid-project without re-indexing existing vectors.

### Interview questions

Why does the number of embedding dimensions matter for a vector database?

---

## Semantic Similarity

### What is it?

A numerical measure of how similar two pieces of text are in meaning, computed as the cosine similarity between their embedding vectors.

### Why do we need it?

Enables retrieval of document chunks that are semantically related to a user query, even when no exact keyword match exists.

### How does it work?

Cosine similarity = dot product of two unit vectors; ranges from -1 (opposite) to 1 (identical). ChromaDB's HNSW index finds approximate nearest neighbours efficiently.

### How is it used in this project?

The ChromaDB collection is created with `metadata={"hnsw:space": "cosine"}` in `vector_store._get_collection()`.

### Important implementation details

Cosine similarity is angle-based and scale-invariant; it measures directional closeness, not magnitude.

### Common mistakes

Confusing cosine similarity with Euclidean distance; assuming a high similarity score means factual correctness.

### Interview questions

What is the difference between cosine similarity and Euclidean distance for vector search?

---

## Vector Database

### What is it?

A specialised database optimised for storing high-dimensional embedding vectors and executing approximate-nearest-neighbour (ANN) queries.

### Why do we need it?

Relational databases like PostgreSQL are not designed for high-dimensional vector operations. A vector database with an ANN index (HNSW, IVFFlat, etc.) queries millions of vectors in milliseconds.

### How does it work?

Vectors are indexed with HNSW or similar structures. A query vector is compared against the index to retrieve the K most similar stored vectors.

### How is it used in this project?

ChromaDB stores chunk embeddings. Phase 4 will query it with a question embedding to retrieve the most relevant chunks.

### Important implementation details

PostgreSQL stores *metadata*; ChromaDB stores *vectors*. They complement each other.

### Common mistakes

Attempting to store raw embedding arrays as PostgreSQL JSONB columns — this works at tiny scale but does not scale.

### Interview questions

What is ANN search? How does it differ from exact nearest-neighbour search?

---

## ChromaDB

### What is it?

An open-source, Python-native vector database that supports local persistent storage, built-in embedding functions, and metadata filtering.

### Why do we need it?

It requires zero server setup, integrates directly with sentence-transformers, and persists data to disk — ideal for development and learning phases.

### How does it work?

`chromadb.PersistentClient(path=...)` opens or creates a local database at the specified directory. Collections store vectors, documents, and metadata.

### How is it used in this project?

`backend/vector_store.py` initialises a persistent ChromaDB client pointing to `backend/chroma_data/`. It receives explicit vectors from `embedding_service.py` and stores them in the `document_chunks` collection.

### Important implementation details

Data persists across process restarts. The `PersistentClient` writes to `backend/chroma_data/` using SQLite-backed files.

### Common mistakes

Using `chromadb.Client()` (ephemeral, in-memory) instead of `PersistentClient` — data is lost on restart.

### Interview questions

What are the differences between ChromaDB's ephemeral and persistent clients?

---

## Vector Collections

### What is it?

A named namespace within ChromaDB for storing related vectors, analogous to a SQL table.

### Why do we need it?

Separating collections allows different types of data (document chunks, hypothetical question embeddings, etc.) to use different embedding models and index parameters.

### How does it work?

`client.get_or_create_collection(name=...)` returns an existing or freshly created collection. Each record has an `id`, `embedding`, `document`, and `metadata`.

### How is it used in this project?

One collection named `document_chunks` (configurable via `CHROMA_COLLECTION_NAME`) holds all chunk vectors for all documents.

### Important implementation details

All vectors in a collection must share the same embedding dimension.

### Common mistakes

Creating a new collection per document — this makes cross-document queries impossible.

### Interview questions

Why would you use multiple ChromaDB collections in the same application?

---

## Vector Metadata

### What is it?

Key-value attributes stored alongside each vector in ChromaDB, enabling metadata-based filtering during retrieval.

### Why do we need it?

Phase 4 retrieval needs to cite which document and which chunk a result came from. Metadata links vectors back to PostgreSQL records.

### How does it work?

Each upsert call includes a `metadatas=[{...}]` list. ChromaDB stores these and returns them alongside retrieved vectors.

### How is it used in this project?

Each chunk is stored with `{"document_id": int, "filename": str, "chunk_index": int}` metadata.

### Important implementation details

The PostgreSQL integer document ID is stored as an integer and the same type is used in ChromaDB metadata filters. The current extractors do not expose page-to-chunk data, so page numbers are not invented.

### Common mistakes

Storing integer metadata values and then filtering with a string (or vice versa) — ChromaDB where-filters are type-sensitive.

### Interview questions

How does metadata stored in a vector database differ from metadata stored in a relational database?

---

## Document Ingestion Pipeline

### What is it?

The end-to-end sequence of steps that transforms an uploaded raw file into searchable embedded vectors.

### Why do we need it?

Each step — extraction, chunking, embedding, vector storage — has distinct responsibilities. A pipeline makes the order and failure modes observable.

### How does it work?

```
Upload → Validate → Store file → PostgreSQL UPLOADED
       → Text extraction → Chunking → Embedding → ChromaDB upsert
       → PostgreSQL COMPLETED  (or FAILED on any error)
```

### How is it used in this project?

`POST /documents/upload` in `main.py` delegates the processing steps to `ingestion.index_document()`, keeping the API route separate from extraction, chunking, embedding, and vector storage.

### Important implementation details

Any exception in extraction, chunking, embedding, or vector storage sets `status = FAILED`; `COMPLETED` is set only after the complete vector replacement succeeds.

### Common mistakes

Marking a document `COMPLETED` before all ingestion steps succeed; embedding before chunking is done.

### Interview questions

What would happen if the vector ingestion step failed but the document was still marked COMPLETED?

---

## Re-indexing (Reprocessing)

### What is it?

The ability to re-run the chunking and embedding pipeline on a document without creating duplicate vectors.

### Why do we need it?

If a document is re-uploaded, or if the chunking strategy changes, previously stored vectors must be replaced rather than duplicated.

### How does it work?

New chunks are embedded first. Then `replace_document_chunks()` deletes every existing vector for the document and upserts the complete deterministic-ID set (`doc_{document_id}_chunk_{idx}`).

### How is it used in this project?

`vector_store.replace_document_chunks()` is used by ingestion, so a later internal reprocess run replaces the document's full vector set.

### Important implementation details

Embedding occurs before deletion, avoiding removal when embedding itself fails. Complete deletion before the upsert prevents stale higher-index chunks when the new run produces fewer chunks.

### Common mistakes

Using `collection.add()` or only overwriting matching IDs can leave duplicates or stale chunks. Reprocessing must replace the full set for the document.

### Interview questions

How would you implement zero-downtime re-indexing for a production RAG system?

---

## Vector Cleanup

### What is it?

Deleting all stored embeddings associated with a document when that document is removed from the system.

### Why do we need it?

Orphaned vectors consume storage and pollute retrieval results — queries may return chunks from documents that no longer exist in PostgreSQL.

### How does it work?

`vector_store.delete_document_chunks(document_id)` finds all IDs with matching integer `document_id` metadata and deletes them before file and PostgreSQL cleanup begins.

### How is it used in this project?

Called inside `DELETE /documents/{document_id}` in `main.py` before file and PostgreSQL deletion.

### Important implementation details

If ChromaDB cleanup fails, the endpoint returns `503` before changing PostgreSQL or the file. No distributed transaction spans ChromaDB, filesystem, and PostgreSQL; later-step failures are logged and reported, with vector restoration attempted when file deletion fails.

### Common mistakes

Deleting the PostgreSQL row first and then failing to clean ChromaDB — the document no longer exists, but its vectors still pollute search results.

---

## Retrieval-Augmented Generation (RAG)

### What is it?

RAG retrieves document evidence before an LLM generates an answer.

### Why do we need it?

The LLM does not otherwise know this project's uploaded PDF and DOCX content.

### How does it work?

The application embeds a question, retrieves similar chunks, builds context, then asks the LLM to answer from it.

### How is it used in this project?

`POST /query` calls `query_service.py` for retrieval, context construction, prompting, and generation.

### Important implementation details

The LLM is skipped if no chunk meets the relevance threshold.

### Common mistakes

Calling the LLM directly and presenting unsupported general knowledge as document content.

### Interview questions

How does RAG improve an answer over a direct LLM request?

---

## Retrieval

### What is it?

Retrieval selects the most relevant indexed chunks for a question.

### Why do we need it?

Only a small, relevant part of the document corpus should become LLM context.

### How does it work?

`retrieval_service.py` embeds the question, queries ChromaDB, and filters candidates by similarity.

### How is it used in this project?

It searches all currently indexed documents; the internal API accepts optional document IDs for future filtering.

### Important implementation details

It returns application-level chunk fields rather than the raw ChromaDB response.

### Common mistakes

Treating the nearest vector as relevant without a threshold.

### Interview questions

What distinguishes retrieval from generation in a RAG system?

---

## Query Embeddings

### What is it?

A query embedding is the numeric representation of a user's question.

### Why do we need it?

It makes a question comparable to the document chunk vectors.

### How does it work?

`embedding_service.embed_text()` reuses the cached sentence-transformer model.

### How is it used in this project?

Questions and chunks both use configurable `all-MiniLM-L6-v2` in the same 384-dimensional space.

### Important implementation details

Using a different embedding model would make distance comparisons unreliable.

### Common mistakes

Creating a separate query model or loading the model once for every request.

### Interview questions

Why must query and document embeddings share a vector space?

---

## Similarity Search

### What is it?

Similarity search finds stored vectors closest in meaning to the query vector.

### Why do we need it?

It can find related language even where exact keywords differ.

### How does it work?

The ChromaDB collection uses cosine space and returns cosine distance, where lower is closer.

### How is it used in this project?

The application converts distance to `similarity = 1 - distance` before relevance filtering.

### Important implementation details

Similarity is a retrieval signal, not proof that a chunk answers the question correctly.

### Common mistakes

Comparing distance directly to a threshold intended as similarity.

### Interview questions

How does cosine distance relate to cosine similarity here?

---

## Top-K

### What is it?

Top-K is the maximum number of nearest candidate chunks requested from the vector database.

### Why do we need it?

It bounds retrieval work and reduces unnecessary context.

### How does it work?

`TOP_K=4` is passed to ChromaDB before threshold filtering.

### How is it used in this project?

The environment variable is read from `config.py`, not hardcoded in the route.

### Important implementation details

Four is an initial baseline and may be tuned from retrieval evaluation.

### Common mistakes

Assuming top-K means all returned chunks are relevant.

### Interview questions

What trade-off changes when top-K is increased?

---

## Relevance Threshold

### What is it?

A threshold is the minimum similarity required before a retrieved chunk becomes evidence.

### Why do we need it?

Nearest unrelated chunks should not force an answer.

### How does it work?

Chunks must meet `SIMILARITY_THRESHOLD=0.35` after distance conversion.

### How is it used in this project?

Chunks below the threshold are excluded and an empty result skips LLM generation.

### Important implementation details

The default is a baseline for this model and corpus, not a universal semantic-quality value.

### Common mistakes

Setting a threshold without documenting whether it is a distance or similarity.

### Interview questions

Why can an overly low threshold increase hallucination risk?

---

## Context Construction

### What is it?

Context construction formats selected evidence into the text sent to the LLM.

### Why do we need it?

The LLM needs useful evidence and source labels, but not unlimited document text.

### How does it work?

`context_builder.py` adds highest-ranked labelled chunks until `MAX_CONTEXT_LENGTH=6000` would be exceeded.

### How is it used in this project?

Only chunks actually included in this context are returned as response sources.

### Important implementation details

Labels preserve filename, document ID, and chunk index for prompt references.

### Common mistakes

Returning sources that were retrieved but never passed to the LLM.

### Interview questions

Why should a RAG application limit context size?

---

## Prompt Construction

### What is it?

A RAG prompt combines grounding instructions, context, and the user question.

### Why do we need it?

It tells the LLM how to use retrieved evidence instead of treating it as optional.

### How does it work?

`prompt_builder.py` supplies concise system instructions and a source-labelled user prompt.

### How is it used in this project?

The prompt requires context-only answers, insufficiency acknowledgement, concise output, and source labels where useful.

### Important implementation details

The no-context branch is enforced in code rather than relying only on this prompt.

### Common mistakes

Using an ambiguous prompt that permits unsupported prior knowledge.

### Interview questions

What instruction makes a RAG prompt grounded?

---

## LLM Generation

### What is it?

LLM generation produces the natural-language answer from the RAG prompt.

### Why do we need it?

Retrieval returns evidence; generation turns it into a concise response to the user’s question.

### How does it work?

`llm_service.py` calls the configurable OpenAI Responses API using `LLM_MODEL`.

### How is it used in this project?

The default is `gpt-4.1-mini`; `OPENAI_API_KEY` is read only from environment configuration.

### Important implementation details

The service is a small provider boundary, so the RAG orchestration does not depend on OpenAI client details.

### Common mistakes

Hardcoding an API key or letting an LLM call happen before grounded retrieval.

### Interview questions

Why is an LLM service abstraction useful in a RAG application?

---

## Grounding and Hallucination

### What is it?

Grounding constrains an answer to evidence; hallucination is an unsupported or invented claim.

### Why do we need it?

Document intelligence should not pretend that unrelated documents answer a question.

### How does it work?

Threshold filtering, bounded retrieved context, prompt instructions, and the no-context branch work together.

### How is it used in this project?

The API returns a document-insufficiency answer and skips generation when evidence is absent.

### Important implementation details

Prompt instructions reduce risk but cannot guarantee factual accuracy; source review remains important.

### Common mistakes

Claiming a RAG system can never hallucinate.

### Interview questions

What is the difference between grounding and guaranteed truth?

---

## Source Citations

### What is it?

Sources identify the retrieved chunks used as answer evidence.

### Why do we need it?

They let a client display provenance and let users inspect supporting documents.

### How does it work?

`QuerySource` maps selected chunk metadata into `document_id`, `filename`, `chunk_index`, and similarity.

### How is it used in this project?

`POST /query` returns only context-included chunks; `page_number` is omitted when unavailable.

### Important implementation details

Raw embeddings and raw ChromaDB result structures are never sent to API clients.

### Common mistakes

Inventing page numbers or presenting all indexed documents as sources.

### Interview questions

Why are RAG citations metadata rather than model-generated claims?

---

## Retrieval Failure

### What is it?

Retrieval failure means question embedding or ChromaDB search could not complete; it differs from no relevant result.

### Why do we need it?

Users and clients need to distinguish unavailable infrastructure from absent document evidence.

### How does it work?

`RetrievalError` is translated to a safe `503 Service Unavailable` response.

### How is it used in this project?

No ChromaDB exception details, documents, or vectors are exposed in the response.

### Important implementation details

An empty collection is not a failure: it returns the normal grounded no-context response.

### Common mistakes

Treating an outage as proof that documents have no relevant content.

### Interview questions

Why should no-results and retrieval-errors use different responses?

---

## Generation Failure

### What is it?

Generation failure means the configured LLM cannot be called or returns no usable text.

### Why do we need it?

The application must not return a fabricated fallback answer after a provider failure.

### How does it work?

Missing/unsupported configuration returns `503`; provider failures return `502`.

### How is it used in this project?

`llm_service.py` logs the failure safely and `main.py` returns a generic API error.

### Important implementation details

The OpenAI key is never logged or placed in `.env.example` as a real value.

### Common mistakes

Returning provider exception text or silently substituting unrelated text.

### Interview questions

Why is a provider error different from an answer that says “not enough information”?
