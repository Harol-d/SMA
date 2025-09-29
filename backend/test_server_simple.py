#!/usr/bin/env python3
"""
Script simple para probar el servidor
"""

import requests
import time

def test_server():
    """Prueba si el servidor está funcionando"""
    try:
        print("Probando conexión al servidor...")
        response = requests.get("http://127.0.0.1:5000/api/dashboard", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except requests.exceptions.ConnectionError:
        print("Error: No se puede conectar al servidor")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_server()
