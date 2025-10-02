from dataclasses import dataclass
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
import os
import dotenv
import numpy as np

# Intentar cargar variables de entorno desde el archivo .env
try:
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except:
    pass

class CustomEmbedding:
    """Wrapper para generar embeddings de 1024 dimensiones"""
    def __init__(self):
        self.base_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def embed_query(self, text: str):
        """Genera embedding de 1024 dimensiones"""
        base_embedding = self.base_model.embed_query(text)
        # Expandir de 384 a 1024 dimensiones usando padding y normalización
        expanded = np.pad(base_embedding, (0, 1024 - len(base_embedding)), 'constant')
        return expanded.tolist()
    
    def embed_documents(self, texts):
        """Genera embeddings de documentos de 1024 dimensiones"""
        base_embeddings = self.base_model.embed_documents(texts)
        expanded_embeddings = []
        for embedding in base_embeddings:
            expanded = np.pad(embedding, (0, 1024 - len(embedding)), 'constant')
            expanded_embeddings.append(expanded.tolist())
        return expanded_embeddings

@dataclass
class PineconeConfig:
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY") or "demo_pinecone_key"
    PINECONE_ENV: Optional[str] = os.getenv("PINECONE_ENV") or "us-east-1"
    API_KEY: Optional[str] = os.getenv("API_KEY") or "demo_key"
    GEMINI_MODEL: Optional[str] = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
    
    # Modelo personalizado compatible con 1024 dimensiones
    Modelo = CustomEmbedding()
 