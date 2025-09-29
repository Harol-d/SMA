"""
Servicio de procesamiento de archivos Excel
Maneja la carga, validación y procesamiento de archivos Excel para análisis de proyectos
"""

import os
import pandas as pd
import numpy as np
import uuid
import re
from typing import Dict, Any, List
from werkzeug.utils import secure_filename


class ExcelProcessingService:
    """Servicio especializado en procesamiento de archivos Excel"""
    
    def __init__(self):
        self.allowed_extensions = {'xlsx', 'xls'}
        self.upload_folder = 'uploads'
    
    def allowed_file(self, filename: str) -> bool:
        """Verifica si el archivo tiene una extensión permitida"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def normalize_excel_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza y limpia los datos del DataFrame de Excel"""
        df_clean = df.copy()
        
        # Eliminar filas completamente vacías
        df_clean = df_clean.dropna(how='all')
        
        # Reemplazar valores NaN con cadenas vacías
        df_clean = df_clean.fillna('')
        
        # Limpiar strings y normalizar
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                df_clean[col] = df_clean[col].astype(str).str.strip()
                # Reemplazar valores que pandas convierte a 'nan' string
                df_clean[col] = df_clean[col].replace(['nan', 'NaN', 'None', 'null'], '')
        
        return df_clean
    
    def validate_excel_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida la estructura del Excel y proporciona recomendaciones"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'recommendations': [],
            'column_mapping': {},
            'data_quality_score': 0
        }
        
        columns = df.columns.tolist()
        
        # Campos esperados y sus variantes
        expected_fields = {
            'project': ['proyecto', 'project', 'nombre_proyecto', 'project_name'],
            'assignee': ['asignado', 'assignee', 'responsable', 'encargado'],
            'activity': ['actividad', 'activity', 'tarea', 'task'],
            'progress': ['progreso', 'progress', 'avance', 'porcentaje', 'completado'],
            'notes': ['notas', 'notes', 'comentarios', 'observaciones'],
            'dates': ['fecha', 'date', 'inicio', 'fin', 'start', 'end', 'timeline']
        }
        
        # Verificar qué campos tenemos
        found_fields = {}
        for field_type, variants in expected_fields.items():
            for col in columns:
                col_lower = col.lower().strip()
                if any(variant in col_lower for variant in variants):
                    if field_type not in found_fields:
                        found_fields[field_type] = []
                    found_fields[field_type].append(col)
                    validation_result['column_mapping'][col] = field_type
        
        # Evaluar calidad
        critical_fields = ['project', 'assignee', 'activity']
        missing_critical = [field for field in critical_fields if field not in found_fields]
        
        if missing_critical:
            validation_result['warnings'].append(
                f"Faltan campos críticos: {missing_critical}"
            )
            validation_result['recommendations'].append(
                f"Agregar columnas para: {', '.join(missing_critical)}"
            )
        
        if 'progress' not in found_fields:
            validation_result['warnings'].append("No se encontró información de progreso")
            validation_result['recommendations'].append(
                "Agregar columna de progreso (ej: 'Progreso', 'Avance', 'Porcentaje')"
            )
        
        # Calcular puntuación de calidad
        total_expected = len(expected_fields)
        found_count = len(found_fields)
        validation_result['data_quality_score'] = (found_count / total_expected) * 100
        
        if validation_result['data_quality_score'] < 30:
            validation_result['is_valid'] = False
            validation_result['warnings'].append(
                "Estructura de datos insuficiente para análisis completo"
            )
        
        return validation_result
    
    def extract_percentage(self, value: str) -> float:
        """Extrae porcentaje de un string"""
        if isinstance(value, (int, float)):
            return float(value)
        
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%?', str(value))
        if numbers:
            return min(100, max(0, float(numbers[0])))
        return None
    
    def analyze_delays_in_notes(self, notes: str) -> List[str]:
        """Analiza las notas para identificar razones de atrasos"""
        delay_indicators = [
            'atraso', 'retraso', 'delay', 'pendiente', 'problema', 'issue',
            'bloqueado', 'blocked', 'esperando', 'waiting', 'falta', 'missing',
            'cancelado', 'cancelled', 'pospuesto', 'postponed'
        ]
        
        reasons = []
        sentences = notes.split('.')
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in delay_indicators):
                reason = sentence.strip()
                if len(reason) > 10:
                    reasons.append(reason)
        
        return reasons
    
    def extract_pending_tasks(self, notes: str) -> List[str]:
        """Extrae tareas pendientes de las notas"""
        pending_indicators = [
            'pendiente', 'pending', 'por hacer', 'to do', 'falta', 'missing',
            'revisar', 'review', 'completar', 'complete', 'terminar', 'finish'
        ]
        
        tasks = []
        sentences = notes.replace(',', '.').split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in pending_indicators):
                if len(sentence) > 10:
                    tasks.append(sentence)
        
        return tasks
    
    def extract_project_data(self, row: pd.Series, columns: List[str]) -> Dict[str, Any]:
        """Extrae información estructurada de proyectos de una fila del Excel"""
        project_data = {
            'assignee': None,
            'project_name': None,
            'activity_name': None,
            'progress_percentage': None,
            'notes': None,
            'timeline_start': None,
            'timeline_end': None,
            'status': 'unknown',
            'is_delayed': False,
            'pending_tasks': [],
            'delay_reasons': [],
            'data_quality': 'complete',
            'missing_fields': [],
            'warnings': []
        }
        
        # Campos reconocidos automáticamente
        assignee_fields = ['asignado', 'assignee', 'responsable', 'encargado']
        project_fields = ['proyecto', 'project', 'nombre_proyecto']
        activity_fields = ['actividad', 'activity', 'tarea', 'task']
        progress_fields = ['progreso', 'progress', 'avance', 'porcentaje', 'completado']
        notes_fields = ['notas', 'notes', 'comentarios', 'observaciones']
        date_fields = ['fecha_inicio', 'fecha_fin', 'start_date', 'end_date', 'timeline']
        
        # Procesar cada columna
        for col in columns:
            col_lower = col.lower().strip()
            value = str(row[col]).strip() if pd.notna(row[col]) else ''
            
            # Validar que el valor no esté vacío
            is_valid_value = value and value not in ['', 'nan', 'NaN', 'None', 'null']
            
            if is_valid_value:
                if any(field in col_lower for field in assignee_fields):
                    project_data['assignee'] = value
                elif any(field in col_lower for field in project_fields):
                    project_data['project_name'] = value
                elif any(field in col_lower for field in activity_fields):
                    project_data['activity_name'] = value
                elif any(field in col_lower for field in progress_fields):
                    progress = self.extract_percentage(value)
                    if progress is not None:
                        project_data['progress_percentage'] = progress
                        if progress < 50:
                            project_data['status'] = 'delayed'
                            project_data['is_delayed'] = True
                        elif progress < 80:
                            project_data['status'] = 'at_risk'
                        else:
                            project_data['status'] = 'on_track'
                    else:
                        project_data['warnings'].append(f'Valor de progreso no válido: {value}')
                elif any(field in col_lower for field in notes_fields):
                    project_data['notes'] = value
                    project_data['delay_reasons'] = self.analyze_delays_in_notes(value)
                    project_data['pending_tasks'] = self.extract_pending_tasks(value)
                elif any(field in col_lower for field in date_fields):
                    if 'inicio' in col_lower or 'start' in col_lower:
                        project_data['timeline_start'] = value
                    elif 'fin' in col_lower or 'end' in col_lower:
                        project_data['timeline_end'] = value
            else:
                # Registrar campos vacíos importantes
                if any(field in col_lower for field in assignee_fields + project_fields + activity_fields):
                    project_data['missing_fields'].append(col)
        
        # Evaluar calidad de datos
        critical_fields = ['project_name', 'assignee', 'activity_name']
        missing_critical = [field for field in critical_fields if not project_data[field]]
        
        if len(missing_critical) >= 2:
            project_data['data_quality'] = 'poor'
            project_data['warnings'].append(f'Faltan campos críticos: {missing_critical}')
        elif len(missing_critical) == 1:
            project_data['data_quality'] = 'partial'
            project_data['warnings'].append(f'Falta campo crítico: {missing_critical[0]}')
        
        if not project_data['progress_percentage']:
            project_data['warnings'].append('Sin información de progreso')
        
        return project_data
    
    def create_project_text(self, row: pd.Series, columns: List[str], project_data: Dict[str, Any]) -> str:
        """Crea texto descriptivo para análisis de proyectos"""
        parts = []
        
        # Información básica del proyecto
        if project_data['project_name']:
            parts.append(f"Proyecto: {project_data['project_name']}")
        else:
            parts.append("Proyecto: [No especificado]")
            
        if project_data['activity_name']:
            parts.append(f"Actividad: {project_data['activity_name']}")
        else:
            parts.append("Actividad: [No especificada]")
            
        if project_data['assignee']:
            parts.append(f"Asignado a: {project_data['assignee']}")
        else:
            parts.append("Asignado a: [No asignado]")
        
        # Información de progreso
        if project_data['progress_percentage'] is not None:
            parts.append(f"Progreso: {project_data['progress_percentage']}%")
            parts.append(f"Estado: {project_data['status']}")
            if project_data['is_delayed']:
                parts.append("PROYECTO CON ATRASO IDENTIFICADO")
        else:
            parts.append("Progreso: [Sin información]")
            parts.append(f"Estado: {project_data['status']}")
        
        # Calidad de datos
        parts.append(f"Calidad de datos: {project_data['data_quality']}")
        
        # Advertencias si las hay
        if project_data['warnings']:
            parts.append("Advertencias:")
            for warning in project_data['warnings']:
                parts.append(f"- {warning}")
        
        # Campos faltantes
        if project_data['missing_fields']:
            parts.append(f"Campos faltantes: {', '.join(project_data['missing_fields'])}")
        
        # Notas e información adicional
        if project_data['notes']:
            parts.append(f"Notas: {project_data['notes']}")
        
        if project_data['delay_reasons']:
            parts.append("Razones de atraso:")
            for reason in project_data['delay_reasons']:
                parts.append(f"- {reason}")
        
        if project_data['pending_tasks']:
            parts.append("Tareas pendientes:")
            for task in project_data['pending_tasks']:
                parts.append(f"- {task}")
        
        context = "Información de seguimiento de proyecto. Análisis de avances, atrasos y gestión de tareas."
        return ". ".join(parts) + ". " + context
    
    def process_excel_to_vectors(self, file_path: str) -> List[Dict[str, Any]]:
        """Procesa un archivo Excel y convierte cada fila en datos para vectores"""
        try:
            df = pd.read_excel(file_path)
            
            # Validar estructura del Excel
            validation = self.validate_excel_structure(df)
            
            df_clean = self.normalize_excel_data(df)
            columns = df_clean.columns.tolist()
            vectors_data = []
            
            # Añadir información de validación al primer vector
            validation_info = {
                'id': f"validation_info_{uuid.uuid4().hex[:8]}",
                'text': f"Validación del archivo Excel: Calidad de datos {validation['data_quality_score']:.1f}%. "
                       f"Advertencias: {'. '.join(validation['warnings'])}. "
                       f"Recomendaciones: {'. '.join(validation['recommendations'])}.",
                'metadata': {
                    'file_source': str(os.path.basename(file_path)),
                    'analysis_type': 'file_validation',
                    'data_quality_score': float(validation['data_quality_score']),
                    'warnings_count': len(validation['warnings']),
                    'recommendations_count': len(validation['recommendations']),
                    'row_index': -1
                }
            }
            vectors_data.append(validation_info)
            
            # Procesar cada fila
            for index, row in df_clean.iterrows():
                project_data = self.extract_project_data(row, columns)
                descriptive_text = self.create_project_text(row, columns, project_data)
                
                # Crear metadata completo (solo campos compatibles con Pinecone)
                metadata = {}
                for col in columns:
                    metadata[col] = str(row[col]).strip() if pd.notna(row[col]) else ''
                
                # Agregar campos de project_data (solo los compatibles)
                metadata['assignee'] = str(project_data.get('assignee', '')) if project_data.get('assignee') else ''
                metadata['project_name'] = str(project_data.get('project_name', '')) if project_data.get('project_name') else ''
                metadata['activity_name'] = str(project_data.get('activity_name', '')) if project_data.get('activity_name') else ''
                metadata['progress_percentage'] = float(project_data.get('progress_percentage', 0)) if project_data.get('progress_percentage') is not None else 0.0
                metadata['notes'] = str(project_data.get('notes', '')) if project_data.get('notes') else ''
                metadata['status'] = str(project_data.get('status', '')) if project_data.get('status') else ''
                metadata['is_delayed'] = bool(project_data.get('is_delayed', False))
                metadata['data_quality'] = str(project_data.get('data_quality', '')) if project_data.get('data_quality') else ''
                
                metadata['row_index'] = int(index)
                metadata['file_source'] = str(os.path.basename(file_path))
                metadata['analysis_type'] = 'project_management'
                metadata['validation_score'] = float(validation['data_quality_score'])
                
                # Generar ID más robusto
                project_name = project_data.get('project_name', 'unknown')
                if not project_name or project_name == 'unknown':
                    project_name = f"row_{index}"
                
                vectors_data.append({
                    'id': f"project_{project_name}_{index}_{uuid.uuid4().hex[:8]}",
                    'text': descriptive_text,
                    'metadata': metadata
                })
            
            return vectors_data
            
        except Exception as e:
            # Proporcionar información más detallada sobre el error
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file_path': file_path,
                'suggestions': []
            }
            
            if 'No such file' in str(e):
                error_details['suggestions'].append('Verificar que el archivo existe en la ruta especificada')
            elif 'Excel' in str(e) or 'openpyxl' in str(e):
                error_details['suggestions'].append('Verificar que el archivo sea un Excel válido (.xlsx o .xls)')
            elif 'Permission' in str(e):
                error_details['suggestions'].append('Cerrar el archivo Excel si está abierto y volver a intentar')
            
            raise Exception(f"Error procesando archivo Excel: {error_details}")
