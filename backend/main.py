from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routes.Routes import api

app = Flask(__name__)

# Configuración básica
#app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# CORS configurado para desarrollo
CORS(app, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000"
], supports_credentials=True)

# Manejo de errores básico
@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "message": "Archivo demasiado grande"}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "message": "Error interno del servidor"}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Página no encontrada"}), 404

app.register_blueprint(api, url_prefix='/api')

def main():
    print("SMA Backend iniciando en http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)

if __name__ == "__main__":
    main()

