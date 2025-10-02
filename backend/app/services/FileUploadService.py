
from app.services.Chunk_service import ChunksService
from app.services.jsonProcessing import ConvertDocJSON

class FileUploadService:
    def __init__(self):
        self.chunk = ChunksService(size=5000, overlap=20)
        self.json_converter = ConvertDocJSON()  # Servicio de JSON
    
    def validateFile(self, file_path: str):
        try:
            if not file_path.strip():
                raise ValueError("Error: No se ha proporcionado una ruta de archivo.")
        
            if file_path.strip() == "":
                raise ValueError("Error: La ruta del archivo no puede estar vacía.")
            
            # Validar que el archivo existe
            import os
            if not os.path.exists(file_path):
                raise ValueError(f"Error: El archivo {file_path} no existe.")
            
            # Validar extensión permitida usando el json_converter
            if not self.json_converter.allowed_file(file_path):
                raise ValueError(f"Error: Tipo de archivo no permitido. Formatos válidos: {', '.join(self.json_converter.allowed_extensions)}")
            
            file_path = file_path.strip()
            validate = True
            return validate
            
        except (ValueError, Exception) as e:
            return {
                "success": False,
                "message": f"Error: el archivo no es válido: {str(e)}",
                "recommendations": [
                    "Seleccionar un archivo válido (.xlsx, .xls, .pdf)",
                    "Verificar que el archivo existe en la ruta especificada",
                    "Asegurarse de que el archivo no esté corrupto"
                ]
            }

    def ArchiveToChunks(self, file_path: str):
        """Convierte archivos Excel/PDF a JSON y luego a chunks"""
        try:
            # Primero: convertir el archivo a JSON usando jsonProcessing
            conversion_result = self.json_converter.process_document(file_path)
            
            if not conversion_result['success']:
                raise ValueError(f"Error en conversión: {conversion_result['error']}")
            
            # Segundo: obtener los chunks listos para embedding
            embedding_chunks = conversion_result['embedding_chunks']
            
            # Tercero: si necesitas procesar los chunks con tu ChunksService existente
            # puedes convertir los embedding_chunks al formato que espera tu servicio
            processed_chunks = self._adapt_chunks_for_service(embedding_chunks)
            
            return {
                "success": True,
                "chunks": processed_chunks,
                "conversion_info": conversion_result['processing_info'],
                "document_id": conversion_result['document']['document_id']
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando archivo: {str(e)}",
                "chunks": []
            }
    
    def _adapt_chunks_for_service(self, embedding_chunks):
        """Adapta los chunks del conversor JSON al formato que espera tu ChunksService"""
        adapted_chunks = []
        
        for chunk in embedding_chunks:
            # Crear estructura compatible con tu sistema existente
            adapted_chunk = {
                'id': chunk['chunk_id'],
                'content': chunk['content'],
                'metadata': chunk['metadata'],
                'type': 'document_chunk'
            }
            adapted_chunks.append(adapted_chunk)
        
        return adapted_chunks
    
    def process_file_complete(self, file_path: str):
        """Proceso completo: validación + conversión a chunks"""
        # Paso 1: Validar archivo
        validation = self.validateFile(file_path)
        
        if isinstance(validation, dict) and not validation['success']:
            return validation
        
        # Paso 2: Convertir a chunks
        result = self.ArchiveToChunks(file_path)
        
        return result


# Ejemplo de uso
if __name__ == "__main__":
    upload_service = FileUploadService()
    
    # Procesar un archivo
    file_path = "mi_documento.xlsx"  # o "mi_documento.pdf"
    
    result = upload_service.process_file_complete(file_path)
    
    if result['success']:
        print(f"Procesamiento exitoso!")
        print(f"Chunks generados: {len(result['chunks'])}")
        print(f"Tipo de archivo: {result['conversion_info']['file_type']}")
        
        # Mostrar primer chunk como ejemplo
        if result['chunks']:
            print(f"\nPrimer chunk:")
            print(f"ID: {result['chunks'][0]['id']}")
            print(f"Contenido: {result['chunks'][0]['content'][:100]}...")
    else:
        print(f"Error: {result['message']}")