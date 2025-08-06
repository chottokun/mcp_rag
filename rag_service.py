# rag_service.py
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import os
import tempfile
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader

class RAGService:
    def __init__(
        self,
        db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        model_name: str = os.getenv("EMBED_MODEL", "cl-nagoya/ruri-v3-30m"),
    ):
        self.client = chromadb.PersistentClient(path=db_path)
        self.model = SentenceTransformer(model_name, device=os.getenv("DEVICE", "cpu"))
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
            length_function=len,
        )

    def add_document(self, content: bytes, filename: str, collection_name: str = "documents"):
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine distance
        )

        text = ""
        # Create a temporary file to use with langchain loaders
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            file_extension = Path(filename).suffix.lower()

            if file_extension == ".pdf":
                loader = PyPDFLoader(tmp_file_path)
                documents = loader.load()
                text = "\n".join([doc.page_content for doc in documents])
            elif file_extension == ".md":
                loader = UnstructuredMarkdownLoader(tmp_file_path)
                documents = loader.load()
                text = "\n".join([doc.page_content for doc in documents])
            else:
                # Default to decoding as plain text
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    text = ""  # Or raise an exception if preferred

            if text:
                chunks = self.text_splitter.split_text(text)
                ids, docs = [], []
                for i, chunk in enumerate(chunks):
                    pref = f"検索文書: {chunk}"
                    ids.append(f"{filename}_{i}")
                    docs.append(pref)

                if docs:
                    embeddings = self.model.encode(docs).tolist()
                    collection.add(
                        embeddings=embeddings,
                        documents=docs,
                        metadatas=[{"source": filename}] * len(docs),
                        ids=ids,
                    )
        finally:
            # Clean up the temporary file
            os.remove(tmp_file_path)

    def query_rag(self, query_text: str, n_results: int = 3, collection_name: str = "documents") -> Dict[str, Any]:
        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine distance
        )
        prefq = f"検索クエリ: {query_text}"
        emb = self.model.encode([prefq]).tolist()[0]
        res = collection.query(
            query_embeddings=[emb], n_results=n_results, include=["documents", "metadatas", "distances"]
        )

        if not res or not res.get("documents") or not res["documents"][0]:
            return {"query": query_text, "results": []}

        docs = [d.replace("検索文書: ", "") for d in res["documents"][0]]
        metas = res["metadatas"][0]
        distances = res["distances"][0]

        # Filter results based on a distance threshold.
        DISTANCE_THRESHOLD = 0.2

        results = []
        for doc, meta, dist in zip(docs, metas, distances):
            if dist < DISTANCE_THRESHOLD:
                results.append({"text": doc, "metadata": meta, "distance": dist})

        return {"query": query_text, "results": results}
