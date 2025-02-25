from fastapi import FastAPI, Form, Request, Query, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse, JSONResponse
import os
import subprocess
import re
import ast
import traceback

app = FastAPI(title="Intent Manager with Ollama")

TOOLS_DIR = "tools"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

templates = Jinja2Templates(directory="templates")

# Function to call Ollama and generate code based on a description
async def call_ollama(description: str):
    try:
        prompt = (
            f"Generate only the Python code for the following, without explanations: {description}. "
            "Only respond with code, no additional text. Return the code within triple backticks ```python."
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
                return f"# Prompt used: {description}\n\n{code_block}", parameters
            return "⚠️ No valid code was generated.", []

        else:
            return f"⚠️ Error executing Ollama: {result.stderr.strip()}", []

    except Exception as e:
        return f"⚠️ Exception while executing Ollama: {str(e)}", []


# Function to extract only the code and detect parameters
def extract_code(text):
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    code = match.group(1).strip() if match else text.strip()

    # Find all functions and their parameters
    param_matches = re.findall(r"def\s+\w+\((.*?)\):", code)

    parameters = set()  # Use a set to avoid duplicates
    for param_match in param_matches:
        params = [param.strip().split("=")[0] for param in param_match.split(",") if param]  # Clean up parameters
        parameters.update(params)

    return code, list(parameters)


# Function to save generated intents
def save_intent(intent_name, intent_code):
    filename = os.path.join(TOOLS_DIR, f"{intent_name}.py")
    os.makedirs(TOOLS_DIR, exist_ok=True)
    with open(filename, "w") as f:
        f.write(intent_code)
    return f"✅ Intent '{intent_name}' successfully saved."


# Function to read the content of a tool
@app.get("/read_intent/", response_class=PlainTextResponse)
async def read_intent_endpoint(intent_name: str = Query(...)):
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return PlainTextResponse(f"⚠️ File '{filename}' not found.", status_code=404)

    with open(filename, "r") as f:
        return PlainTextResponse(f.read())


# Endpoint to delete a tool
@app.delete("/delete_intent/")
async def delete_intent(intent_name: str = Query(...)):
    # Ensure the name has the .py extension
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return JSONResponse(content={"error": f"⚠️ File not found: {filename}"}, status_code=404)

    try:
        os.remove(filename)
        return JSONResponse(content={"message": f"✅ Intent '{intent_name}' successfully deleted."}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": f"⚠️ Could not delete file: {str(e)}"}, status_code=500)


# Function to render the HTML template
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


# Main page with the form
@app.get("/")
async def form_page(request: Request):
    return render_template(request)


# Generate a new intent with Ollama
@app.post("/generate/")
async def generate_intent(request: Request, intent_name: str = Form(...), description: str = Form(...)):
    intent_code, parameters = await call_ollama(description)

    # Save the intent without parameters yet
    save_intent(intent_name, intent_code)

    # Render with detected parameters
    return render_template(
        request,
        message=f"Intent '{intent_name}' generated.",
        content=intent_code,
        parameters=parameters,
        intent_name=intent_name
    )


# Endpoint to obtain the content of a specific tool
@app.get("/read_intent/", response_class=PlainTextResponse)
async def read_intent_endpoint(intent_name: str = Query(...)):
    filename = os.path.join(TOOLS_DIR, intent_name)

    # Ensure the name has the .py extension
    if not intent_name.endswith(".py"):
        filename += ".py"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read()
    
    return PlainTextResponse(f"⚠️ Error: File '{filename}' not found.", status_code=404)

@app.post("/save_edited_code/")
async def save_edited_code(intent_name: str = Query(...), body: dict = Body(...)):
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return JSONResponse(content={"error": f"⚠️ File '{filename}' not found."}, status_code=404)

    try:
        with open(filename, "w") as f:
            f.write(body["code"])

        return JSONResponse(content={"message": "✅ Code successfully updated."}, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={"error": f"⚠️ Could not save the code: {str(e)}"}, status_code=500)


# Save parameters entered by the user in the tool
@app.post("/save_params/")
async def save_params(intent_name: str = Query(...), params: dict = Body(...)):
    filename = os.path.join(TOOLS_DIR, f"{intent_name}.py")

    if os.path.exists(filename):
        with open(filename, "a") as f:
            f.write("\n\n# User-entered parameters:\n")
            for key, value in params.items():
                f.write(f"{key} = '{value}'\n")
        return JSONResponse(content={"message": "Parameters saved."}, status_code=200)
    
    return JSONResponse(content={"error": "File not found."}, status_code=404)


# Validate the correctness of the tool's code
@app.get("/validate_intent/")
async def validate_intent(intent_name: str = Query(...)):
    if not intent_name.endswith(".py"):
        intent_name += ".py"

    filename = os.path.join(TOOLS_DIR, intent_name)

    if not os.path.exists(filename):
        return JSONResponse(content={"status": "error", "message": f"⚠️ File not found: '{filename}'"}, status_code=404)

    try:
        with open(filename, "r") as f:
            code = f.read()

        ast.parse(code)  # Check syntax
        exec_globals = {}

        try:
            exec(code, exec_globals)  # Execute code safely
        except ImportError as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"⚠️ ImportError: {str(e)}. Run 'python -m spacy download en_core_web_sm'.",
                "code": code
            })

        return JSONResponse(content={"status": "success", "message": "✅ The tool's code is valid and executed correctly."})

    except SyntaxError as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"⚠️ Syntax error on line {e.lineno}: {e.msg}",
            "code": code
        })

    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"⚠️ Error executing the code: {traceback.format_exc()}",
            "code": code
        })

        
@app.post("/fix_errors/")
async def fix_errors(body: dict = Body(...)):
    original_code = body.get("code", "")

    if not original_code:
        return JSONResponse(content={"error": "⚠️ No code received for correction."}, status_code=400)

    try:
        prompt = (
            f"Fix the errors in the following Python code and return only the corrected code, without explanations. "
            f"The code to fix is:\n```python\n{original_code}\n```"
        )

        result = subprocess.run(
            ["ollama", "run", "deepseek-r1:latest", prompt],
            capture_output=True,
            text=True
        )

        fixed_code = extract_code(result.stdout)

        return JSONResponse(content={"fixed_code": fixed_code, "message": "✅ Code automatically corrected."}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": f"⚠️ Error fixing the code: {str(e)}"}, status_code=500)
