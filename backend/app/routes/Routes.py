from flask import Blueprint, jsonify, request

# Importar servicios
from Controllers.LmmController import lmmController
from Controllers.dataBaseVectorController import dataBaseVectorController
from Controllers.fileController import fileController


# Inicializar Blueprint
api = Blueprint('api', __name__)

# Endpoints de la API
@api.route("/response", methods=["POST"])
def index():
    llmController = lmmController()
    """Endpoint principal para consultas al LLM"""
    try:
        prompt = request.get_json()
        response = llmController.promptValidate(prompt)
        return jsonify({"LLM": response})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500



@api.route("/eliminar", methods=["GET", "POST"])
def eliminar():
    """Elimina todos los registros de la base de datos vectorial"""
    try:
        result = dataBaseVectorController().eliminarRecords()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500



@api.route("/cargar", methods=["POST"])
def cargar():
    """Endpoint para cargar archivos Excel, PDF, Word y texto desde el frontend"""
    try:
        if 'archivo' not in request.files:
            return jsonify({"success": False, "message": "No se proporcionó archivo"}), 400
            
        archivo = request.files['archivo']
        if archivo.filename == '':
            return jsonify({"success": False, "message": "No se seleccionó archivo"}), 400
            
        controller = fileController(archivo)
        result = controller.cargarArchivo()
        
        if not result['success']:
            return jsonify(result), 400
            
        # Insertar chunks en la base de datos vectorial
        db_result = dataBaseVectorController().insertarChunks(result['chunks'])
        
        return jsonify({
            "success": True,
            "message": "Archivo cargado exitosamente",
            "archivo": result['filename']
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error interno: {str(e)}"}), 500
    
@api.route("/buscar", methods=["POST"])
def buscar():
    """Endpoint para buscar en la base de datos vectorial"""
    try:
        pregunta = request.get_json()
        response = dataBaseVectorController().buscarSimilitud(pregunta)
        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/dashboard", methods=["GET"])
def dashboard():
    """Endpoint para obtener métricas del dashboard"""
    try:
        # Por ahora devolvemos métricas de ejemplo
        # En el futuro esto se puede conectar con la base de datos
        metrics = {
            "total_projects": 0,
            "on_track": 0,
            "at_risk": 0,
            "delayed": 0
        }
        return jsonify({"success": True, "metrics": metrics})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/analyze_delays", methods=["POST"])
def analyze_delays():
    """Endpoint para analizar atrasos en proyectos"""
    try:
        # Por ahora devolvemos un análisis de ejemplo
        # En el futuro esto se puede conectar con la base de datos vectorial
        analysis = {
            "message": "Análisis de atrasos no implementado aún. Carga un archivo para habilitar esta funcionalidad.",
            "delays_found": 0,
            "projects_at_risk": []
        }
        return jsonify({"success": True, "analysis": analysis})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/pending_tasks", methods=["POST"])
def pending_tasks():
    """Endpoint para obtener tareas pendientes"""
    try:
        data = request.get_json() or {}
        assignee = data.get('assignee', '')
        
        # Por ahora devolvemos tareas de ejemplo
        tasks = {
            "message": "Análisis de tareas pendientes no implementado aún. Carga un archivo para habilitar esta funcionalidad.",
            "total_tasks": 0,
            "pending_tasks": []
        }
        
        if assignee:
            tasks["filtered_by"] = assignee
            
        return jsonify({"success": True, "tasks": tasks})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/project_summary", methods=["POST"])
def project_summary():
    """Endpoint para obtener resumen de proyecto"""
    try:
        data = request.get_json()
        project_name = data.get('project_name', '') if data else ''
        
        if not project_name:
            return jsonify({"success": False, "message": "Nombre del proyecto requerido"}), 400
            
        # Por ahora devolvemos un resumen de ejemplo
        summary = {
            "project_name": project_name,
            "message": "Resumen de proyecto no implementado aún. Carga un archivo para habilitar esta funcionalidad.",
            "status": "No disponible",
            "progress": 0,
            "key_metrics": {}
        }
        
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    