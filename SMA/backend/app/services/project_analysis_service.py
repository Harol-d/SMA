"""
Servicio de análisis de proyectos
Maneja el análisis de atrasos, tareas pendientes y resúmenes de proyectos
"""

from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from Controllers.LmmController import lmmController
from Models.databaseVectorModel import databaseVectormodel


class ProjectAnalysisService:
    """Servicio especializado en análisis de proyectos"""
    
    def __init__(self):
        self.llm_controller = lmmController()
        self.db_model = databaseVectormodel()
    
    def analyze_delays(self, project_name: str = '', assignee: str = '', top_k: int = 20) -> Dict[str, Any]:
        """Analiza proyectos con atrasos y sus causas"""
        try:
            query_parts = ["proyectos con atraso", "tareas atrasadas", "problemas identificados"]
            
            if project_name:
                query_parts.append(f"proyecto {project_name}")
            if assignee:
                query_parts.append(f"asignado a {assignee}")
            
            query_text = " ".join(query_parts)
            search_result = self.db_model.search_similar_vectors(query_text, top_k)
            
            if not search_result["success"]:
                return {"success": False, "message": f"Error: {search_result['message']}"}
            
            delayed_projects = []
            for result in search_result["results"]:
                metadata = result.get("metadata", {})
                if metadata.get("is_delayed") or metadata.get("status") == "delayed":
                    delayed_projects.append(result)
            
            context_text = "Análisis de atrasos en proyectos:\n\n"
            for project in delayed_projects:
                metadata = project.get("metadata", {})
                context_text += f"Proyecto: {metadata.get('project_name', 'N/A')}\n"
                context_text += f"Asignado: {metadata.get('assignee', 'N/A')}\n"
                context_text += f"Progreso: {metadata.get('progress_percentage', 'N/A')}%\n"
                context_text += f"Notas: {metadata.get('notes', 'N/A')}\n"
                if metadata.get('delay_reasons'):
                    context_text += f"Razones de atraso: {', '.join(metadata.get('delay_reasons', []))}\n"
                context_text += "\n---\n\n"
            
            llm_prompt = {
                "prompt": f"""Analiza los siguientes proyectos con atrasos:

{context_text}

Proporciona:
1. Resumen de atrasos identificados
2. Principales razones de los atrasos
3. Recomendaciones específicas para cada proyecto
4. Acciones correctivas prioritarias

Análisis detallado y accionable."""
            }
            
            llm_analysis = self.llm_controller.promptValidate(llm_prompt)
            
            return {
                "success": True,
                "query": query_text,
                "delayed_projects_found": len(delayed_projects),
                "delayed_projects": delayed_projects,
                "llm_analysis": llm_analysis
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def analyze_pending_tasks(self, project_name: str = '', assignee: str = '', top_k: int = 15) -> Dict[str, Any]:
        """Identifica y analiza tareas pendientes"""
        try:
            query_parts = ["tareas pendientes", "por hacer", "completar", "revisar"]
            
            if project_name:
                query_parts.append(f"proyecto {project_name}")
            if assignee:
                query_parts.append(f"asignado a {assignee}")
            
            query_text = " ".join(query_parts)
            search_result = self.db_model.search_similar_vectors(query_text, top_k)
            
            if not search_result["success"]:
                return {"success": False, "message": f"Error: {search_result['message']}"}
            
            projects_with_tasks = []
            
            for result in search_result["results"]:
                metadata = result.get("metadata", {})
                pending_tasks = metadata.get("pending_tasks", [])
                
                if pending_tasks:
                    project_info = {
                        "project_name": metadata.get("project_name", "N/A"),
                        "assignee": metadata.get("assignee", "N/A"),
                        "progress": metadata.get("progress_percentage", "N/A"),
                        "pending_tasks": pending_tasks,
                        "notes": metadata.get("notes", "")
                    }
                    projects_with_tasks.append(project_info)
            
            context_text = "Tareas pendientes identificadas:\n\n"
            for project in projects_with_tasks:
                context_text += f"Proyecto: {project['project_name']}\n"
                context_text += f"Asignado: {project['assignee']}\n"
                context_text += f"Progreso: {project['progress']}%\n"
                context_text += "Tareas pendientes:\n"
                for task in project['pending_tasks']:
                    context_text += f"  - {task}\n"
                context_text += "\n---\n\n"
            
            llm_prompt = {
                "prompt": f"""Analiza las siguientes tareas pendientes:

{context_text}

Proporciona:
1. Resumen de tareas pendientes por proyecto
2. Priorización de tareas críticas
3. Recomendaciones de asignación de recursos
4. Plan de acción para completar tareas

Recomendaciones específicas y accionables."""
            }
            
            llm_analysis = self.llm_controller.promptValidate(llm_prompt)
            
            return {
                "success": True,
                "query": query_text,
                "projects_with_pending_tasks": len(projects_with_tasks),
                "projects": projects_with_tasks,
                "llm_analysis": llm_analysis
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def generate_project_summary(self, project_name: str) -> Dict[str, Any]:
        """Resumen completo de un proyecto específico"""
        try:
            if not project_name or not project_name.strip():
                return {"success": False, "message": "Nombre del proyecto no puede estar vacío"}
            
            search_result = self.db_model.search_similar_vectors(f"proyecto {project_name}", 50)
            
            if not search_result["success"]:
                return {"success": False, "message": f"Error: {search_result['message']}"}
            
            project_activities = []
            for result in search_result["results"]:
                metadata = result.get("metadata", {})
                if project_name.lower() in str(metadata.get("project_name", "")).lower():
                    project_activities.append(result)
            
            if not project_activities:
                return {"success": False, "message": f"No se encontraron actividades para '{project_name}'"}
            
            # Calcular métricas
            total_activities = len(project_activities)
            completed_activities = 0
            delayed_activities = 0
            at_risk_activities = 0
            total_progress = 0
            assignees = set()
            all_pending_tasks = []
            all_delay_reasons = []
            
            for activity in project_activities:
                metadata = activity.get("metadata", {})
                
                status = metadata.get("status", "unknown")
                if status == "on_track":
                    completed_activities += 1
                elif status == "delayed":
                    delayed_activities += 1
                elif status == "at_risk":
                    at_risk_activities += 1
                
                progress = metadata.get("progress_percentage")
                if progress is not None:
                    total_progress += progress
                
                if metadata.get("assignee"):
                    assignees.add(metadata.get("assignee"))
                
                if metadata.get("pending_tasks"):
                    all_pending_tasks.extend(metadata.get("pending_tasks"))
                
                if metadata.get("delay_reasons"):
                    all_delay_reasons.extend(metadata.get("delay_reasons"))
            
            average_progress = total_progress / total_activities if total_activities > 0 else 0
            completion_rate = (completed_activities / total_activities) * 100 if total_activities > 0 else 0
            
            summary_data = {
                "project_name": project_name,
                "total_activities": total_activities,
                "completed_activities": completed_activities,
                "delayed_activities": delayed_activities,
                "at_risk_activities": at_risk_activities,
                "average_progress": round(average_progress, 2),
                "completion_rate": round(completion_rate, 2),
                "assignees": list(assignees),
                "pending_tasks_count": len(all_pending_tasks),
                "delay_reasons_count": len(all_delay_reasons)
            }
            
            context_text = f"""Resumen del Proyecto: {project_name}

Métricas:
- Total actividades: {total_activities}
- Completadas: {completed_activities}
- Atrasadas: {delayed_activities}
- En riesgo: {at_risk_activities}
- Progreso promedio: {average_progress:.2f}%
- Personas: {', '.join(assignees)}

Tareas pendientes ({len(all_pending_tasks)}):
{chr(10).join([f"- {task}" for task in all_pending_tasks[:10]])}

Razones de atraso ({len(all_delay_reasons)}):
{chr(10).join([f"- {reason}" for reason in all_delay_reasons[:10]])}
"""
            
            llm_prompt = {
                "prompt": f"""Proporciona análisis ejecutivo del proyecto:

{context_text}

Incluye:
1. Estado general del proyecto
2. Análisis de riesgos
3. Recomendaciones para mejorar rendimiento
4. Plan de acción sugerido
5. Evaluación de carga de trabajo

Insights accionables para toma de decisiones."""
            }
            
            llm_analysis = self.llm_controller.promptValidate(llm_prompt)
            
            return {
                "success": True,
                "project_name": project_name,
                "metrics": summary_data,
                "activities": project_activities,
                "llm_analysis": llm_analysis
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
