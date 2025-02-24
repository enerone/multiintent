from fastapi import FastAPI, Form, Request, Query, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse, JSONResponse
import os
import subprocess
import re
import ast
import traceback

app = FastAPI(title="Gestor de Intents con Ollama")

TOOLS_DIR = "tools"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

templates = Jinja2Templates(directory="templates")

# Función para llamar a Ollama y generar código en base a una descripción
async def call_ollama(description: str):
    try:
        prompt = (
            f"Genera solo el código en Python para lo siguiente, sin explicaciones: {description}. "
            "Solo responde con código, sin texto adicional. Devuelve el código dentro de triple backticks ```python."
        )

        result = subprocess.run(
            ["ollama", "run", "deepseek-r1:latest", prompt],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()

        if result.returncode == 0:
            code_block, parameters = extract_code(output)
            if code_block:
                return f"# Prompt utilizado: {description}\n\n{code_block}", parameters
            return "⚠️ No se generó código válido.", []

        else:
            return f"⚠️ Error ejecutando Ollama: {result.stderr.strip()}", []

    except Exception as e:
        return f"⚠️ Excepción al ejecutar Ollama: {str(e)}", []


# Función para extraer solo el código y detectar parámetros
def extract_code(text):
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    code = match.group(1).strip() if match else text.strip()

    # Buscar todas las funciones y sus parámetros
    param_matches = re.findall(r"def\s+\w+\((.*?)\):", code)

    parameters = set()  # Usamos un set para evitar duplicados
    for param_match in param_matches:
        params = [param.strip().split("=")[0] for param in param_match.split(",") if param]  # Limpiamos parámetros
        parameters.update(params)

    return code, list(parameters)


# Función para guardar intents generados
def save_intent(intent_name, intent_code):
    filename = os.path.join(TOOLS_DIR, f"{intent_name}.py")
    os.makedirs(TOOLS_DIR, exist_ok=True)
    with open(filename, "w") as f:
        f.write(intent_code)
    return f"✅ Intent '{intent_name}' guardado correctamente."


# Función para leer el contenido de una tool
@app.get("/read_intent/", response_class=PlainTextResponse)
async def read_intent_endpoint(intent_name: str = Query(...)):
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return PlainTextResponse(f"⚠️ No se encontró el archivo '{filename}'", status_code=404)

    with open(filename, "r") as f:
        return PlainTextResponse(f.read())


# Endpoint para eliminar una tool
@app.delete("/delete_intent/")
async def delete_intent(intent_name: str = Query(...)):
    # Asegurar que el nombre tiene la extensión .py
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return JSONResponse(content={"error": f"⚠️ Archivo no encontrado: {filename}"}, status_code=404)

    try:
        os.remove(filename)
        return JSONResponse(content={"message": f"✅ Intent '{intent_name}' eliminado correctamente."}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": f"⚠️ No se pudo eliminar el archivo: {str(e)}"}, status_code=500)


# Función para renderizar la plantilla HTML
def render_template(request: Request, message="", content="", parameters=None, intent_name=""):
    if parameters is None:
        parameters = []

    intents = [f for f in os.listdir(TOOLS_DIR) if f.endswith(".py")] if os.path.exists(TOOLS_DIR) else []
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "message": message,
            "intents": intents,
            "content": content,
            "parameters": parameters,
            "intent_name": intent_name
        }
    )


# Página principal con el formulario
@app.get("/")
async def form_page(request: Request):
    return render_template(request)


# Generar un nuevo intent con Ollama
@app.post("/generate/")
async def generate_intent(request: Request, intent_name: str = Form(...), description: str = Form(...)):
    intent_code, parameters = await call_ollama(description)

    # Guardamos el intent sin parámetros aún
    save_intent(intent_name, intent_code)

    # Renderizar con los parámetros detectados
    return render_template(
        request,
        message=f"Intent '{intent_name}' generado.",
        content=intent_code,
        parameters=parameters,
        intent_name=intent_name
    )


# Endpoint para obtener el contenido de una tool específica
@app.get("/read_intent/", response_class=PlainTextResponse)
async def read_intent_endpoint(intent_name: str = Query(...)):
    filename = os.path.join(TOOLS_DIR, intent_name)

    # Asegurar que el nombre tiene la extensión .py
    if not intent_name.endswith(".py"):
        filename += ".py"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read()
    
    return PlainTextResponse(f"⚠️ Error: No se encontró el archivo '{filename}'", status_code=404)

@app.post("/save_edited_code/")
async def save_edited_code(intent_name: str = Query(...), body: dict = Body(...)):
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return JSONResponse(content={"error": f"⚠️ No se encontró el archivo '{filename}'"}, status_code=404)

    try:
        with open(filename, "w") as f:
            f.write(body["code"])

        return JSONResponse(content={"message": "✅ Código actualizado correctamente."}, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={"error": f"⚠️ No se pudo guardar el código: {str(e)}"}, status_code=500)


# Guardar parámetros ingresados por el usuario en la tool
@app.post("/save_params/")
async def save_params(intent_name: str = Query(...), params: dict = Body(...)):
    filename = os.path.join(TOOLS_DIR, f"{intent_name}.py")

    if os.path.exists(filename):
        with open(filename, "a") as f:
            f.write("\n\n# Parámetros ingresados por el usuario:\n")
            for key, value in params.items():
                f.write(f"{key} = '{value}'\n")
        return JSONResponse(content={"message": "Parámetros guardados."}, status_code=200)
    
    return JSONResponse(content={"error": "Archivo no encontrado."}, status_code=404)


# Validar la corrección del código de la tool
@app.get("/validate_intent/")
async def validate_intent(intent_name: str = Query(...)):
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return JSONResponse(content={"status": "error", "message": f"⚠️ No se encontró el archivo '{filename}'"}, status_code=404)

    try:
        with open(filename, "r") as f:
            code = f.read()

        ast.parse(code)  # Verifica la sintaxis
        exec_globals = {}
        exec(code, exec_globals)  # Ejecuta el código de manera segura

        return JSONResponse(content={"status": "success", "message": "✅ El código de la tool es válido y se ejecutó correctamente."})

    except SyntaxError as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"⚠️ Error de sintaxis en la línea {e.lineno}: {e.msg}",
            "code": code  # Enviar el código para que se pueda editar en el modal
        })

    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"⚠️ Error al ejecutar el código: {traceback.format_exc()}",
            "code": code
        })
        
@app.post("/fix_errors/")
async def fix_errors(body: dict = Body(...)):
    original_code = body.get("code", "")

    if not original_code:
        return JSONResponse(content={"error": "⚠️ No se recibió código para corregir."}, status_code=400)

    try:
        prompt = (
            f"Corrige los errores en el siguiente código Python y devuelve solo el código corregido, sin explicaciones. "
            f"El código a corregir es:\n```python\n{original_code}\n```"
        )

        result = subprocess.run(
            ["ollama", "run", "deepseek-r1:latest", prompt],
            capture_output=True,
            text=True
        )

        fixed_code = extract_code(result.stdout)

        return JSONResponse(content={"fixed_code": fixed_code, "message": "✅ Código corregido automáticamente."}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": f"⚠️ Error al corregir el código: {str(e)}"}, status_code=500)

