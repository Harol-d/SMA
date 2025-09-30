from pinecone import Pinecone
#from langchain_pinecone import PineconeVectorStore
from Config.dataBaseConfig import PineconeConfig
import uuid


class databaseVectormodel (PineconeConfig):
    def __init__(self):
        super().__init__() 
        self.pinecone = Pinecone(api_key=self.PINECONE_API_KEY)
        self.record = "smaccb-pruebas1024"

    def agregarRecords(self, chunks: str):
        # Convertir chunks a formato de vectores para usar Gemini
        vectors = []
        for i, chunk in enumerate(chunks):
            vectors.append({
                'id': f"chunk_{i}_{uuid.uuid4().hex[:8]}",
                'text': chunk.page_content,
                'metadata': chunk.metadata
            })
            print(vectors)
        
        return self.upsert_vectors(vectors)
    
    def eliminarRecords(self):
        index = self.pinecone.Index(self.record)
        index.delete(delete_all=True)

        return {
            "success": True,
            "message": "Chunks eliminados correctamente"
        }
    
    def consultarRecords(self, pregunta: str):
        # Usar búsqueda semántica con Gemini
        search_result = self.search_similar_vectors(pregunta, 20)
        if search_result["success"]:
            # Convertir formato para compatibilidad
            context = []
            for result in search_result["results"]:
                context.append(type('Document', (), {
                    'page_content': result['metadata'].get('text', ''),
                    'metadata': result['metadata']
                })())
            return context