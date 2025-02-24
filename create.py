import os

# Directory where the intents will be stored
TOOLS_DIR = "tools"

# Base templates for each type of intent
TEMPLATES = {
    "rag_opensearch": """# RAG with OpenSearch
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
    "generic_empty": """# Generic empty intent
def process(input_data):
    return {"message": "Generic intent executed", "input": input_data}
"""
}

def create_intent(intent_type: str, intent_name: str):
    """Generates an intent file inside the tools/ folder"""
    if intent_type not in TEMPLATES:
        print(f"⚠️ Intent type '{intent_type}' not recognized.")
        return
    
    # Create folder if it doesn't exist
    os.makedirs(TOOLS_DIR, exist_ok=True)
    
    # Create file inside tools/
    filename = f"{TOOLS_DIR}/{intent_name}.py"
    
    if os.path.exists(filename):
        print(f"⚠️ The intent '{intent_name}' already exists.")
        return
    
    with open(filename, "w") as f:
        f.write(TEMPLATES[intent_type])
    
    print(f"✅ Intent '{intent_name}' generated at {filename}")
