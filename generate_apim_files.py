import uuid
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def generate_api_package(data):
    """
    Generates a unique API package by pulling from:
    - policies_templates/
    - terraform_template/
    - output/ (for openapi.json)
    """
    # 1. Setup Jinja2 Environment for both template folders
    # This allows Jinja to look in both directories for .j2 files
    env = Environment(loader=FileSystemLoader(['policies_templates', 'terraform_template']))

    # 2. Updated Template Mapping (Matching your actual filenames from the screenshot)
    template_map = {
        "fastapi": ("fast_api_policies.xml.j2", "fast_api_terraform_template.j2"),
        "logic_app": ("logic_app_policies.xml.j2", "logicapp_terraform.j2"),
        "ai_foundry": ("foundry_policies.xml.j2", "foundry_terraform.j2")
    }

    app_type = data.get("app_type")
    if app_type not in template_map:
        raise ValueError(f"Unsupported app type: {app_type}")

    policy_file, tf_file = template_map[app_type]

    # Load templates from the environment
    policy_tmpl = env.get_template(policy_file)
    terraform_tmpl = env.get_template(tf_file)

    # 3. Create a Unique Folder Name (Slugified Display Name + UUID)
    clean_display_name = data.get("display_name", "api").replace(" ", "_").lower()
    unique_id = str(uuid.uuid4())[:8]
    folder_name = f"{clean_display_name}_{unique_id}"

    # Final destination path
    output_path = Path.cwd() / folder_name
    output_path.mkdir(parents=True, exist_ok=True)

    # 4. Feature: Copy openapi.json if FastAPI (looking in your 'output' folder)
    if app_type == "fastapi":
        source_openapi = Path.cwd() / "output" / "openapi.json"

        if source_openapi.exists():
            shutil.copy2(source_openapi, output_path / "openapi.json")
        else:
            print(f"Warning: openapi.json not found in 'output' folder.")

    # 5. Render and Save
    rendered_policy = policy_tmpl.render(data)
    rendered_terraform = terraform_tmpl.render(data)

    (output_path / "policies.xml").write_text(rendered_policy)
    (output_path / "main.tf").write_text(rendered_terraform)

    return str(output_path)