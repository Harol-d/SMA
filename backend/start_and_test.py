#!/usr/bin/env python3
"""
Script para iniciar el servidor y ejecutar pruebas de integración
"""

import subprocess
import time
import sys
import os
import requests
import signal
import threading

def start_server():
    """Inicia el servidor Flask en un proceso separado"""
    print("Iniciando servidor Flask...")
    try:
        # Cambiar al directorio del backend
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Iniciar el servidor
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Servidor iniciado con PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Error iniciando servidor: {e}")
        return None

def wait_for_server(max_attempts=30):
    """Espera a que el servidor esté disponible"""
    print("Esperando a que el servidor esté disponible...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:5000/api/dashboard", timeout=2)
            if response.status_code == 200:
                print("Servidor disponible!")
                return True
        except:
            pass
        
        print(f"Intento {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("Timeout: El servidor no respondió en el tiempo esperado")
    return False

def run_tests():
    """Ejecuta las pruebas de integración"""
    print("\nEjecutando pruebas de integración...")
    try:
        result = subprocess.run([
            sys.executable, "tests/test_excel_integration.py"
        ], capture_output=True, text=True, timeout=60)
        
        print("SALIDA DE LAS PRUEBAS:")
        print("=" * 50)
        print(result.stdout)
        
        if result.stderr:
            print("ERRORES:")
            print("=" * 50)
            print(result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Timeout: Las pruebas tardaron demasiado")
        return False
    except Exception as e:
        print(f"Error ejecutando pruebas: {e}")
        return False

def main():
    """Función principal"""
    print("SCRIPT DE INICIO Y PRUEBA DEL SERVIDOR SMA")
    print("=" * 60)
    
    server_process = None
    
    try:
        # Iniciar servidor
        server_process = start_server()
        if not server_process:
            print("No se pudo iniciar el servidor")
            return False
        
        # Esperar a que esté disponible
        if not wait_for_server():
            print("El servidor no se pudo iniciar correctamente")
            return False
        
        # Ejecutar pruebas
        success = run_tests()
        
        if success:
            print("\nSUCCESS: Todas las pruebas pasaron!")
        else:
            print("\nERROR: Algunas pruebas fallaron")
        
        return success
        
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
        return False
    except Exception as e:
        print(f"\nError inesperado: {e}")
        return False
    finally:
        # Limpiar: terminar el servidor
        if server_process:
            print("\nTerminando servidor...")
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
                print("Servidor terminado correctamente")
            except:
                print("Forzando terminación del servidor...")
                server_process.kill()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
