from flask import Blueprint, jsonify, request
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Importar servicios
from app.services.excel_processing_service import ExcelProcessingService
from app.services.project_analysis_service import ProjectAnalysisService
from app.services.search_service import SearchService
from app.services.file_upload_service import FileUploadService

# Inicializar Blueprint
api = Blueprint('api', __name__)

# Inicializar servicios
excel_service = ExcelProcessingService()
project_service = ProjectAnalysisService()
search_service = SearchService()
upload_service = FileUploadService()

# Endpoints de la API
@api.route("/response", methods=["POST"])
def index():
    """Endpoint principal para consultas al LLM"""
    try:
        prompt = request.get_json()
        response = search_service.llm_query(prompt)
        return jsonify({"LLM": response})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@api.route("/ask/SMA-Agent", methods=["POST"])
def sma_agent_chat():
    """Endpoint principal del chat SMA que maneja consultas con acceso a datos Excel"""
    try:
        print("=== CONSULTA RECIBIDA EN SMA-AGENT ===")
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No se recibieron datos"}), 400
        
        # Extraer texto de consulta (compatible con formato del frontend)
        user_text = data.get('text') or data.get('prompt') or data.get('query')
        conversation_id = data.get('conversationId', 'default')
        
        if not user_text or not user_text.strip():
            return jsonify({"success": False, "message": "Consulta vacía"}), 400
        
        print(f"Texto de consulta: {user_text}")
        print(f"ID de conversación: {conversation_id}")
        
        # Preparar prompt en formato esperado por el LLM
        prompt_data = {"prompt": user_text.strip()}
        
        # Procesar consulta con acceso a datos vectorizados
        response = search_service.llm_query(prompt_data)
        
        print(f"Respuesta generada exitosamente")
        
        # Respuesta en formato esperado por el frontend
        return jsonify({
            "success": True,
            "content": response,
            "conversationId": conversation_id,
            "timestamp": data.get('timestamp', None)
        })
        
    except Exception as e:
        print(f"❌ Error en SMA-Agent: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        print(f"📋 Detalles completos del error:\n{error_details}")
        
        return jsonify({
            "success": False, 
            "content": f"Error procesando consulta: {str(e)}",
            "message": f"Error: {str(e)}"
        }), 500

@api.route("/eliminar")
def eliminar():
    """Elimina todos los registros de la base de datos vectorial"""
    try:
        result = search_service.clear_database()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    
@api.route("/upload_excel", methods=["POST"])
def upload_excel():
    """Sube y procesa archivos Excel para análisis de proyectos"""
    try:
        print("=== INICIANDO UPLOAD EXCEL ===")
        
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No se encontró archivo"}), 400
        
        file = request.files['file']
        print(f"Archivo recibido: {file.filename}")
        
        if file.filename == '':
            return jsonify({"success": False, "message": "No se seleccionó archivo"}), 400
        
        # DEBUG: Verificar que el servicio se inicializa
        print("Llamando a upload_service...")
        result = upload_service.upload_excel_file(request)
        print("Servicio ejecutado correctamente")
        
        return jsonify(result)
            
    except Exception as e:
        print(f" ERROR CRÍTICO: {str(e)}")
        # Debug adicional para identificar el problema
        import traceback
        error_details = traceback.format_exc()
        print(f" DETALLES DEL ERROR:\n{error_details}")
        
        return jsonify({
            "success": False, 
            "message": f"Error procesando archivo: {str(e)}"
        }), 500

@api.route("/search", methods=["POST"])
def search():
    """Búsqueda semántica en los datos vectorizados"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"success": False, "message": "Se requiere 'query'"}), 400
        
        query_text = data['query']
        top_k = data.get('top_k', 10)
        
        result = search_service.semantic_search(query_text, top_k)
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400 if "Query no puede estar vacío" in result["message"] else 500
        
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
        
        result = project_service.analyze_delays(project_name, assignee, top_k)
        return jsonify(result)
        
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
        
        result = project_service.analyze_pending_tasks(project_name, assignee, top_k)
        return jsonify(result)
        
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
        result = project_service.generate_project_summary(project_name)
        
        if result["success"]:
            return jsonify(result)
        else:
            status_code = 400 if "no puede estar vacío" in result["message"] else 404 if "No se encontraron" in result["message"] else 500
            return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500