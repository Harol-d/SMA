from dataclasses import dataclass
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
import os
import dotenv

dotenv.load_dotenv("../../.env")
@dataclass
class PineconeConfig:
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY") 
    PINECONE_ENV: Optional[str] = os.getenv("PINECONE_ENV")
    API_KEY: Optional[str] = os.getenv("API_KEY") 
    EMBBEDING_MODEL: Optional[str] = os.getenv("EMBBEDING_MODEL","sentence-transformers/all-MiniLM-L6-v2")
    INDEX: Optional[str] = os.getenv("PINECONE_INDEX")
    model = HuggingFaceEmbeddings(
        model_name=EMBBEDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )