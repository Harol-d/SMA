from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

class ChunksService:
    """Servicio especializado en búsquedas semánticas"""
    def __init__(self,size,overlap):
        self.size = size
        self.overlap = overlap
    
    def crearChunks(self,documentos):
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.size,
                chunk_overlap=self.overlap,
                length_function=len
            )
        
            chunks = text_splitter.split_documents(documentos)
            return chunks
        except Exception as e:
            return {"success": False, "message": f"Error al crear chunks: {str(e)}"}
        