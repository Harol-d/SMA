
import os
from flask import request
from werkzeug.utils import secure_filename
from typing import Dict, Any
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from Models.databaseVectorModel import databaseVectormodel
from .excel_processing_service import ExcelProcessingService


class FileUploadService:
    """Servicio especializado en carga de archivos"""
    
    def __init__(self):
        self.db_model = databaseVectormodel()
        self.excel_service = ExcelProcessingService()
        self.upload_folder = 'uploads'
    
    def upload_excel_file(self, file_request) -> Dict[str, Any]:
        """Sube y procesa archivos Excel para análisis de proyectos"""
        try:
            if 'file' not in file_request.files:
                return {
                    "success": False, 
                    "message": "No se encontró archivo",
                    "recommendations": ["Seleccionar un archivo Excel (.xlsx o .xls)"]
                }
            
            file = file_request.files['file']
            
            if file.filename == '':
                return {
                    "success": False, 
                    "message": "No se seleccionó archivo",
                    "recommendations": ["Seleccionar un archivo válido"]
                }
            
            if not self.excel_service.allowed_file(file.filename):
                return {
                    "success": False, 
                    "message": "Solo archivos .xlsx y .xls",
                    "recommendations": [
                        "Convertir el archivo a formato Excel",
                        "Verificar que la extensión sea .xlsx o .xls"
                    ]
                }
            
            upload_path = os.path.join(os.path.dirname(__file__), '..', self.upload_folder)
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            try:
                vectors_data = self.excel_service.process_excel_to_vectors(file_path)
                
                if not vectors_data:
                    return {
                        "success": False, 
                        "message": "No se encontraron datos válidos",
                        "recommendations": [
                            "Verificar que el Excel tenga datos en las filas",
                            "Asegurarse de que las columnas tengan nombres descriptivos",
                            "Incluir al menos: Proyecto, Asignado, Actividad, Progreso"
                        ]
                    }
                
                upsert_result = self.db_model.upsert_vectors(vectors_data)
                
                if not upsert_result["success"]:
                    return {
                        "success": False, 
                        "message": f"Error en base de datos: {upsert_result['message']}",
                        "recommendations": [
                            "Verificar conexión a la base de datos vectorial",
                            "Revisar configuración de Pinecone",
                            "Contactar al administrador del sistema"
                        ]
                    }
                
                os.remove(file_path)
                
                # Obtener estadísticas de calidad de datos
                validation_vector = next((v for v in vectors_data if v['metadata'].get('analysis_type') == 'file_validation'), None)
                quality_score = validation_vector['metadata'].get('data_quality_score', 0) if validation_vector else 0
                warnings_count = validation_vector['metadata'].get('warnings_count', 0) if validation_vector else 0
                recommendations_count = validation_vector['metadata'].get('recommendations_count', 0) if validation_vector else 0
                
                return {
                    "success": True,
                    "message": "Archivo procesado exitosamente",
                    "data": {
                        "filename": filename,
                        "rows_processed": len(vectors_data) - 1,  # -1 para excluir el vector de validación
                        "vectors_created": upsert_result["vectors_count"],
                        "data_quality_score": quality_score,
                        "warnings_count": warnings_count,
                        "recommendations_count": recommendations_count
                    }
                }
                
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise e
                
        except Exception as e:
            error_message = str(e)
            recommendations = []
            if 'validation_score' in error_message or 'data_quality' in error_message:
                recommendations.extend([
                    "Verificar que el Excel tenga las columnas correctas",
                    "Asegurarse de que los datos no estén vacíos",
                    "Revisar el formato de los porcentajes de progreso"
                ])
            elif 'Permission' in error_message:
                recommendations.extend([
                    "Cerrar el archivo Excel si está abierto",
                    "Verificar permisos de escritura en la carpeta"
                ])
            else:
                recommendations.extend([
                    "Verificar que el archivo no esté corrupto",
                    "Intentar con un archivo Excel diferente",
                    "Contactar soporte técnico si el problema persiste"
                ])
            
            return {
                "success": False, 
                "message": f"Error: {error_message}",
                "recommendations": recommendations
            }
