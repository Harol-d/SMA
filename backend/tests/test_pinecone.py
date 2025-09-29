import os
from dotenv import load_dotenv
from pinecone import Pinecone
import google.generativeai as genai

# Cargar variables de entorno desde el archivo .env
load_dotenv()

print("🔍 Iniciando pruebas de conexión...")

# ===== PRUEBA 1: PINE CONE =====
print("\n📊 Probando conexión con Pinecone...")
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("smaccb-pruebas1024")
    stats = index.describe_index_stats()
    print("✅ Pinecone conectado exitosamente!")
    print(f"   - Dimensión: {stats['dimension']}")
    print(f"   - Vectores totales: {stats['total_vector_count']}")
    print(f"   - Métrica: {stats['metric']}")
    print(f"   - Completitud: {stats['index_fullness']}")
except Exception as e:
    print(f"❌ Error con Pinecone: {e}")

# ===== PRUEBA 2: GEMINI =====
print("\n🤖 Probando conexión con Gemini...")
try:
    # Configurar Gemini
    genai.configure(api_key=os.getenv("API_KEY"))
    
    # Verificar API key
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("❌ Error: No se encontró API_KEY en el archivo .env")
        print("💡 Asegúrate de que la línea API_KEY esté configurada en tu archivo .env")
    else:
        print(f"✅ API Key de Gemini cargada: {api_key[:10]}...{api_key[-10:]}")
        
        # Generar embedding para un texto de prueba
        text = "Texto de prueba para generar embeddings con Gemini"
        result = genai.embed_content(
            model="models/embedding-001",
            content=text
        )
        
        vector = result['embedding']
        print("✅ Embedding generado exitosamente!")
        print(f"   - Longitud del vector: {len(vector)}")
        print(f"   - Primeros 5 valores: {vector[:5]}")
        print(f"   - Últimos 5 valores: {vector[-5:]}")
        
except Exception as e:
    print(f"❌ Error con Gemini: {e}")
    print("💡 Sugerencias:")
    print("   - Verifica que la API key de Gemini sea correcta")
    print("   - Verifica tu cuota en Google AI Studio")

print("\n🎉 Pruebas completadas!")
