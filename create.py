import os

# Carpeta donde se guardarán los intents
TOOLS_DIR = "tools"

# Plantillas base para cada tipo de intento
TEMPLATES = {
    "rag_opensearch": """# RAG con OpenSearch
import httpx

async def process(query: str):
    url = "http://localhost:9200/_search"
    response = httpx.get(url, params={"q": query})
    return response.json()
""",
    "nlp_to_sql": """# NLP → SQL
import sqlite3

def process(query: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    sql_query = f"SELECT * FROM table WHERE column LIKE '%{query}%'"
    cursor.execute(sql_query)
    results = cursor.fetchall()
    conn.close()
    return results
""",
    "generic_empty": """# Intento genérico vacío
def process(input_data):
    return {"message": "Intento genérico ejecutado", "input": input_data}
"""
}

def create_intent(intent_type: str, intent_name: str):
    """Genera un archivo de intento en la carpeta tools/"""
    if intent_type not in TEMPLATES:
        print(f"⚠️ Tipo de intento '{intent_type}' no reconocido.")
        return
    
    # Crear carpeta si no existe
    os.makedirs(TOOLS_DIR, exist_ok=True)
    
    # Crear archivo dentro de tools/
    filename = f"{TOOLS_DIR}/{intent_name}.py"
    
    if os.path.exists(filename):
        print(f"⚠️ El intento '{intent_name}' ya existe.")
        return
    
    with open(filename, "w") as f:
        f.write(TEMPLATES[intent_type])
    
    print(f"✅ Intento '{intent_name}' generado en {filename}")

