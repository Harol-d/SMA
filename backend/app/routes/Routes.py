from flask import Blueprint, jsonify, request
import os
from werkzeug.utils import secure_filename

# Importar servicios
from Controllers.LmmController import lmmController
from Controllers.dataBaseVectorController import dataBaseVectorController
from app.services.FileUploadService import FileUploadService

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

@api.route("/ask/SMA-Agent", methods=["POST"])
def sma_agent_chat():
    """Endpoint principal del chat SMA que maneja consultas con acceso a datos Excel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No se recibieron datos"}), 400
        
        # Extraer texto de consulta (compatible con formato del frontend)
        user_text = data.get('text') or data.get('prompt') or data.get('query')
        conversation_id = data.get('conversationId', 'default')
        
        if not user_text or not user_text.strip():
            return jsonify({"success": False, "message": "Consulta vacía"}), 400
        
        # Preparar prompt en formato esperado por el LLM
        prompt_data = {"prompt": user_text.strip()}
        
        # Procesar consulta usando el controlador LLM
        llmController = lmmController()
        response = llmController.promptValidate(prompt_data)
        
        # Respuesta en formato esperado por el frontend
        return jsonify({
            "success": True,
            "content": response,
            "conversationId": conversation_id,
            "timestamp": data.get('timestamp', None)
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "content": f"Error procesando consulta: {str(e)}",
            "message": f"Error: {str(e)}"
        }), 500

@api.route("/eliminar")
def eliminar():
    """Elimina todos los registros de la base de datos vectorial"""
    try:
        result = dataBaseVectorController().eliminarRecords()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500



@api.route("/upload_excel", methods=["POST"])
def upload_excel():
    """Endpoint para cargar archivos Excel desde el frontend"""
    try:
        # Verificar que se recibió un archivo
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No se recibió ningún archivo"
            }), 400
        
        file = request.files['file']
        
        # Verificar que el archivo no esté vacío
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No se seleccionó ningún archivo"
            }), 400
        
        # Verificar extensión del archivo
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                "success": False,
                "error": "Solo se permiten archivos Excel (.xlsx, .xls)"
            }), 400
        
        # Crear directorio de uploads si no existe
        upload_folder = 'uploads'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Guardar archivo de forma segura
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Procesar archivo usando FileUploadService
        upload_service = FileUploadService()
        result = upload_service.process_file_complete(file_path)
        
        # Limpiar archivo temporal
        try:
            os.remove(file_path)
        except:
            pass  # Ignorar errores al eliminar archivo temporal
        
        if result.get('success', False):
            # Guardar chunks en la base de datos vectorial
            try:
                chunks = result.get('chunks', [])
                if chunks:
                    # Guardar chunks en la base de datos vectorial
                    db_controller = dataBaseVectorController()
                    db_result = db_controller.insertarChunks(chunks)
                
                return jsonify({
                    "success": True,
                    "message": "Archivo Excel procesado exitosamente",
                    "chunks_count": len(chunks),
                    "document_id": result.get('document_id'),
                    "processing_info": result.get('conversion_info', {})
                })
            except Exception as db_error:
                return jsonify({
                    "success": False,
                    "error": f"Error al guardar en base de datos: {str(db_error)}"
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": result.get('message', 'Error desconocido al procesar el archivo')
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error al procesar el archivo Excel: {str(e)}"
        }), 500
