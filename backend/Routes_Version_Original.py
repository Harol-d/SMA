import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import uuid
import re
from typing import Dict, Any, List
from flask import Blueprint, jsonify, request, make_response
from datetime import datetime
from Controllers.LmmController import lmmController
from Models.databaseVectorModel import databaseVectormodel
from Controllers.dataBaseVectorController import dataBaseVectorController

api = Blueprint('api', __name__)
llmresponse = lmmController()
dbModel = databaseVectormodel()
dbController = dataBaseVectorController()

# Configuración para archivos Excel
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_excel_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza y limpia los datos del DataFrame de Excel"""
    df_clean = df.copy()
    
    # Eliminar filas completamente vacías
    df_clean = df_clean.dropna(how='all')
    
    # Reemplazar valores NaN con cadenas vacías
    df_clean = df_clean.fillna('')
    
    # Limpiar strings y normalizar
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean[col] = df_clean[col].astype(str).str.strip()
            # Reemplazar valores que pandas convierte a 'nan' string
            df_clean[col] = df_clean[col].replace(['nan', 'NaN', 'None', 'null'], '')
    
    return df_clean

def extract_project_data(row: pd.Series, columns: List[str]) -> Dict[str, Any]:
    """Extrae información estructurada de proyectos de una fila del Excel"""
    project_data = {
        'assignee': None,
        'project_name': None,
        'activity_name': None,
        'progress_percentage': None,
        'notes': None,
        'timeline_start': None,
        'timeline_end': None,
        'status': 'unknown',
        'is_delayed': False,
        'pending_tasks': [],
        'delay_reasons': [],
        'data_quality': 'complete',
        'missing_fields': [],
        'warnings': []
    }
    
    # Campos reconocidos automáticamente
    assignee_fields = ['asignado', 'assignee', 'responsable', 'encargado']
    project_fields = ['proyecto', 'project', 'nombre_proyecto']
    activity_fields = ['actividad', 'activity', 'tarea', 'task']
    progress_fields = ['progreso', 'progress', 'avance', 'porcentaje', 'completado']
    notes_fields = ['notas', 'notes', 'comentarios', 'observaciones']
    date_fields = ['fecha_inicio', 'fecha_fin', 'start_date', 'end_date', 'timeline']
    
    # Procesar cada columna
    for col in columns:
        col_lower = col.lower().strip()
        value = str(row[col]).strip() if pd.notna(row[col]) else ''
        
        # Validar que el valor no esté vacío
        is_valid_value = value and value not in ['', 'nan', 'NaN', 'None', 'null']
        
        if is_valid_value:
            if any(field in col_lower for field in assignee_fields):
                project_data['assignee'] = value
            elif any(field in col_lower for field in project_fields):
                project_data['project_name'] = value
            elif any(field in col_lower for field in activity_fields):
                project_data['activity_name'] = value
            elif any(field in col_lower for field in progress_fields):
                progress = extract_percentage(value)
                if progress is not None:
                    project_data['progress_percentage'] = progress
                    if progress < 50:
                        project_data['status'] = 'delayed'
                        project_data['is_delayed'] = True
                    elif progress < 80:
                        project_data['status'] = 'at_risk'
                    else:
                        project_data['status'] = 'on_track'
                else:
                    project_data['warnings'].append(f'Valor de progreso no válido: {value}')
            elif any(field in col_lower for field in notes_fields):
                project_data['notes'] = value
                project_data['delay_reasons'] = analyze_delays_in_notes(value)
                project_data['pending_tasks'] = extract_pending_tasks(value)
            elif any(field in col_lower for field in date_fields):
                if 'inicio' in col_lower or 'start' in col_lower:
                    project_data['timeline_start'] = value
                elif 'fin' in col_lower or 'end' in col_lower:
                    project_data['timeline_end'] = value
        else:
            # Registrar campos vacíos importantes
            if any(field in col_lower for field in assignee_fields + project_fields + activity_fields):
                project_data['missing_fields'].append(col)
    
    # Evaluar calidad de datos
    critical_fields = ['project_name', 'assignee', 'activity_name']
    missing_critical = [field for field in critical_fields if not project_data[field]]
    
    if len(missing_critical) >= 2:
        project_data['data_quality'] = 'poor'
        project_data['warnings'].append(f'Faltan campos críticos: {missing_critical}')
    elif len(missing_critical) == 1:
        project_data['data_quality'] = 'partial'
        project_data['warnings'].append(f'Falta campo crítico: {missing_critical[0]}')
    
    if not project_data['progress_percentage']:
        project_data['warnings'].append('Sin información de progreso')
    
    return project_data

def extract_percentage(value: str) -> float:
    """Extrae porcentaje de un string"""
    if isinstance(value, (int, float)):
        return float(value)
    
    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%?', str(value))
    if numbers:
        return min(100, max(0, float(numbers[0])))
    return None

def analyze_delays_in_notes(notes: str) -> List[str]:
    """Analiza las notas para identificar razones de atrasos"""
    delay_indicators = [
        'atraso', 'retraso', 'delay', 'pendiente', 'problema', 'issue',
        'bloqueado', 'blocked', 'esperando', 'waiting', 'falta', 'missing',
        'cancelado', 'cancelled', 'pospuesto', 'postponed'
    ]
    
    reasons = []
    sentences = notes.split('.')
    
    for sentence in sentences:
        if any(indicator in sentence.lower() for indicator in delay_indicators):
            reason = sentence.strip()
            if len(reason) > 10:
                reasons.append(reason)
    
    return reasons

def extract_pending_tasks(notes: str) -> List[str]:
    """Extrae tareas pendientes de las notas"""
    pending_indicators = [
        'pendiente', 'pending', 'por hacer', 'to do', 'falta', 'missing',
        'revisar', 'review', 'completar', 'complete', 'terminar', 'finish'
    ]
    
    tasks = []
    sentences = notes.replace(',', '.').split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if any(indicator in sentence.lower() for indicator in pending_indicators):
            if len(sentence) > 10:
                tasks.append(sentence)
    
    return tasks

def create_project_text(row: pd.Series, columns: List[str], project_data: Dict[str, Any]) -> str:
    """Crea texto descriptivo para análisis de proyectos"""
    parts = []
    
    if project_data['project_name']:
        parts.append(f"Proyecto: {project_data['project_name']}")
    if project_data['activity_name']:
        parts.append(f"Actividad: {project_data['activity_name']}")
    if project_data['assignee']:
        parts.append(f"Asignado a: {project_data['assignee']}")
    if project_data['progress_percentage'] is not None:
        parts.append(f"Progreso: {project_data['progress_percentage']}%")
        parts.append(f"Estado: {project_data['status']}")
        if project_data['is_delayed']:
            parts.append("PROYECTO CON ATRASO IDENTIFICADO")
    
    if project_data['notes']:
        parts.append(f"Notas: {project_data['notes']}")
    
    if project_data['delay_reasons']:
        parts.append("Razones de atraso:")
        for reason in project_data['delay_reasons']:
            parts.append(f"- {reason}")
    
    if project_data['pending_tasks']:
        parts.append("Tareas pendientes:")
        for task in project_data['pending_tasks']:
            parts.append(f"- {task}")
    
    context = "Información de seguimiento de proyecto. Análisis de avances, atrasos y gestión de tareas."
    return ". ".join(parts) + ". " + context

def process_excel_to_vectors(file_path: str) -> List[Dict[str, Any]]:
    """Procesa un archivo Excel y convierte cada fila en datos para vectores"""
    try:
        df = pd.read_excel(file_path)
        df_clean = normalize_excel_data(df)
        columns = df_clean.columns.tolist()
        vectors_data = []
        
        for index, row in df_clean.iterrows():
            project_data = extract_project_data(row, columns)
            descriptive_text = create_project_text(row, columns, project_data)
            
            metadata = {}
            for col in columns:
                metadata[col] = str(row[col]).strip()
            
            metadata.update(project_data)
            metadata['row_index'] = index
            metadata['file_source'] = os.path.basename(file_path)
            metadata['analysis_type'] = 'project_management'
            
            vectors_data.append({
                'id': f"project_{project_data.get('project_name', 'unknown')}_{index}_{uuid.uuid4().hex[:8]}",
                'text': descriptive_text,
                'metadata': metadata
            })
        
        return vectors_data
        
    except Exception as e:
        raise Exception(f"Error procesando archivo Excel: {str(e)}")

@api.route("/response", methods=["POST"])
def index():
    """Endpoint principal para consultas al LLM"""
    prompt = request.get_json()
    response = llmresponse.promptValidate(prompt)
    return jsonify({"LLM": response})

@api.route("/eliminar")
def eliminar():
    """Elimina todos los registros de la base de datos vectorial"""
    dbModel.eliminarRecords()
    return jsonify({"mensaje": "Registros eliminados correctamente"})

@api.route("/crear")
def crear():
    """Crea embeddings desde archivo SQL"""
    sql_file_path = os.path.join(os.path.dirname(__file__), './db/Serviciosvirtuales.sql')
    chunks = dbController.crearChunks(sql_file_path)
    return jsonify({"mensaje": f"chunks creados correctamente: {chunks}"})

@api.route("/upload_excel", methods=["POST"])
def upload_excel():
    """Sube y procesa archivos Excel para análisis de proyectos"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No se encontró archivo"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "No se seleccionó archivo"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "message": "Solo archivos .xlsx y .xls"}), 400
        
        upload_path = os.path.join(os.path.dirname(__file__), UPLOAD_FOLDER)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        try:
            vectors_data = process_excel_to_vectors(file_path)
            
            if not vectors_data:
                return jsonify({"success": False, "message": "No se encontraron datos válidos"}), 400
            
            upsert_result = dbModel.upsert_vectors(vectors_data)
            
            if not upsert_result["success"]:
                return jsonify({"success": False, "message": f"Error: {upsert_result['message']}"}), 500
            
            os.remove(file_path)
            
            return jsonify({
                "success": True,
                "message": "Archivo procesado exitosamente",
                "data": {
                    "filename": filename,
                    "rows_processed": len(vectors_data),
                    "vectors_created": upsert_result["vectors_count"]
                }
            })
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/search", methods=["POST"])
def search():
    """Búsqueda semántica en los datos vectorizados"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"success": False, "message": "Se requiere 'query'"}), 400
        
        query_text = data['query'].strip()
        top_k = data.get('top_k', 10)
        
        if not query_text:
            return jsonify({"success": False, "message": "Query no puede estar vacío"}), 400
        
        search_result = dbModel.search_similar_vectors(query_text, top_k)
        
        if not search_result["success"]:
            return jsonify({"success": False, "message": f"Error: {search_result['message']}"}), 500
        
        return jsonify({
            "success": True,
            "query": search_result["query"],
            "total_found": search_result["total_found"],
            "results": search_result["results"]
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/analyze_delays", methods=["POST"])
def analyze_delays():
    """Analiza proyectos con atrasos y sus causas"""
    try:
        data = request.get_json() or {}
        project_name = data.get('project_name', '')
        assignee = data.get('assignee', '')
        top_k = data.get('top_k', 20)
        
        query_parts = ["proyectos con atraso", "tareas atrasadas", "problemas identificados"]
        
        if project_name:
            query_parts.append(f"proyecto {project_name}")
        if assignee:
            query_parts.append(f"asignado a {assignee}")
        
        query_text = " ".join(query_parts)
        search_result = dbModel.search_similar_vectors(query_text, top_k)
        
        if not search_result["success"]:
            return jsonify({"success": False, "message": f"Error: {search_result['message']}"}), 500
        
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
        
        llm_analysis = llmresponse.promptValidate(llm_prompt)
        
        return jsonify({
            "success": True,
            "query": query_text,
            "delayed_projects_found": len(delayed_projects),
            "delayed_projects": delayed_projects,
            "llm_analysis": llm_analysis
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/pending_tasks", methods=["POST"])
def pending_tasks():
    """Identifica y analiza tareas pendientes"""
    try:
        data = request.get_json() or {}
        project_name = data.get('project_name', '')
        assignee = data.get('assignee', '')
        top_k = data.get('top_k', 15)
        
        query_parts = ["tareas pendientes", "por hacer", "completar", "revisar"]
        
        if project_name:
            query_parts.append(f"proyecto {project_name}")
        if assignee:
            query_parts.append(f"asignado a {assignee}")
        
        query_text = " ".join(query_parts)
        search_result = dbModel.search_similar_vectors(query_text, top_k)
        
        if not search_result["success"]:
            return jsonify({"success": False, "message": f"Error: {search_result['message']}"}), 500
        
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
        
        llm_analysis = llmresponse.promptValidate(llm_prompt)
        
        return jsonify({
            "success": True,
            "query": query_text,
            "projects_with_pending_tasks": len(projects_with_tasks),
            "projects": projects_with_tasks,
            "llm_analysis": llm_analysis
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/project_summary", methods=["POST"])
def project_summary():
    """Resumen completo de un proyecto específico"""
    try:
        data = request.get_json()
        
        if not data or 'project_name' not in data:
            return jsonify({"success": False, "message": "Se requiere 'project_name'"}), 400
        
        project_name = data['project_name'].strip()
        
        if not project_name:
            return jsonify({"success": False, "message": "Nombre del proyecto no puede estar vacío"}), 400
        
        search_result = dbModel.search_similar_vectors(f"proyecto {project_name}", 50)
        
        if not search_result["success"]:
            return jsonify({"success": False, "message": f"Error: {search_result['message']}"}), 500
        
        project_activities = []
        for result in search_result["results"]:
            metadata = result.get("metadata", {})
            if project_name.lower() in str(metadata.get("project_name", "")).lower():
                project_activities.append(result)
        
        if not project_activities:
            return jsonify({"success": False, "message": f"No se encontraron actividades para '{project_name}'"}), 404
        
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
        
        llm_analysis = llmresponse.promptValidate(llm_prompt)
        
        return jsonify({
            "success": True,
            "project_name": project_name,
            "metrics": summary_data,
            "activities": project_activities,
            "llm_analysis": llm_analysis
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/dashboard", methods=["GET"])
def dashboard():
    """Métricas consolidadas del dashboard"""
    try:
        dashboard_data = dbController.obtener_metricas_dashboard()
        
        if not dashboard_data["success"]:
            return jsonify({"success": False, "message": f"Error: {dashboard_data['message']}"}), 500
        
        response_data = {
            "success": True,
            "timestamp": pd.Timestamp.now().isoformat(),
            "data": {
                "summary": {
                    "total_vectors": dashboard_data["total_vectors"],
                    "projects_analyzed": dashboard_data["sample_analyzed"],
                    "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "metrics": dashboard_data["metrics"]
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500