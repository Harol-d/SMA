# Funcion Normalize_text - Ayuda de DeepSeek
    # def normalize_text(self, text: str) -> str:
    #     """Normaliza y limpia texto"""
    #     if not text:
    #         return ""
        
    #     # Eliminar caracteres extraños y normalizar espacios
    #     text = re.sub(r'\s+', ' ', text.strip())
    #     # Esto Elimina los caracteres no ASCII
    #     text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    #     return text
"""
Servicio de conversión de documentos a JSON
Convierte archivos XLS, XLSX y PDF a formato JSON para embeddings
"""

import os
import pandas as pd
import json
import uuid
import re
from typing import Dict, Any, List
from datetime import datetime
import pdfplumber
from werkzeug.utils import secure_filename


class ConvertDocJSON:
    """Servicio especializado en convertir documentos a JSON para embeddings"""
    
    def __init__(self):
        self.allowed_extensions = {'xlsx', 'xls', 'pdf'}
        self.upload_folder = 'uploads'
        
    def allowed_file(self, filename: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def normalize_text(self, text: str) -> str:
        """Normaliza y limpia texto"""
        if not text:
            return ""
        
        # Eliminar caracteres extraños y normalizar espacios
        text = re.sub(r'\s+', ' ', text.strip())
        # Eliminar caracteres no ASCII
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        return text
    
    def extract_pdf_text(self, file_path: str) -> Dict[str, Any]:
        """Extrae texto de archivos PDF usando pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                pdf_data = {
                    'metadata': {
                        'total_pages': len(pdf.pages),
                        'author': pdf.metadata.get('Author', ''),
                        'title': pdf.metadata.get('Title', ''),
                        'subject': pdf.metadata.get('Subject', ''),
                        'creator': pdf.metadata.get('Creator', ''),
                        'producer': pdf.metadata.get('Producer', ''),
                        'creation_date': pdf.metadata.get('CreationDate', '')
                    },
                    'pages': []
                }
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    normalized_text = self.normalize_text(page_text)
                    
                    page_data = {
                        'page_number': page_num + 1,
                        'text': normalized_text,
                        'word_count': len(normalized_text.split()),
                        'char_count': len(normalized_text),
                        'page_size': {
                            'width': page.width,
                            'height': page.height
                        }
                    }
                    pdf_data['pages'].append(page_data)
                
                return pdf_data
                
        except Exception as e:
            raise Exception(f"Error extrayendo texto del PDF: {str(e)}")
    
    def extract_excel_data(self, file_path: str) -> Dict[str, Any]:
        """Extrae datos de archivos Excel - ADAPTADO para estructura de vectores"""
        try:
            df = pd.read_excel(file_path)
            
            # Normalizar datos (similar a tu servicio original)
            df_clean = df.fillna('')
            
            # Eliminar filas completamente vacías
            df_clean = df_clean.dropna(how='all')
            
            # Limpiar strings
            for col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].astype(str).str.strip()
                    df_clean[col] = df_clean[col].replace(['nan', 'NaN', 'None', 'null'], '')
            
            excel_data = {
                'metadata': {
                    'total_sheets': 1,  # Simplificado para una hoja
                    'sheet_names': ['Sheet1'],
                    'file_type': 'excel'
                },
                'sheets': {
                    'Sheet1': {
                        'sheet_name': 'Sheet1',
                        'columns': df_clean.columns.tolist(),
                        'row_count': len(df_clean),
                        'column_count': len(df_clean.columns),
                        'data': []
                    }
                }
            }
            
            # Convertir cada fila a diccionario
            for index, row in df_clean.iterrows():
                row_data = {
                    'row_index': int(index),
                    'cells': {},
                    'non_empty_cells': 0
                }
                
                for col in df_clean.columns:
                    value = str(row[col]).strip()
                    row_data['cells'][col] = value
                    if value and value not in ['', 'nan', 'NaN', 'None', 'null']:
                        row_data['non_empty_cells'] += 1
                
                excel_data['sheets']['Sheet1']['data'].append(row_data)
            
            return excel_data
            
        except Exception as e:
            raise Exception(f"Error extrayendo datos de Excel: {str(e)}")
    
    def validate_document_structure(self, file_path: str) -> Dict[str, Any]:
        """Valida la estructura del documento - SIMILAR a tu servicio original"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'recommendations': [],
            'data_quality_score': 0
        }
        
        file_extension = file_path.rsplit('.', 1)[1].lower()
        
        try:
            if file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
                columns = df.columns.tolist()
                
                # Verificar si hay datos
                if len(df) == 0:
                    validation_result['warnings'].append("El archivo está vacío")
                    validation_result['is_valid'] = False
                
                # Calcular calidad de datos
                total_cells = len(df) * len(columns)
                if total_cells > 0:
                    non_empty_cells = df.count().sum()
                    validation_result['data_quality_score'] = (non_empty_cells / total_cells) * 100
                
            elif file_extension == 'pdf':
                with pdfplumber.open(file_path) as pdf:
                    # Validar que tenga texto
                    sample_text = ""
                    for page in pdf.pages[:2]:
                        sample_text += page.extract_text() or ""
                    
                    if len(sample_text.strip()) < 10:
                        validation_result['warnings'].append("PDF con poco texto extraíble")
                        validation_result['data_quality_score'] = 30
                    else:
                        validation_result['data_quality_score'] = 80
            
            return validation_result
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['warnings'].append(f"Error validando: {str(e)}")
            return validation_result
    
    def process_document_to_vectors(self, file_path: str) -> List[Dict[str, Any]]:
        """Procesa documento y devuelve datos para vectores - COMPATIBLE con tu servicio original"""
        try:
            # Validar estructura
            validation = self.validate_document_structure(file_path)
            
            vectors_data = []
            file_extension = file_path.rsplit('.', 1)[1].lower()
            
            # Información de validación (similar a tu servicio original)
            validation_info = {
                'id': f"validation_info_{uuid.uuid4().hex[:8]}",
                'text': f"Validación del archivo: Calidad de datos {validation['data_quality_score']:.1f}%. "
                       f"Advertencias: {'. '.join(validation['warnings'])}.",
                'metadata': {
                    'file_source': str(os.path.basename(file_path)),
                    'analysis_type': 'file_validation',
                    'data_quality_score': float(validation['data_quality_score']),
                    'warnings_count': len(validation['warnings']),
                    'row_index': -1
                }
            }
            vectors_data.append(validation_info)
            
            # Procesar según tipo de archivo
            if file_extension in ['xlsx', 'xls']:
                content_data = self.extract_excel_data(file_path)
                
                for sheet_name, sheet_info in content_data['sheets'].items():
                    for row in sheet_info['data']:
                        # Crear texto descriptivo (similar a tu servicio original)
                        text_parts = []
                        for col_name, cell_value in row['cells'].items():
                            if cell_value and cell_value != '':
                                text_parts.append(f"{col_name}: {cell_value}")
                        
                        if text_parts:  # Solo si hay datos
                            descriptive_text = f"Fila {row['row_index']}: {'. '.join(text_parts)}"
                            
                            vector_data = {
                                'id': f"excel_{os.path.basename(file_path)}_{row['row_index']}_{uuid.uuid4().hex[:8]}",
                                'text': descriptive_text,
                                'metadata': {
                                    'file_source': str(os.path.basename(file_path)),
                                    'analysis_type': 'excel_data',
                                    'row_index': row['row_index'],
                                    'non_empty_cells': row['non_empty_cells']
                                }
                            }
                            vectors_data.append(vector_data)
            
            elif file_extension == 'pdf':
                content_data = self.extract_pdf_text(file_path)
                
                for page in content_data['pages']:
                    if page['text']:
                        vector_data = {
                            'id': f"pdf_{os.path.basename(file_path)}_page_{page['page_number']}_{uuid.uuid4().hex[:8]}",
                            'text': page['text'],
                            'metadata': {
                                'file_source': str(os.path.basename(file_path)),
                                'analysis_type': 'pdf_content',
                                'page_number': page['page_number'],
                                'word_count': page['word_count']
                            }
                        }
                        vectors_data.append(vector_data)
            
            return vectors_data
            
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file_path': file_path
            }
            
            if 'No such file' in str(e):
                error_details['suggestions'] = ['Verificar que el archivo existe']
            elif 'Excel' in str(e):
                error_details['suggestions'] = ['Verificar que sea un Excel válido']
            elif 'PDF' in str(e):
                error_details['suggestions'] = ['Verificar que sea un PDF válido']
            
            raise Exception(f"Error procesando documento: {error_details}")


# Para mantener compatibilidad con el código existente
def process_document(file_path: str) -> Dict[str, Any]:
    """Función de compatibilidad para reemplazar process_excel_to_vectors"""
    converter = ConvertDocJSON()
    try:
        vectors_data = converter.process_document_to_vectors(file_path)
        return vectors_data
    except Exception as e:
        raise e