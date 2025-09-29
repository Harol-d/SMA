from Models.LlmModel import ModeLlm
from Controllers.dataBaseVectorController import dataBaseVectorController
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Models.databaseVectorModel import databaseVectormodel

class lmmController:
    def __init__(self):
        self.model = ModeLlm()
        self.database = dataBaseVectorController()
        self.db_model = databaseVectormodel()  # Acceso directo al modelo de base de datos vectorial
    
    def promptValidate(self, data: dict):
        try:
            prompt = data.get("prompt")
            
            if prompt is None:
                raise ValueError("Error: No se ha proporcionado un prompt.")
            
            if not isinstance(prompt, str):
                raise TypeError("Error: El prompt debe ser un String.")
            
            if prompt.strip() == "":
                raise ValueError("Error: El prompt no puede estar vacío.")
            
            prompt = prompt.strip()
            
        except (ValueError, TypeError) as e:
            return str(e)
        
        # Usar búsqueda semántica directa para obtener contexto relevante
        try:
            # Realizar búsqueda semántica en los datos vectorizados
            search_result = self.db_model.search_similar_vectors(prompt, top_k=10)
            
            if search_result["success"] and search_result["results"]:
                # Construir contexto a partir de los resultados de búsqueda
                context_documents = []
                for result in search_result["results"]:
                    metadata = result.get('metadata', {})
                    text_content = metadata.get('text', '')
                    if text_content:
                        # Crear documento compatible con el formato esperado
                        doc = type('Document', (), {
                            'page_content': text_content,
                            'metadata': metadata
                        })()
                        context_documents.append(doc)
                
                print(f"Contexto encontrado: {len(context_documents)} documentos relevantes")
                print(f"Puntuacion de relevancia: {[r.get('score', 0) for r in search_result['results'][:3]]}")
                
                # Usar el contexto encontrado
                context = context_documents
            else:
                print("No se encontraron datos relevantes en la base vectorial")
                print("Sugerencia: Verificar que se haya cargado un archivo Excel")
                # Usar método legacy como fallback
                context = self.database.obtenerRecords(prompt)
                
        except Exception as e:
            print(f"Error en busqueda semantica: {str(e)}")
            print("Usando metodo legacy como fallback")
            # Fallback al método original
            context = self.database.obtenerRecords(prompt)
        
        response = self.model.sendPrompt(prompt, context)
        return response
            
