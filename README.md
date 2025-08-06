# RAG Service with FastAPI and ChromaDB

This repository provides a working implementation of a Retrieval-Augmented Generation (RAG) service, exposed as an MCP (Machine-Callable Pool) server using FastAPI. It handles document ingestion, embedding generation with `cl-nagoya/ruri-v3-30m`, storage and retrieval with ChromaDB, and querying via a simple API.

## Features

- **Multi-Collection Support**: Store documents in separate, named collections within ChromaDB.
- **File Ingestion**: Upload and process various file types, including:
    - Plain Text (`.txt`)
    - Markdown (`.md`)
    - PDF (`.pdf`)
- **Advanced Search**: Performs similarity search using cosine distance and returns relevant chunks with their distance scores.
- **MCP-Enabled API**: Exposes endpoints that can be discovered and used by AI agents via `fastapi-mcp`.
- **Healthcheck**: A `/healthcheck` endpoint to monitor service status.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create a virtual environment and install dependencies:**
    This project uses `uv` for fast environment management, but `venv` and `pip` work perfectly fine.
    ```bash
    # Using uv
    uv venv
    uv pip install -r requirements.txt

    # Or using venv/pip
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## How to Run

1.  **Start the FastAPI server:**
    ```bash
    python main.py
    ```
    The server will be running at `http://127.0.0.1:8000`.

2.  **Access the API Documentation:**
    - **Swagger UI**: `http://127.0.0.1:8000/docs`
    - **MCP Endpoint**: `http://127.0.0.1:8000/mcp`


## API Endpoints

### 1. Ingest a Document

- **URL**: `/ingest/`
- **Method**: `POST`
- **Description**: Uploads a file for ingestion into a specified collection.
- **Query Parameters**:
    - `collection_name` (optional, string): The name of the collection to add the document to. Defaults to `"documents"`.
- **Body**: `multipart/form-data` with a `file` field containing the document.
- **Example (`curl`)**:
    ```bash
    curl -X POST "http://127.0.0.1:8000/ingest/?collection_name=my_collection" \
         -H "Authorization: Bearer dummytoken" \
         -F "file=@/path/to/your/document.pdf"
    ```

### 2. Query for Similar Documents

- **URL**: `/query/`
- **Method**: `GET`
- **Description**: Searches for documents in a collection that are similar to the query text.
- **Query Parameters**:
    - `query` (required, string): The text to search for.
    - `collection_name` (optional, string): The collection to search within. Defaults to `"documents"`.
- **Example (`curl`)**:
    ```bash
    curl -X GET "http://127.0.0.1:8000/query/?query=what%20is%20fastapi&collection_name=my_collection"
    ```

### 3. Health Check

- **URL**: `/healthcheck`
- **Method**: `GET`
- **Description**: Checks if the service is running.
- **Example (`curl`)**:
    ```bash
    curl -X GET http://127.0.0.1:8000/healthcheck
    ```
