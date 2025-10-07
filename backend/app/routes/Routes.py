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



@api.route("/eliminar")
def eliminar():
    """Elimina todos los registros de la base de datos vectorial"""
    try:
        result = dataBaseVectorController().eliminarRecords()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500



@api.route("/cargar", methods=["POST"])
def cargar():
    """Endpoint para cargar archivos Excel,pdf,word,etc desde el frontend"""
    archivo = request.files['archivo']
    controller = fileController(archivo)
    chunks = controller.cargarArchivo()
    dataBaseVectorController().insertarChunks(chunks)
    return jsonify({
            "archivo": archivo.filename
        }),200
    
@api.route("/buscar", methods=["POST"])
def buscar():
    """Endpoint para buscar en la base de datos vectorial"""
    try:
        pregunta = request.get_json()
        response = dataBaseVectorController().buscarSimilitud(pregunta)
        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    