from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
import asyncio

app = FastAPI(title="Generador de Tools Multi-Intent con Ollama Local")

# Configuración de las herramientas
class ToolConfig(BaseModel):
    type: str
    count: int

# Ejemplo de configuración:
# - 3 instancias de RAG con OpenSearch
# - 2 instancias de herramienta vacía (generic_empty)
# - 1 instancia de conversión de lenguaje natural a SQL
tools_config = [
    ToolConfig(type="rag_opensearch", count=3),
    ToolConfig(type="generic_empty", count=2),
    ToolConfig(type="nlp_to_sql", count=1),
    # Puedes agregar más tipos, por ejemplo:
    # ToolConfig(type="rag_kendra", count=1),
]

# Función para consumir LLMs desde un Ollama local
async def call_ollama(prompt: str):
    url = "http://localhost:11434/api/generate"  # Ajusta la URL y puerto según tu configuración local
    payload = {
        "model": "deepseek-r1:latest",  # Especifica el modelo que deseas utilizar, ej: "llama2"
        "prompt": prompt,
        "options": {}  # Puedes agregar opciones adicionales si es necesario
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPError as e:
            # Manejo de errores: log o retornar un mensaje adecuado
            return {"error": str(e)}

# Función para crear un router para cada herramienta
def create_tool_router(tool_type: str, tool_id: int) -> APIRouter:
    router = APIRouter(prefix=f"/{tool_type}/{tool_id}", tags=[f"{tool_type}_{tool_id}"])
    
    @router.get("/")
    async def get_info():
        """
        Endpoint de información básica de la herramienta.
        """
        return {
            "tool_type": tool_type,
            "tool_id": tool_id,
            "description": "Endpoint de información de la herramienta."
        }
    
    @router.post("/process")
    async def process_tool(data: dict):
        """
        Endpoint para procesar datos con la herramienta correspondiente.
        La lógica varía según el tipo de herramienta.
        """
        if tool_type == "rag_opensearch":
            # Lógica de procesamiento para RAG con OpenSearch
            result = {"result": "Procesamiento RAG con OpenSearch", "input": data}
        elif tool_type == "nlp_to_sql":
            # Lógica para convertir lenguaje natural a SQL
            result = {"result": "Consulta SQL generada", "input": data}
        elif tool_type == "generic_empty":
            # Lógica genérica (placeholder)
            result = {"result": "Procesamiento genérico", "input": data}
        else:
            raise HTTPException(status_code=400, detail="Tipo de herramienta no soportado")
        
        # Integración con Ollama local para obtener respuesta del LLM
        ollama_response = await call_ollama(f"Procesar {data} con {tool_type}")
        result["ollama"] = ollama_response
        return result
        
    return router

# Registrar dinámicamente los routers basados en la configuración
for config in tools_config:
    for i in range(1, config.count + 1):
        router = create_tool_router(config.type, i)
        app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
