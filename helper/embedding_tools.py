"""
Embedding and Vector Store Tools Module
Handles document embeddings, vector storage, and similarity search.
"""

import os
import uuid
from typing import List, Dict, Optional, Tuple
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings


class EmbeddingConfig:
    """Configuration for embedding models"""
    
    # Default embedding models
    DOCUMENT_EMBEDDING_MODEL = "google/embeddinggemma-300m"
    YOUTUBE_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Vector store settings
    DEFAULT_SIMILARITY_K = 3
    MAX_SIMILARITY_K = 10
    
    @staticmethod
    def validate_hf_token(hf_token: str) -> bool:
        """Validate HuggingFace token exists"""
        return hf_token is not None and len(hf_token) > 0
    
    @staticmethod
    def get_hf_token() -> Optional[str]:
        """Get HuggingFace token from environment"""
        return os.environ.get('HF_TOKEN')


class VectorStoreManager:
    """Manage vector stores for documents and YouTube transcripts"""
    
    def __init__(self, upload_folder: str):
        """
        Initialize vector store manager.
        
        Args:
            upload_folder: Base folder for storing vector stores
        """
        self.upload_folder = upload_folder
    
    def create_embeddings(self, model: str, hf_token: str) -> HuggingFaceEndpointEmbeddings:
        """
        Create HuggingFace embedding instance.
        
        Args:
            model: Model identifier (e.g., "google/embeddinggemma-300m")
            hf_token: HuggingFace API token
            
        Returns:
            HuggingFaceEndpointEmbeddings instance
        """
        return HuggingFaceEndpointEmbeddings(
            model=model,
            huggingfacehub_api_token=hf_token
        )
    
    def create_vector_store(
        self,
        documents: List,
        model: str,
        hf_token: str
    ) -> FAISS:
        """
        Create FAISS vector store from documents.
        
        Args:
            documents: List of LangChain documents
            model: Embedding model identifier
            hf_token: HuggingFace API token
            
        Returns:
            FAISS vector store instance
        """
        embeddings = self.create_embeddings(model, hf_token)
        return FAISS.from_documents(documents, embeddings)
    
    def save_vector_store(
        self,
        vector_store: FAISS,
        session_id: str,
        prefix: str = 'vector_store'
    ) -> str:
        """
        Save vector store to disk.
        
        Args:
            vector_store: FAISS vector store to save
            session_id: Unique session identifier
            prefix: Folder name prefix
            
        Returns:
            Path to saved vector store
        """
        vector_store_path = os.path.join(
            self.upload_folder,
            f'{prefix}_{session_id}'
        )
        os.makedirs(vector_store_path, exist_ok=True)
        vector_store.save_local(vector_store_path)
        return vector_store_path
    
    def load_vector_store(
        self,
        vector_store_path: str,
        model: str,
        hf_token: str
    ) -> FAISS:
        """
        Load vector store from disk.
        
        Args:
            vector_store_path: Path to saved vector store
            model: Embedding model identifier
            hf_token: HuggingFace API token
            
        Returns:
            Loaded FAISS vector store
        """
        embeddings = self.create_embeddings(model, hf_token)
        return FAISS.load_local(
            vector_store_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    
    def generate_session_id(self) -> str:
        """Generate unique session ID for vector store"""
        return str(uuid.uuid4())


class SimilaritySearcher:
    """Perform similarity searches on vector stores"""
    
    @staticmethod
    def search_with_scores(
        vector_store: FAISS,
        query: str,
        k: int = EmbeddingConfig.DEFAULT_SIMILARITY_K
    ) -> List[Tuple]:
        """
        Search for similar documents with scores.
        
        Args:
            vector_store: FAISS vector store
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        k = min(k, EmbeddingConfig.MAX_SIMILARITY_K)
        return vector_store.similarity_search_with_score(query, k=k)
    
    @staticmethod
    def search(
        vector_store: FAISS,
        query: str,
        k: int = EmbeddingConfig.DEFAULT_SIMILARITY_K
    ) -> List:
        """
        Search for similar documents without scores.
        
        Args:
            vector_store: FAISS vector store
            query: Search query
            k: Number of results to return
            
        Returns:
            List of documents
        """
        k = min(k, EmbeddingConfig.MAX_SIMILARITY_K)
        return vector_store.similarity_search(query, k=k)
    
    @staticmethod
    def extract_context(documents: List) -> str:
        """
        Extract and combine text from documents.
        
        Args:
            documents: List of LangChain documents
            
        Returns:
            Combined text content
        """
        return "\n\n".join([doc.page_content for doc in documents])
    
    @staticmethod
    def extract_context_with_metadata(documents: List) -> List[Dict]:
        """
        Extract text and metadata from documents.
        
        Args:
            documents: List of LangChain documents
            
        Returns:
            List of dicts with 'content' and 'metadata'
        """
        return [
            {
                'content': doc.page_content,
                'metadata': doc.metadata
            }
            for doc in documents
        ]


class DocumentVectorStore:
    """High-level interface for document vector operations"""
    
    def __init__(self, upload_folder: str):
        """
        Initialize document vector store.
        
        Args:
            upload_folder: Base folder for storing vector stores
        """
        self.manager = VectorStoreManager(upload_folder)
        self.searcher = SimilaritySearcher()
    
    def create_and_save_document_store(
        self,
        documents: List,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Create and save vector store for documents.
        
        Args:
            documents: List of LangChain documents
            session_id: Optional session ID (generates if not provided)
            
        Returns:
            Dict with 'vector_store_path' and 'session_id'
        """
        hf_token = EmbeddingConfig.get_hf_token()
        if not EmbeddingConfig.validate_hf_token(hf_token):
            raise ValueError("HuggingFace token not found in environment")
        
        if not session_id:
            session_id = self.manager.generate_session_id()
        
        # Create vector store
        vector_store = self.manager.create_vector_store(
            documents,
            EmbeddingConfig.DOCUMENT_EMBEDDING_MODEL,
            hf_token
        )
        
        # Save to disk
        vector_store_path = self.manager.save_vector_store(
            vector_store,
            session_id,
            prefix='doc_vector_store'
        )
        
        return {
            'vector_store_path': vector_store_path,
            'session_id': session_id
        }
    
    def create_and_save_youtube_store(
        self,
        documents: List,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Create and save vector store for YouTube transcripts.
        
        Args:
            documents: List of LangChain documents
            session_id: Optional session ID (generates if not provided)
            
        Returns:
            Dict with 'vector_store_path' and 'session_id'
        """
        hf_token = EmbeddingConfig.get_hf_token()
        if not EmbeddingConfig.validate_hf_token(hf_token):
            raise ValueError("HuggingFace token not found in environment")
        
        if not session_id:
            session_id = self.manager.generate_session_id()
        
        # Create vector store
        vector_store = self.manager.create_vector_store(
            documents,
            EmbeddingConfig.YOUTUBE_EMBEDDING_MODEL,
            hf_token
        )
        
        # Save to disk
        vector_store_path = self.manager.save_vector_store(
            vector_store,
            session_id,
            prefix='youtube_vector_store'
        )
        
        return {
            'vector_store_path': vector_store_path,
            'session_id': session_id
        }
    
    def search_document_store(
        self,
        vector_store_path: str,
        query: str,
        k: int = EmbeddingConfig.DEFAULT_SIMILARITY_K,
        return_scores: bool = False
    ) -> Dict:
        """
        Search document vector store.
        
        Args:
            vector_store_path: Path to saved vector store
            query: Search query
            k: Number of results
            return_scores: Whether to return similarity scores
            
        Returns:
            Dict with 'documents' (and optionally 'scores'), 'context'
        """
        hf_token = EmbeddingConfig.get_hf_token()
        if not EmbeddingConfig.validate_hf_token(hf_token):
            raise ValueError("HuggingFace token not found in environment")
        
        # Load vector store
        vector_store = self.manager.load_vector_store(
            vector_store_path,
            EmbeddingConfig.DOCUMENT_EMBEDDING_MODEL,
            hf_token
        )
        
        # Search
        if return_scores:
            results = self.searcher.search_with_scores(vector_store, query, k)
            documents = [doc for doc, score in results]
            scores = [score for doc, score in results]
            context = self.searcher.extract_context(documents)
            
            return {
                'documents': documents,
                'scores': scores,
                'context': context
            }
        else:
            documents = self.searcher.search(vector_store, query, k)
            context = self.searcher.extract_context(documents)
            
            return {
                'documents': documents,
                'context': context
            }
    
    def search_youtube_store(
        self,
        vector_store_path: str,
        query: str,
        k: int = EmbeddingConfig.DEFAULT_SIMILARITY_K,
        return_scores: bool = False
    ) -> Dict:
        """
        Search YouTube transcript vector store.
        
        Args:
            vector_store_path: Path to saved vector store
            query: Search query
            k: Number of results
            return_scores: Whether to return similarity scores
            
        Returns:
            Dict with 'documents' (and optionally 'scores'), 'context'
        """
        hf_token = EmbeddingConfig.get_hf_token()
        if not EmbeddingConfig.validate_hf_token(hf_token):
            raise ValueError("HuggingFace token not found in environment")
        
        # Load vector store
        vector_store = self.manager.load_vector_store(
            vector_store_path,
            EmbeddingConfig.YOUTUBE_EMBEDDING_MODEL,
            hf_token
        )
        
        # Search
        if return_scores:
            results = self.searcher.search_with_scores(vector_store, query, k)
            documents = [doc for doc, score in results]
            scores = [score for doc, score in results]
            context = self.searcher.extract_context(documents)
            
            return {
                'documents': documents,
                'scores': scores,
                'context': context
            }
        else:
            documents = self.searcher.search(vector_store, query, k)
            context = self.searcher.extract_context(documents)
            
            return {
                'documents': documents,
                'context': context
            }
