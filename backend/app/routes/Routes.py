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

        # Verificar que se recibió un archivo
    if 'archivo' not in request.files:
            return jsonify({
                "success": False,
                "error": "No se recibió ningún archivo"
            }), 400
        
    file = request.files['archivo']
        
        # Verificar que el archivo no esté vacío
    if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No se seleccionó ningún archivo"
            }), 400
        
        # Verificar extensión del archivo
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf', '.docx', '.doc')):
            return jsonify({
                "success": False,
                "error": "Solo se permiten archivos Excel (.xlsx, .xls), PDF (.pdf), Word (.docx, .doc)"
            }), 400
    return jsonify({
        "success": True,
        "message": "Archivo cargado exitosamente",
        "archivo": file.filename
    }),200
        
        # Guardar archivo de forma segura
        filename = secure_filename(file.filename)
        # file_path = os.path.join(upload_folder, filename)
        # file.save(file_path)
        
        # Procesar archivo usando FileUploadService
    #     upload_service = FileUploadService()
    #     result = upload_service.process_file_complete(file_path)
        
    #     # Limpiar archivo temporal
    #     try:
    #         os.remove(file_path)
    #     except:
    #         pass  # Ignorar errores al eliminar archivo temporal
        
    #     if result.get('success', False):
    #         # Guardar chunks en la base de datos vectorial
    #         try:
    #             chunks = result.get('chunks', [])
    #             if chunks:
    #                 # Guardar chunks en la base de datos vectorial
    #                 db_controller = dataBaseVectorController()
    #                 db_result = db_controller.insertarChunks(chunks)
                
    #             return jsonify({
    #                 "success": True,
    #                 "message": "Archivo Excel procesado exitosamente",
    #                 "chunks_count": len(chunks),
    #                 "document_id": result.get('document_id'),
    #                 "processing_info": result.get('conversion_info', {})
    #             })
    #         except Exception as db_error:
    #             return jsonify({
    #                 "success": False,
    #                 "error": f"Error al guardar en base de datos: {str(db_error)}"
    #             }), 500
    #     else:
    #         return jsonify({
    #             "success": False,
    #             "error": result.get('message', 'Error desconocido al procesar el archivo')
    #         }), 400
            
    # except Exception as e:
    #     return jsonify({
    #         "success": False,
    #         "error": f"Error al procesar el archivo Excel: {str(e)}"
    #     }), 500

