from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from Config.dataBaseConfig import PineconeConfig
# import uuid


class databaseVectormodel (PineconeConfig):
    def __init__(self):
        super().__init__() 
        self.pinecone = Pinecone(api_key=self.PINECONE_API_KEY)
    
    def agregarRecords(self, chunks: list):
        resultado = PineconeVectorStore.from_documents(
        chunks,
        embedding=self.model,
        index_name=self.INDEX)
        return resultado
    
    def eliminarRecords(self):
        index = self.pinecone.Index(self.INDEX)
        index.delete(delete_all=True)
        return {
            "success": True,
            "message": "Chunks eliminados correctamente"
        }
    
    def consultarRecords(self):
        # Usar búsqueda semántica con Gemini
        vstore = PineconeVectorStore.from_existing_index(index_name=self.INDEX, embedding=self.model)
        print(vstore)
        return vstore