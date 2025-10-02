from dataclasses import dataclass
from typing import Optional
import os
import dotenv

# Intentar cargar .env, pero continuar si no existe
try:
    dotenv.load_dotenv("../../.env")
except:
    pass

@dataclass
class SettingsLlm:
    LLM_PROVEEDOR: Optional[str] = os.getenv("LLM_PROVEEDOR") or "gemini"
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL") or "gemini-1.5-flash"
    API_KEY: Optional[str] = os.getenv("API_KEY") or "demo_key"
    modelRole: str = f"""
                        Eres un Project Manager Senior. 
                        Analiza datos de avances de proyectos y entrega un resumen ejecutivo breve, máximo 2 viñetas o 100 palabras, solo con lo crítico o importante para la toma de decisiones.

                        Contexto: Datos de Excel con responsable, proyecto, actividades, % avance, notas de reuniones y estado de tareas.

                        Instrucciones:
                        - Identifica únicamente los 3 hallazgos más relevantes (atrasos, bloqueos o riesgos).
                        - Incluye una recomendación por hallazgo y un timeline sugerido.
                        - Usa lenguaje claro y de negocio, sin jerga técnica ni código.
                        - Responde solo a lo que aplique a la consulta.  
                        - Si no hay hallazgos críticos, responde en una sola frase.

                        Siempre responde con: análisis basado en evidencia, recomendaciones accionables y responsabilidades claras.
                        """
    max_tokens: int = 2500
    temperature: float = 0.2
