from pickletools import read_uint1
from app.services.FileUploadService import FileUploadService

class fileController:
    def __init__(self,file: dict):
        self.file = file.get("file")
        self.validate = False
        self.file_service = FileUploadService()

    def cargarArchivo(self):
        self.validate = self.file_service.validateFile(self.file)
        if self.validate:
            return self.file_service.ArchiveToChunks(self.file)
        else:
            return self.validate

