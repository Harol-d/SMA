from app.services.Chunk_service import ChunksService
from langchain_community.document_loaders import TextLoader
class FileUploadService:
    def __init__(self):
        self.chunk = ChunksService(size=5000, overlap=20)
    
    def validateFile(self,file: str):
        try:
            if not file.strip():
                raise ValueError("Error: No se ha proporcionado un archivo.")
        
            if file.strip() == "":
                    raise ValueError(f"Error: El campo {file} no puede estar vacío.")
            
            file = file.strip()
            validate = True
            return validate
        except (ValueError) as e:
            return {
            "success": False,
            "message": f"Error el archivo no es valido: {str(e)}",
            "recommendations": ["Seleccionar un archivo válido"]
        }

    def ArchiveToChunks(self,file: str):
        loader = TextLoader(file, encoding='utf-8')
        documentos = loader.load()
        chunks = self.chunk.crearChunks(documentos)
        return chunks

