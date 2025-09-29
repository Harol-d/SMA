import pandas as pd
import re
import os
from pathlib import Path
from typing import Dict, Any, List

def normalize_excel_data(df: pd.DataFrame) -> pd.DataFrame:
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

def validate_excel_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """Valida la estructura del Excel y proporciona recomendaciones"""
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'recommendations': [],
        'column_mapping': {},
        'data_quality_score': 0
    }
    
    columns = df.columns.tolist()
    
    # Campos esperados y sus variantes (incluyendo formato Gantt)
    expected_fields = {
        'project': ['proyecto', 'project', 'nombre_proyecto', 'project_name', 'id'],
        'assignee': ['asignado', 'assignee', 'responsable', 'encargado'],
        'activity': ['actividad', 'activity', 'tarea', 'task'],
        'progress': ['progreso', 'progress', 'avance', 'porcentaje', 'completado'],
        'notes': ['notas', 'notes', 'comentarios', 'observaciones'],
        'dates': ['fecha', 'date', 'inicio', 'fin', 'start', 'end', 'timeline', 'duración', 'duration']
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

def extract_percentage(value: str) -> float:
    """Extrae porcentaje de un string"""
    if isinstance(value, (int, float)):
        return float(value)
    
    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%?', str(value))
    if numbers:
        return min(100, max(0, float(numbers[0])))
    return None

def test_excel_file(file_path: str, file_description: str):
    """Prueba un archivo Excel específico"""
    
    print(f"\n{'='*60}")
    print(f"PROBANDO: {file_description}")
    print(f"Archivo: {file_path}")
    print(f"{'='*60}")
    
    try:
        # 1. Leer Excel
        df = pd.read_excel(file_path)
        print(f"Excel leído exitosamente")
        print(f"  - Filas: {len(df)}")
        print(f"  - Columnas: {len(df.columns)}")
        print(f"  - Primeras columnas: {list(df.columns[:8])}")
        
        # 2. Normalizar datos
        df_clean = normalize_excel_data(df)
        print(f"Datos normalizados")
        print(f"  - Filas después de limpieza: {len(df_clean)}")
        
        # 3. Validar estructura
        validation = validate_excel_structure(df_clean)
        print(f"Estructura validada")
        print(f"  - Calidad de datos: {validation['data_quality_score']:.1f}%")
        print(f"  - Es válido para análisis: {'SÍ' if validation['is_valid'] else 'NO'}")
        print(f"  - Campos detectados: {len(validation['column_mapping'])}")
        
        if validation['warnings']:
            print(f"  Advertencias:")
            for warning in validation['warnings']:
                print(f"     - {warning}")
        
        if validation['recommendations']:
            print(f"  Recomendaciones:")
            for rec in validation['recommendations']:
                print(f"     - {rec}")
        
        # 4. Mostrar datos de ejemplo si hay contenido útil
        relevant_cols = [col for col in df_clean.columns if any(keyword in col.lower() 
                        for keyword in ['id', 'proyecto', 'tarea', 'asignado', 'progreso', 'estado', 'notas'])]
        
        if relevant_cols and len(df_clean) > 0:
            print(f"Datos de ejemplo encontrados:")
            sample_rows = min(2, len(df_clean))
            
            for i in range(sample_rows):
                if i < len(df_clean):
                    row = df_clean.iloc[i]
                    print(f"  --- Fila {i+1} ---")
                    for col in relevant_cols[:6]:  # Limitar a 6 columnas
                        if col in row.index:
                            value = str(row[col]).strip() if pd.notna(row[col]) else ''
                            if value and value != 'nan':
                                print(f"    {col}: {value}")
                                
                                # Probar extracción de porcentaje
                                if 'progreso' in col.lower():
                                    percentage = extract_percentage(value)
                                    if percentage is not None:
                                        print(f"      -> Porcentaje: {percentage}%")
        
        # 5. Resumen del resultado
        print(f"\nRESUMEN DE {file_description.upper()}:")
        if validation['data_quality_score'] >= 70:
            print(f"  EXCELENTE - Listo para análisis completo")
        elif validation['data_quality_score'] >= 40:
            print(f"  BUENO - Análisis parcial posible")
        elif validation['data_quality_score'] >= 20:
            print(f"  BÁSICO - Análisis limitado")
        else:
            print(f"  INSUFICIENTE - Requiere más datos")
        
        return {
            'success': True,
            'quality_score': validation['data_quality_score'],
            'is_valid': validation['is_valid'],
            'rows': len(df_clean),
            'columns': len(df_clean.columns)
        }
        
    except Exception as e:
        print(f"ERROR procesando archivo:")
        print(f"   {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Ejecuta pruebas completas del sistema"""
    
    print("INICIANDO PRUEBAS COMPLETAS DEL SISTEMA SMA")
    print("=" * 80)
    
    # Obtener la ruta base del proyecto de forma robusta
    current_dir = Path(__file__).parent  # backend/tests/
    project_root = current_dir.parent.parent  # SMA/
    excel_files_dir = project_root / "data" / "excel_files"
    
    print(f"Directorio actual: {current_dir}")
    print(f"Directorio de archivos Excel: {excel_files_dir}")
    print(f"¿Directorio existe?: {excel_files_dir.exists()}")
    
    # Archivos a probar (rutas absolutas y robustas)
    test_files = [
        {
            'path': str(excel_files_dir / 'SMA_Lector.xlsx'),
            'description': 'Excel Original (Vacío/Plantilla)'
        },
        {
            'path': str(excel_files_dir / 'SMA_Lector_Gantt.xlsx'), 
            'description': 'Excel con Formato Gantt'
        },
        {
            'path': str(excel_files_dir / 'SMA_Lector_Pruebas.xlsx'),
            'description': 'Excel con Datos Planos'
        }
    ]
    
    # Verificar que todos los archivos existen antes de proceder
    print(f"\nVerificando existencia de archivos:")
    for test_file in test_files:
        file_path = Path(test_file['path'])
        exists = file_path.exists()
        print(f"  {test_file['description']}: {'✓' if exists else '✗'} ({test_file['path']})")
        if not exists:
            print(f"    ADVERTENCIA: Archivo no encontrado")
    print()
    
    results = []
    
    # Probar cada archivo
    for test_file in test_files:
        result = test_excel_file(test_file['path'], test_file['description'])
        result['file'] = test_file['description']
        results.append(result)
    
    # Resumen final
    print(f"\n{'='*80}")
    print("RESUMEN FINAL DE PRUEBAS")
    print(f"{'='*80}")
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"Archivos procesados exitosamente: {len(successful_tests)}/3")
    print(f"Archivos con errores: {len(failed_tests)}/3")
    
    if successful_tests:
        print(f"\nCALIDAD DE DATOS:")
        for result in successful_tests:
            if 'quality_score' in result:
                status = "EXCELENTE" if result['quality_score'] >= 70 else "BUENO" if result['quality_score'] >= 40 else "BASICO" if result['quality_score'] >= 20 else "INSUFICIENTE"
                print(f"  {result['file']}: {result['quality_score']:.1f}% - {status}")
    
    if failed_tests:
        print(f"\nERRORES ENCONTRADOS:")
        for result in failed_tests:
            print(f"  {result['file']}: {result.get('error', 'Error desconocido')}")
    
    # Conclusión
    print(f"\nCONCLUSIÓN:")
    if len(successful_tests) == 3:
        print("  SISTEMA COMPLETAMENTE FUNCIONAL")
        print("  La aplicación puede procesar todos los formatos de Excel")
        print("  Manejo robusto de datos vacíos y completos")
        print("  Validación inteligente y recomendaciones útiles")
    elif len(successful_tests) >= 2:
        print("  SISTEMA MAYORMENTE FUNCIONAL")
        print("  La mayoría de archivos se procesan correctamente")
    else:
        print("  SISTEMA REQUIERE ATENCIÓN")
        print("  Revisar configuración y dependencias")
    
    return results

if __name__ == "__main__":
    results = main()
