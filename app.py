from flask import Flask, render_template, request
import os
import json
import requests
from pathlib import Path
from generate_apim_files import generate_api_package
from generate_fast_api_openapi import create_fastapi_openapi_json

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


@app.route('/generate', methods=['POST'])
def generate():
    # 1. Obtain all user inputs using our new method
    try:
        user_data = get_form_data()
        if user_data["app_type"] == "fastapi":
            success, filepath, clean_data = create_fastapi_openapi_json(user_data)

        # check results
        generated_data = generate_api_package(user_data)
        print("--- User Input Received ---")
        print(json.dumps(user_data, indent=4))

        return render_template('success_page.html', display_name=user_data['display_name'])
    except Exception as e:
        return render_template('error_page.html', error_message=str(e))

if __name__ == '__main__':
    app.run(debug=True)