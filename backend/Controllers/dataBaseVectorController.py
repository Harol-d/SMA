from Models.databaseVectorModel import databaseVectormodel
class dataBaseVectorController:
    def __init__(self):
        self.dbvector = databaseVectormodel()
    
    def insertarChunks(self, chunks: list):
        print(chunks)
        response = self.dbvector.agregarRecords(chunks)
        return response

    def eliminarchunks(self):
        response = self.dbvector.eliminarRecords()
        return response

    def buscarSimilitud(self, pregunta: str):
        record = self.dbvector.consultarRecords()
        print(record)
        response = record.similarity_search(query=pregunta,k=5)
        return response