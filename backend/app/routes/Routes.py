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

# @api.route("/ask/SMA-Agent", methods=["POST"])
# def sma_agent_chat():
#     """Endpoint principal del chat SMA que maneja consultas con acceso a datos Excel"""
#     try:
#         print("=== CONSULTA RECIBIDA EN SMA-AGENT ===")
        
#         data = request.get_json()
#         if not data:
#             return jsonify({"success": False, "message": "No se recibieron datos"}), 400
        
#         # Extraer texto de consulta (compatible con formato del frontend)
#         user_text = data.get('text') or data.get('prompt') or data.get('query')
#         conversation_id = data.get('conversationId', 'default')
        
#         if not user_text or not user_text.strip():
#             return jsonify({"success": False, "message": "Consulta vacía"}), 400
        
#         print(f"Texto de consulta: {user_text}")
#         print(f"ID de conversación: {conversation_id}")
        
#         # Preparar prompt en formato esperado por el LLM
#         prompt_data = {"prompt": user_text.strip()}
        
#         # Procesar consulta con acceso a datos vectorizados
#         response = search_service.llm_query(prompt_data)
        
#         print(f"Respuesta generada exitosamente")
        
#         # Respuesta en formato esperado por el frontend
#         return jsonify({
#             "success": True,
#             "content": response,
#             "conversationId": conversation_id,
#             "timestamp": data.get('timestamp', None)
#         })
        
#     except Exception as e:
#         print(f"❌ Error en SMA-Agent: {str(e)}")
#         import traceback
#         error_details = traceback.format_exc()
#         print(f"📋 Detalles completos del error:\n{error_details}")
        
#         return jsonify({
#             "success": False, 
#             "content": f"Error procesando consulta: {str(e)}",
#             "message": f"Error: {str(e)}"
#         }), 500

@api.route("/eliminar")
def eliminar():
    """Elimina todos los registros de la base de datos vectorial"""
    try:
        result = dataBaseVectorController().eliminarRecords()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@api.route("/subirArchivo", methods=["POST"])
def subirArchivo():
    filecontroller = fileController(request.get_json())
    return jsonify(filecontroller.processarArchivo())
