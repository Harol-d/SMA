from app.services.FileUploadService import FileUploadService
from app.services.Chunk_service import ChunksService


class fileController:
    def __init__(self, archivo):
        self.file = archivo
        self.file_service = FileUploadService()
        self.chunk = ChunksService(size=5000, overlap=20)
        # Usar ruta absoluta para evitar problemas de directorio
        import os
        self.route = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

    def cargarArchivo(self):
        # Validar el archivo
        validate = self.file_service.validateFile(self.file)
        if not validate['success']:
            return validate
            
        try:
            # Crear directorio si no existe
            import os
            os.makedirs(self.route, exist_ok=True)
            
            # Guardar archivo
            file_path = self.file_service.guardarArchivo(self.file, self.route)
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return {"success": False, "message": f"Error: El archivo no se guardó correctamente"}
            
            # Procesar archivo a chunks
            chunks = self.chunk.ArchiveToChunks(file_path)
            
            # Verificar si hay error en el procesamiento
            if isinstance(chunks, Exception):
                return {"success": False, "message": f"Error procesando archivo: {str(chunks)}"}
            
            return {"success": True, "chunks": chunks, "filename": self.file.filename}
            
        except Exception as e:
            return {"success": False, "message": f"Error al cargar archivo: {str(e)}"}

    
