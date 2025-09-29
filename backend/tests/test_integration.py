#!/usr/bin/env python3
"""
Script de prueba para verificar la integración entre chat y datos Excel
Ejecutar: python test_integration.py
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

def test_chat_endpoint():
    """Prueba el endpoint del chat"""
    print("🧪 PRUEBA 1: Endpoint del chat")
    print("="*50)
    
    # Consulta de prueba
    test_query = "¿Qué proyectos están disponibles?"
    
    payload = {
        "text": test_query,
        "conversationId": "test_conv_123",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa:")
            print(f"   - success: {data.get('success', 'N/A')}")
            print(f"   - content length: {len(data.get('content', ''))}")
            print(f"   - content preview: {data.get('content', '')[:100]}...")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión. ¿Está el servidor ejecutándose?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def test_dashboard_endpoint():
    """Prueba el endpoint del dashboard"""
    print("\n🧪 PRUEBA 2: Endpoint del dashboard")
    print("="*50)
    
    try:
        response = requests.get(DASHBOARD_ENDPOINT, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dashboard disponible:")
            print(f"   - success: {data.get('success', 'N/A')}")
            print(f"   - total_vectors: {data.get('total_vectors', 'N/A')}")
            print(f"   - metrics: {data.get('metrics', {})}")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_server_connectivity():
    """Prueba la conectividad básica del servidor"""
    print("\n🧪 PRUEBA 3: Conectividad del servidor")
    print("="*50)
    
    try:
        # Intentar hacer una petición básica
        response = requests.get(f"{BASE_URL}/api/dashboard", timeout=5)
        print(f"✅ Servidor accesible en {BASE_URL}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar a {BASE_URL}")
        print("   Verifica que el servidor esté ejecutándose:")
        print("   cd SMA/backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ Error de conectividad: {str(e)}")
        return False

def test_with_excel_data():
    """Simula consultas que requieren datos Excel"""
    print("\n🧪 PRUEBA 4: Consultas que requieren datos Excel")
    print("="*50)
    
    test_queries = [
        "¿Qué proyectos están atrasados?",
        "Dame un resumen de los proyectos",
        "¿Cuáles son las principales causas de atraso?",
        "¿Qué persona tiene más tareas pendientes?"
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n📝 Consultando: {query}")
        
        payload = {
            "text": query,
            "conversationId": f"test_conv_{hash(query)}",
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
                
                # Verificar si la respuesta indica falta de datos
                if any(indicator in content.lower() for indicator in ['no hay datos', 'sin información', 'carga un archivo']):
                    print("⚠️  Respuesta indica falta de datos Excel")
                    results.append('no_data')
                else:
                    print("✅ Respuesta con contenido")
                    results.append('success')
            else:
                print(f"❌ Error {response.status_code}")
                results.append('error')
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append('error')
    
    # Resumen
    success_count = results.count('success')
    no_data_count = results.count('no_data')
    error_count = results.count('error')
    
    print(f"\n📊 Resumen de consultas:")
    print(f"   - Exitosas: {success_count}/{len(test_queries)}")
    print(f"   - Sin datos: {no_data_count}/{len(test_queries)}")
    print(f"   - Errores: {error_count}/{len(test_queries)}")
    
    return success_count > 0 or no_data_count > 0

def main():
    """Función principal de pruebas"""
    print("🔍 SCRIPT DE PRUEBAS DE INTEGRACIÓN SMA")
    print("="*60)
    print("Este script verifica que el chat pueda acceder a los datos Excel")
    print("="*60)
    
    # Ejecutar pruebas
    tests_passed = 0
    total_tests = 4
    
    if test_server_connectivity():
        tests_passed += 1
    
    if test_dashboard_endpoint():
        tests_passed += 1
    
    if test_chat_endpoint():
        tests_passed += 1
    
    if test_with_excel_data():
        tests_passed += 1
    
    # Resultado final
    print(f"\n{'='*60}")
    print(f"🏁 RESULTADO FINAL: {tests_passed}/{total_tests} pruebas exitosas")
    
    if tests_passed == total_tests:
        print("✅ ¡Integración funcionando correctamente!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Carga un archivo Excel usando la interfaz web")
        print("   2. Haz preguntas específicas sobre tus proyectos")
        print("   3. Verifica que las respuestas incluyan datos reales")
    elif tests_passed >= 2:
        print("⚠️  Integración parcialmente funcional")
        print("\n🔧 RECOMENDACIONES:")
        print("   1. Verifica que el archivo Excel se cargue correctamente")
        print("   2. Revisa los logs del servidor para errores específicos")
        print("   3. Prueba consultas simples primero")
    else:
        print("❌ Problemas críticos de integración")
        print("\n🚨 ACCIONES REQUERIDAS:")
        print("   1. Verifica que el servidor esté ejecutándose")
        print("   2. Revisa la configuración de la base de datos vectorial")
        print("   3. Verifica las variables de entorno (.env)")
    
    print("="*60)
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
