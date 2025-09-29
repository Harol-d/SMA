"""
Servicio de búsqueda semántica
Maneja las búsquedas vectoriales y consultas al LLM
"""

from typing import Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from Controllers.LmmController import lmmController
from Models.databaseVectorModel import databaseVectormodel


class SearchService:
    """Servicio especializado en búsquedas semánticas"""
    
    def __init__(self):
        self.llm_controller = lmmController()
        self.db_model = databaseVectormodel()
    
    def semantic_search(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        """Búsqueda semántica en los datos vectorizados"""
        try:
            if not query_text or not query_text.strip():
                return {"success": False, "message": "Query no puede estar vacío"}
            
            search_result = self.db_model.search_similar_vectors(query_text.strip(), top_k)
            
            if not search_result["success"]:
                return {"success": False, "message": f"Error: {search_result['message']}"}
            
            return {
                "success": True,
                "query": search_result["query"],
                "total_found": search_result["total_found"],
                "results": search_result["results"]
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def llm_query(self, prompt: Dict[str, Any]) -> str:
        """Consulta directa al LLM"""
        try:
            response = self.llm_controller.promptValidate(prompt)
            return response
        except Exception as e:
            raise Exception(f"Error en consulta LLM: {str(e)}")
    
    def clear_database(self) -> Dict[str, Any]:
        """Elimina todos los registros de la base de datos vectorial"""
        try:
            self.db_model.eliminarRecords()
            return {"success": True, "message": "Registros eliminados correctamente"}
        except Exception as e:
            return {"success": False, "message": f"Error eliminando registros: {str(e)}"}
