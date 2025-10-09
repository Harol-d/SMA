from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
import pandas as pd
import os

class ChunksService:
    """Servicio especializado en búsquedas semánticas"""
    def __init__(self,size,overlap):
        self.size = size
        self.overlap = overlap
    
        
    def ArchiveToChunks(self, route: str):
        """Convierte archivos Excel, PDF, Word y texto a chunks directamente desde FileStorage"""
        try:
            file_extension = os.path.splitext(route)[1].lower()
            
            if file_extension == '.pdf':
                return self._process_pdf(route)
            elif file_extension in ['.xlsx', '.xls']:
                return self._process_excel(route)
            elif file_extension in ['.docx', '.doc']:
                return self._process_word(route)
            elif file_extension == '.txt':
                return self._process_text(route)
            else:
                raise Exception(f"Tipo de archivo no soportado: {file_extension}")
                
        except Exception as e:
            return e
    
    def _process_pdf(self, route: str):
        """Procesa archivos PDF usando PyPDFLoader"""
        loader = PyPDFLoader(route)
        documentos = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.size,
            chunk_overlap=self.overlap,
            length_function=len
        )
        chunks = text_splitter.split_documents(documentos)
        return chunks
    
    def _process_excel(self, route: str):
        """Procesa archivos Excel de forma simple con Pandas"""
        try:
            # Leer archivo Excel
            df = pd.read_excel(route)
            
            # Limpiar datos básicos
            df = df.fillna('')
            df = df.dropna(how='all')
            
            # Convertir a texto simple
            chunks = []
            for index, row in df.iterrows():
                # Crear texto simple de la fila
                row_text = ""
                for col in df.columns:
                    value = str(row[col]).strip()
                    if value and value != '':
                        row_text += f"{col}: {value}. "
                
                if row_text.strip():
                    # Crear documento langchain simple
                    doc = Document(
                        page_content=row_text.strip(),
                        metadata={
                            'source': os.path.basename(route),
                            'row_index': index,
                            'file_type': 'excel'
                        }
                    )
                    chunks.append(doc)
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Error procesando archivo Excel: {str(e)}")
    
    def _process_word(self, route: str):
        """Procesa archivos Word usando python-docx"""
        try:
            from docx import Document as DocxDocument
            
            # Leer archivo Word
            doc = DocxDocument(route)
            
            # Extraer texto de todos los párrafos
            chunks = []
            for i, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text:
                    # Crear documento langchain simple
                    from langchain.schema import Document as LangChainDocument
                    doc_chunk = LangChainDocument(
                        page_content=text,
                        metadata={
                            'source': os.path.basename(route),
                            'paragraph_index': i,
                            'file_type': 'word'
                        }
                    )
                    chunks.append(doc_chunk)
            
            return chunks
            
        except ImportError:
            raise Exception("python-docx no está instalado. Instálalo con: pip install python-docx")
        except Exception as e:
            raise Exception(f"Error procesando archivo Word: {str(e)}")
    
    def _process_text(self, route: str):
        """Procesa archivos de texto plano"""
        try:
            with open(route, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Dividir el contenido en chunks usando el text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.size,
                chunk_overlap=self.overlap,
                length_function=len
            )
            
            # Crear un documento temporal para dividir
            from langchain.schema import Document as LangChainDocument
            temp_doc = LangChainDocument(page_content=content, metadata={'source': os.path.basename(route)})
            chunks = text_splitter.split_documents([temp_doc])
            
            # Actualizar metadata para cada chunk
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'file_type': 'text',
                    'chunk_index': i
                })
            
            return chunks
            
        except Exception as e:
            raise Exception(f"Error procesando archivo de texto: {str(e)}")
        