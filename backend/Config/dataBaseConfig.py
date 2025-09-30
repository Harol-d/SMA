from dataclasses import dataclass
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
import os
import dotenv
import numpy as np

# Cargar variables de entorno desde el archivo .env
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

@dataclass
class PineconeConfig:
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV: Optional[str] = os.getenv("PINECONE_ENV")
    API_KEY: Optional[str] = os.getenv("API_KEY")
    GEMINI_MODEL: Optional[str] = os.getenv("GEMINI_MODEL")
    
    # Modelo HuggingFace (mantenido para compatibilidad)
    Modelo = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={
            'normalize_embeddings': True
        }
    )
 