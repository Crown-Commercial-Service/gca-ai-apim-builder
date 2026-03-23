from flask import Flask, render_template, session, request, redirect, url_for
import os
import json
import requests
from pathlib import Path
from generate_apim_files import generate_api_package
#todo ask if vnet is being used if so what name
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default-dev-key-123")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,  # Prevents scripts from stealing the session
    SESSION_COOKIE_SAMESITE="Lax",  # Required by modern browsers to allow redirects
)
@app.route('/')
def index():
    return render_template('index.html')


def get_form_data():
    """
    Extracts and cleans all user inputs from the Flask request.
    Returns a dictionary of mapped values.
    """
    # 1. Basic Info
    data = {
        "email": request.form.get("email"),
        "display_name": request.form.get("display_name"),
        "api_suffix":   request.form.get("api_suffix"),
        "app_type":     request.form.get("app_type"),
        "backend_url":  request.form.get("backend_url"),
        "sub_required": request.form.get("sub_required") == "yes",
        "vnet_type": request.form.get("vnet_type"),
        "description": request.form.get("description"),
        "limit_by" : request.form.get("limit_by"),
        "rate_limit" : request.form.get("rate_limit"),
        "rate_period": request.form.get("rate_period"),
        "quota": request.form.get("quota"),

    }

    # 2. CORS Logic
    data["enable_cors"] = request.form.get("CORS") == "yes"
    if data["enable_cors"]:
        data["cors_origins"] = ", ".join(request.form.getlist("cors_origins[]")) if request.form.get("CORS") == "yes" else "*"
    else:
        data["cors_origins"] = ""

    # 3. OpenAPI URL (Only for FastAPI)
    if data["app_type"] == "ai_foundry":
        data["model_name"] = request.form.get("model_name")
        data["entra_resource_id"] = request.form.get("entra_resource_id")

    # 4. Manual Operations (Only for Logic Apps / Manual)
    # request.form.getlist collects multiple inputs with the same name (the table rows)
    if data["app_type"] == "logic_app":
        data["methods"] = request.form.getlist("methods[]")
        data["f_paths"] = request.form.getlist("f_paths[]")
        data["b_paths"] = request.form.getlist("b_paths[]")

    return data




def clean_fastapi_openai_json(raw_json_string):
    try:
        spec = json.loads(raw_json_string)

        # 1. Downgrade version
        spec["openapi"] = "3.0.1"

        # 2. Fix 'anyOf' in Validation Errors
        if "components" in spec and "schemas" in spec["components"]:
            ve = spec["components"]["schemas"].get("ValidationError")
            if isinstance(ve, dict) and "properties" in ve:
                loc = ve["properties"].get("loc", {})
                if "items" in loc:
                    loc["items"] = {"type": "string"}

        # 3. Handle Paths and Operations
        if "paths" in spec:
            for path_item in spec["paths"].values():
                if not isinstance(path_item, dict): continue

                for operation in path_item.values():
                    if not isinstance(operation, dict): continue

                    # ADDED: Fix 'examples' (plural) to 'example' (singular) for APIM 3.0.1
                    # APIM 3.0.1 will fail if it sees the 3.1.0 'examples' array
                    parameters = operation.get("parameters", [])
                    for param in parameters:
                        if "examples" in param:
                            # Just take the first example and make it the 'example'
                            first_ex = list(param["examples"].values())[0] if isinstance(param["examples"],
                                                                                         dict) else ""
                            param["example"] = first_ex
                            del param["examples"]

                    # Existing Response cleaning
                    responses = operation.get("responses", {})
                    for res in responses.values():
                        content = res.get("content", {})
                        for media_type in content.values():
                            if "schema" in media_type and not media_type["schema"]:
                                media_type["schema"] = {"type": "object"}

                            # ADDED: Recursive anyOf cleanup for complex Pydantic models
                            # This ensures fields like 'string | null' don't break the import
                            schema = media_type.get("schema", {})
                            if "anyOf" in schema:
                                # Simple fix: just use the first type in the list
                                first_type = schema["anyOf"][0]
                                media_type["schema"] = first_type

        return json.dumps(spec, indent=4)

    except json.JSONDecodeError:
        print("Error: Input is not valid JSON. Backend might have sent an HTML error page.")
        return raw_json_string
    except Exception as e:
        print(f"Cleaning failed: {e}")
        return raw_json_string

def create_fastapi_openai_json(user_data):
    if user_data["app_type"] == "fastapi":
        url = user_data["backend_url"]
        full_url = f"{url}/openapi.json"

        output_dir = Path.cwd() / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / 'openapi.json'
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            clean_data = clean_fastapi_openai_json(response.text)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_data)
            return (True, file_path, clean_data)
        except requests.exceptions.RequestException as e:
            return (False, e)

def create_terraform_script():
    pass

@app.route('/generate', methods=['POST'])
def generate():
    # 1. Obtain all user inputs using our new method
    try:
        user_data = get_form_data()
        if user_data["app_type"] == "fastapi":
            success, filepath, clean_data = create_fastapi_openai_json(user_data)

        # 2. For debugging: Print to your terminal to see the clean dictionary
        generated_data = generate_api_package(user_data)
        print("--- User Input Received ---")
        print(json.dumps(user_data, indent=4))

        # Next steps will go here:
        # - Fetching OpenAPI if FastAPI
        # - Rendering main.tf.j2

        return render_template('success_page.html', display_name=user_data['display_name'])
    except Exception as e:
        return render_template('error_page.html', error_message=str(e))

if __name__ == '__main__':
    app.run(debug=True)