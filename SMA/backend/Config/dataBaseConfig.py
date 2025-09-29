from dataclasses import dataclass
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
import os
import dotenv
import google.generativeai as genai
import numpy as np

# Cargar variables de entorno desde el archivo .env
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

@dataclass
class PineconeConfig:
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV: Optional[str] = os.getenv("PINECONE_ENV")
    API_KEY: Optional[str] = os.getenv("API_KEY")
    GEMINI_MODEL: Optional[str] = os.getenv("GEMINI_MODEL", "text-embedding-004")
    
    def __post_init__(self):
        # Configurar Gemini para embeddings
        if self.API_KEY:
            genai.configure(api_key=self.API_KEY)
    
    # Modelo HuggingFace (mantenido para compatibilidad)
    Modelo = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={
            'normalize_embeddings': True
        }
    )
    
    def generate_gemini_embedding(self, text: str) -> list:
        """
        Genera embedding usando Gemini (1024 dimensiones)
        """
        try:
            result = genai.embed_content(
                model=self.GEMINI_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            embedding = result['embedding']
            # Borrar si es necesario, aun no lo veo asi.
            # Ajustar a 1024 dimensiones si es necesario
            if len(embedding) < 1024:
                # Rellenar con ceros si es menor
                embedding.extend([0.0] * (1024 - len(embedding)))
            elif len(embedding) > 1024:
                # Truncar si es mayor
                embedding = embedding[:1024]
            
            # Normalizar el vector (L2 normalization)
            embedding_array = np.array(embedding)
            normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
            
            return normalized_embedding.tolist()
        except Exception as e:
            raise Exception(f"Error generando embedding con Gemini: {str(e)}")
    
    # Código comentado para OpenAI (uso futuro)
    # def generate_openai_embedding(self, text: str) -> list:
    #     """
    #     Genera embedding usando OpenAI text-embedding-3-large (1024 dimensiones)
    #     """
    #     import openai
    #     try:
    #         openai.api_key = self.API_KEY
    #         response = openai.embeddings.create(
    #             model="text-embedding-3-large",
    #             input=text,
    #             dimensions=1024
    #         )
    #         embedding = response.data[0].embedding
    #         
    #         # Normalizar el vector (L2 normalization)
    #         embedding_array = np.array(embedding)
    #         normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
    #         
    #         return normalized_embedding.tolist()
    #     except Exception as e:
    #         raise Exception(f"Error generando embedding con OpenAI: {str(e)}")
    
    