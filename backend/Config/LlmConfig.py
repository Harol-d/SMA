from dataclasses import dataclass
from typing import Optional
import os
import dotenv

# dotenv.load_dotenv("../.env")
dotenv.load_dotenv("../../.env")

@dataclass
class SettingsLlm:
    LLM_PROVEEDOR: Optional[str] = os.getenv("LLM_PROVEEDOR")
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL")
    API_KEY: Optional[str] = os.getenv("API_KEY") 
    max_tokens: int = 5000
    temperature: float = 0.2
