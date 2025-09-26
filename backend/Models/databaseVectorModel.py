from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore 
from Config.dataBaseConfig import PineconeConfig
import uuid
from typing import List, Dict, Any
import warnings

# Suprimir advertencias de pydantic durante la transición
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_pinecone")

class databaseVectormodel (PineconeConfig):
    def __init__(self):
        super().__init__()  # Configurar Gemini API
        # Inicializar Pinecone con la nueva API
        self.pinecone = Pinecone(api_key=self.PINECONE_API_KEY)
        self.record = "smaccb-pruebas1024"

    def agregarRecords(self, chunks: str):
        # Convertir chunks a formato de vectores para usar Gemini
        vectors_data = []
        for i, chunk in enumerate(chunks):
            vectors_data.append({
                'id': f"chunk_{i}_{uuid.uuid4().hex[:8]}",
                'text': chunk.page_content,
                'metadata': chunk.metadata
            })
        
        # Usar el método que ya maneja Gemini correctamente
        return self.upsert_vectors(vectors_data)
    
    def eliminarRecords(self):
        index = self.pinecone.Index(self.record)
        index.delete(delete_all=True)
    
    def consultarRecords(self, pregunta: str):
        # Usar búsqueda semántica con Gemini
        search_result = self.search_similar_vectors(pregunta, 20)
        if search_result["success"]:
            # Convertir formato para compatibilidad
            context = []
            for result in search_result["results"]:
                context.append(type('Document', (), {
                    'page_content': result['metadata'].get('text', ''),
                    'metadata': result['metadata']
                })())
            return context
        else:
            return []
    
    def upsert_vectors(self, vectors_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Inserta o actualiza vectores en Pinecone usando embeddings de Gemini
        
        Args:
            vectors_data: Lista de diccionarios con 'text', 'metadata' y 'id' (opcional)
        
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            index = self.pinecone.Index(self.record)
            
            # Preparar vectores para upsert
            vectors_to_upsert = []
            
            for i, data in enumerate(vectors_data):
                # Generar ID único si no se proporciona
                vector_id = data.get('id', str(uuid.uuid4()))
                
                # Generar embedding usando Gemini
                embedding = self.generate_gemini_embedding(data['text'])
                
                # Preparar metadata
                metadata = data.get('metadata', {})
                metadata['text'] = data['text']  # Incluir texto original en metadata
                
                vectors_to_upsert.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                })
            
            # Realizar upsert en lotes para mejor rendimiento
            batch_size = 100
            results = []
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                result = index.upsert(vectors=batch)
                results.append(result)
            
            return {
                "success": True,
                "message": f"Se procesaron {len(vectors_to_upsert)} vectores exitosamente",
                "vectors_count": len(vectors_to_upsert),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error en upsert de vectores: {str(e)}",
                "error": str(e)
            }
    
    def search_similar_vectors(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Busca vectores similares usando texto de consulta
        
        Args:
            query_text: Texto de consulta para búsqueda semántica
            top_k: Número de resultados a retornar
        
        Returns:
            Diccionario con resultados de búsqueda
        """
        try:
            index = self.pinecone.Index(self.record)
            
            # Generar embedding de la consulta
            query_embedding = self.generate_gemini_embedding(query_text)
            
            # Realizar búsqueda
            search_results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Formatear resultados
            formatted_results = []
            for match in search_results['matches']:
                formatted_results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match['metadata']
                })
            
            return {
                "success": True,
                "query": query_text,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error en búsqueda semántica: {str(e)}",
                "error": str(e)
            }
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas consolidadas para el dashboard
        
        Returns:
            Diccionario con métricas del dashboard
        """
        try:
            index = self.pinecone.Index(self.record)
            
            # Obtener estadísticas del índice
            stats = index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            # Obtener una muestra de vectores para análisis
            sample_size = min(100, total_vectors)  # Limitar muestra para eficiencia
            
            # Solo hacer query si hay vectores
            if sample_size > 0:
                sample_results = index.query(
                    vector=[0.0] * 1024,  # Vector dummy para obtener muestra (Gemini usa 1024 dimensiones)
                    top_k=sample_size,
                    include_metadata=True
                )
            else:
                sample_results = {'matches': []}
            
            # Analizar metadata de los vectores
            projects_data = []
            for match in sample_results['matches']:
                metadata = match.get('metadata', {})
                if metadata:
                    projects_data.append(metadata)
            
            # Calcular métricas básicas
            metrics = self._calculate_project_metrics(projects_data)
            
            return {
                "success": True,
                "total_vectors": total_vectors,
                "sample_analyzed": len(projects_data),
                "metrics": metrics
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error obteniendo métricas del dashboard: {str(e)}",
                "error": str(e)
            }
    
    def _calculate_project_metrics(self, projects_data: List[Dict]) -> Dict[str, Any]:
        """
        Calcula métricas específicas de proyectos
        
        Args:
            projects_data: Lista de metadata de proyectos
        
        Returns:
            Diccionario con métricas calculadas
        """
        if not projects_data:
            return {
                "total_projects": 0,
                "projects_on_track": 0,
                "projects_delayed": 0,
                "average_progress": 0,
                "risk_projects": 0,
                "completion_rate": 0
            }
        
        total_projects = len(projects_data)
        projects_on_track = 0
        projects_delayed = 0
        risk_projects = 0
        progress_values = []
        
        for project in projects_data:
            # Analizar progreso (buscar campos comunes de progreso)
            progress = self._extract_progress_value(project)
            if progress is not None:
                progress_values.append(progress)
            
            # Clasificar estado del proyecto
            status = self._classify_project_status(project)
            if status == "on_track":
                projects_on_track += 1
            elif status == "delayed":
                projects_delayed += 1
            elif status == "at_risk":
                risk_projects += 1
        
        # Calcular métricas
        average_progress = sum(progress_values) / len(progress_values) if progress_values else 0
        completion_rate = (projects_on_track / total_projects) * 100 if total_projects > 0 else 0
        
        return {
            "total_projects": total_projects,
            "projects_on_track": projects_on_track,
            "projects_delayed": projects_delayed,
            "risk_projects": risk_projects,
            "average_progress": round(average_progress, 2),
            "completion_rate": round(completion_rate, 2),
            "projects_analyzed": len(progress_values)
        }
    
    def _extract_progress_value(self, project_metadata: Dict) -> float:
        """
        Extrae valor de progreso de los metadatos del proyecto
        
        Args:
            project_metadata: Metadatos del proyecto
        
        Returns:
            Valor de progreso (0-100) o None si no se encuentra
        """
        # Buscar campos comunes de progreso
        progress_fields = ['progreso', 'progress', 'avance', 'completado', 'porcentaje', '%']
        
        for field in progress_fields:
            for key, value in project_metadata.items():
                if field.lower() in key.lower():
                    try:
                        # Extraer número del valor
                        if isinstance(value, str):
                            # Buscar números en el string
                            import re
                            numbers = re.findall(r'\d+\.?\d*', value)
                            if numbers:
                                progress = float(numbers[0])
                                return min(100, max(0, progress))  # Limitar entre 0-100
                        elif isinstance(value, (int, float)):
                            return min(100, max(0, float(value)))
                    except (ValueError, TypeError):
                        continue
        
        return None
    
    def _classify_project_status(self, project_metadata: Dict) -> str:
        """
        Clasifica el estado del proyecto basado en sus metadatos
        
        Args:
            project_metadata: Metadatos del proyecto
        
        Returns:
            Estado del proyecto: 'on_track', 'delayed', 'at_risk'
        """
        progress = self._extract_progress_value(project_metadata)
        
        if progress is None:
            return "unknown"
        
        # Clasificar basado en progreso
        if progress >= 80:
            return "on_track"
        elif progress >= 50:
            return "at_risk"
        else:
            return "delayed"