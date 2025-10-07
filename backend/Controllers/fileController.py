from app.services.FileUploadService import FileUploadService
from app.services.Chunk_service import ChunksService


class fileController:
    def __init__(self, archivo):
        self.file = archivo
        self.file_service = FileUploadService()
        self.chunk = ChunksService(size=5000, overlap=20)
        self.route = "uploads"

    def cargarArchivo(self):
            # Validar el archivo
        validate = self.file_service.validateFile(self.file)
        if validate['success']:
            self.route = self.file_service.guardarArchivo(self.file, self.route)
            chunks = self.chunk.ArchiveToChunks(self.route)
            return chunks
            
        return validate

    
