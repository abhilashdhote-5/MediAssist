import os
import tempfile
from typing import List, Dict, Any, Optional
from utils.pdf_parser import extract_pdf_text

class AdvancedRAGPipeline:
    """
    Advanced RAG Pipeline for Medical PDF Lab Reports.
    Processes PDF documents using SentenceTransformers ('all-MiniLM-L6-v2')
    for vector embeddings and FAISS for fast similarity search.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._embedder = None
        self._vector_store = None
        self.raw_text = ""
        self.chunks = []
        self.filename = ""

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    def process_pdf_bytes(self, pdf_bytes: bytes, filename: str = "uploaded_report.pdf") -> Dict[str, Any]:
        """
        Extracts text from PDF bytes, splits into chunks, embeds using SentenceTransformers,
        and builds a FAISS vector store in memory.
        """
        self.filename = filename
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name

        try:
            self.raw_text = extract_pdf_text(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        if not self.raw_text or self.raw_text.startswith("[Error"):
            return {
                "status": "Error",
                "message": f"Failed to extract text from {filename}.",
                "num_chunks": 0
            }

        return self._build_vector_index()

    def process_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """
        Processes a PDF file directly from a local file path.
        """
        self.filename = os.path.basename(file_path)
        self.raw_text = extract_pdf_text(file_path)
        if not self.raw_text or self.raw_text.startswith("[Error"):
            return {
                "status": "Error",
                "message": f"Failed to read PDF file at {file_path}.",
                "num_chunks": 0
            }

        return self._build_vector_index()

    def _build_vector_index(self) -> Dict[str, Any]:
        """
        Splits text into chunks, generates embeddings, and creates FAISS index.
        """
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        self.chunks = text_splitter.split_text(self.raw_text)
        if not self.chunks:
            self.chunks = [self.raw_text]

        try:
            from langchain_community.vectorstores import FAISS
            embedder = self._get_embedder()
            
            from langchain_core.embeddings import Embeddings

            class STEmbeddingsWrapper(Embeddings):
                def __init__(self, st_model):
                    self.st_model = st_model
                def embed_documents(self, texts: List[str]) -> List[List[float]]:
                    embeddings = self.st_model.encode(texts, show_progress_bar=False)
                    return embeddings.tolist()
                def embed_query(self, text: str) -> List[float]:
                    embedding = self.st_model.encode([text], show_progress_bar=False)[0]
                    return embedding.tolist()
                def __call__(self, text: str) -> List[float]:
                    return self.embed_query(text)

            embeddings_func = STEmbeddingsWrapper(embedder)
            self._vector_store = FAISS.from_texts(self.chunks, embeddings_func)

        except Exception as e:
            print(f"Warning: FAISS index build fallback: {e}")
            self._vector_store = None

        return {
            "status": "Success",
            "filename": self.filename,
            "num_chunks": len(self.chunks),
            "char_count": len(self.raw_text),
            "raw_text": self.raw_text
        }

    def query(self, search_query: str, top_k: int = 4) -> str:
        """
        Retrieves top_k relevant document chunks for the search query.
        Returns concatenated text string of relevant contexts.
        """
        if not self.chunks:
            return ""

        if self._vector_store:
            try:
                docs = self._vector_store.similarity_search(search_query, k=top_k)
                return "\n---\n".join([doc.page_content for doc in docs])
            except Exception as e:
                print(f"Vector search fallback: {e}")

        # Fallback to returning all chunks or raw text if vector store is unavailable
        return "\n---\n".join(self.chunks[:top_k])
