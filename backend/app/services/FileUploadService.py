from app.services.Chunk_service import ChunksService
# from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
import os
from werkzeug.utils import secure_filename


class FileUploadService:
    def __init__(self):
        self.chunk = ChunksService(size=5000, overlap=20)
    
    def validateFile(self, archivo):
            # Si es un objeto FileStorage de Flask
            if hasattr(archivo, 'filename'):
                filename = archivo.filename
                if not filename or filename.strip() == "":
                    return {"success": False, "message": "Error: No se ha proporcionado un archivo válido."}
                
                # Verificar extensión del archivo
                if not filename.lower().endswith(('.xlsx', '.xls', '.pdf', '.docx', '.doc', '.txt')):
                    return {"success": False, "message": "Error: Solo se permiten archivos Excel (.xlsx, .xls), PDF (.pdf), Word (.docx, .doc) o texto (.txt)"}
            
            return {"success": True}
    
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
    
    def guardarArchivo(self, archivo, path_folder):
            filename = secure_filename(archivo.filename)
            file_path = os.path.join(path_folder, filename)
            archivo.save(file_path)
            return file_path

    def process_file_complete(self, file_path: str):
        """Proceso completo: validación + conversión a chunks"""
        # Paso 1: Validar archivo
        validation = self.validateFile(file_path)
        
        if isinstance(validation, dict) and not validation['success']:
            return validation
        
        # Paso 2: Convertir a chunks
        result = self.ArchiveToChunks(file_path)
        
        return result
