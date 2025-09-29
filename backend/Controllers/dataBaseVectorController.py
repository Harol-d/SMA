from Models.databaseVectorModel import databaseVectormodel
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader


class dataBaseVectorController:
    def __init__(self):
        self.model = databaseVectormodel()
    
    def crearChunks(self, doc: str):
        # Cargar documento con codificación UTF-8 (estándar universal)
        loader = TextLoader(doc, encoding='utf-8')  
        documents = loader.load()

        # Configurar divisor de texto para crear chunks manejables
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=8000,  # Tamaño del chunk en caracteres
            chunk_overlap=500,  # Superposición entre chunks para mantener contexto
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        self.model.agregarRecords(chunks)
        

    def obtenerRecords(self, pregunta: str):
        return self.model.consultarRecords(pregunta)
    
    def obtener_metricas_dashboard(self):
        """
        Obtiene métricas consolidadas para el dashboard
        
        Returns:
            Diccionario con métricas del dashboard
        """
        return self.model.get_dashboard_metrics()