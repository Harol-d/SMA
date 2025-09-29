#!/usr/bin/env python3
"""
Script de prueba específico para verificar la integración entre Excel y LLM
Ejecutar: python test_excel_integration.py
"""

import requests
import json
import sys
import os

# Configuración
BASE_URL = "http://127.0.0.1:5000"
CHAT_ENDPOINT = f"{BASE_URL}/api/ask/SMA-Agent"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/upload_excel"
DASHBOARD_ENDPOINT = f"{BASE_URL}/api/dashboard"

def test_excel_upload():
    """Prueba la carga de un archivo Excel"""
    print("PRUEBA 1: Carga de archivo Excel")
    print("="*50)
    
    # Buscar archivo Excel de prueba
    excel_files = [
        "SMA_Lector_Gantt.xlsx",
        "SMA_Lector.xlsx", 
        "SMA_Lector_Pruebas.xlsx"
    ]
    
    excel_path = None
    for file in excel_files:
        if os.path.exists(f"../data/excel_files/{file}"):
            excel_path = f"../data/excel_files/{file}"
            break
        elif os.path.exists(f"uploads/{file}"):
            excel_path = f"uploads/{file}"
            break
    
    if not excel_path:
        print("ERROR: No se encontro archivo Excel de prueba")
        return False
    
    print(f"Usando archivo: {excel_path}")
    
    try:
        with open(excel_path, 'rb') as f:
            files = {'file': (os.path.basename(excel_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(UPLOAD_ENDPOINT, files=files, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Archivo cargado exitosamente:")
            print(f"   - success: {data.get('success', 'N/A')}")
            print(f"   - filename: {data.get('data', {}).get('filename', 'N/A')}")
            print(f"   - rows_processed: {data.get('data', {}).get('rows_processed', 'N/A')}")
            print(f"   - vectors_created: {data.get('data', {}).get('vectors_created', 'N/A')}")
            return True
        else:
            print(f"ERROR {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_dashboard_after_upload():
    """Verifica que el dashboard muestre datos después de la carga"""
    print("\nPRUEBA 2: Verificacion del dashboard")
    print("="*50)
    
    try:
        response = requests.get(DASHBOARD_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Dashboard accesible:")
            print(f"   - success: {data.get('success', 'N/A')}")
            print(f"   - total_vectors: {data.get('total_vectors', 'N/A')}")
            
            if data.get('total_vectors', 0) > 0:
                print("SUCCESS: Datos vectorizados disponibles")
                return True
            else:
                print("WARNING: No hay vectores en la base de datos")
                return False
        else:
            print(f"ERROR {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_chat_with_excel_data():
    """Prueba consultas específicas que requieren datos del Excel"""
    print("\n PRUEBA 3: Consultas con datos Excel")
    print("="*50)
    
    test_queries = [
        "¿Qué proyectos están disponibles en el sistema?",
        "Dame un resumen de los proyectos cargados",
        "¿Cuáles son las actividades con mayor progreso?",
        "¿Qué personas están asignadas a proyectos?",
        "¿Hay algún proyecto atrasado?"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n Consulta {i}: {query}")
        
        payload = {
            "text": query,
            "conversationId": f"test_excel_{i}",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('content', '')
                
                # Verificar si la respuesta indica acceso a datos
                has_data_indicators = any(indicator in content.lower() for indicator in [
                    'proyecto', 'actividad', 'asignado', 'progreso', 'datos', 'información',
                    'sistema', 'cargado', 'disponible', 'encontrado'
                ])
                
                no_data_indicators = any(indicator in content.lower() for indicator in [
                    'no puedo ver', 'no tengo acceso', 'archivo adjunto', 'proporcionar datos',
                    'no hay información', 'sin datos', 'cargar archivo'
                ])
                
                if no_data_indicators:
                    print(" Respuesta indica falta de acceso a datos")
                    results.append('no_data')
                elif has_data_indicators:
                    print(" Respuesta indica acceso a datos del Excel")
                    print(f"    Longitud de respuesta: {len(content)} caracteres")
                    results.append('success')
                else:
                    print(" Respuesta ambigua - verificar contenido")
                    print(f"    Preview: {content[:100]}...")
                    results.append('ambiguous')
            else:
                print(f" Error {response.status_code}")
                results.append('error')
                
        except Exception as e:
            print(f" Error: {str(e)}")
            results.append('error')
    
    # Resumen
    success_count = results.count('success')
    no_data_count = results.count('no_data')
    ambiguous_count = results.count('ambiguous')
    error_count = results.count('error')
    
    print(f"\n Resumen de consultas:")
    print(f"   - Con datos: {success_count}/{len(test_queries)}")
    print(f"   - Sin datos: {no_data_count}/{len(test_queries)}")
    print(f"   - Ambiguas: {ambiguous_count}/{len(test_queries)}")
    print(f"   - Errores: {error_count}/{len(test_queries)}")
    
    return success_count > 0

def main():
    """Función principal de pruebas"""
    print("SCRIPT DE PRUEBA DE INTEGRACION EXCEL-LLM")
    print("="*60)
    print("Este script verifica que el LLM pueda acceder a datos del Excel")
    print("="*60)
    
    # Ejecutar pruebas
    tests_passed = 0
    total_tests = 3
    
    if test_excel_upload():
        tests_passed += 1
    
    if test_dashboard_after_upload():
        tests_passed += 1
    
    if test_chat_with_excel_data():
        tests_passed += 1
    
    # Resultado final
    print(f"\n{'='*60}")
    print(f" RESULTADO FINAL: {tests_passed}/{total_tests} pruebas exitosas")
    
    if tests_passed == total_tests:
        print(" ¡Integración Excel-LLM funcionando correctamente!")
        print("\n PRÓXIMOS PASOS:")
        print("   1. El sistema ahora puede acceder a datos del Excel")
        print("   2. Haz consultas específicas sobre tus proyectos")
        print("   3. La IA responderá basándose en los datos cargados")
    elif tests_passed >= 2:
        print(" Integración parcialmente funcional")
        print("\n RECOMENDACIONES:")
        print("   1. Verificar que el archivo Excel se cargó correctamente")
        print("   2. Revisar los logs del servidor para errores")
        print("   3. Probar con consultas más específicas")
    else:
        print(" Problemas críticos de integración")
        print("\n ACCIONES REQUERIDAS:")
        print("   1. Verificar que el servidor esté ejecutándose")
        print("   2. Revisar la configuración de Pinecone")
        print("   3. Verificar las variables de entorno")
    
    print("="*60)
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
