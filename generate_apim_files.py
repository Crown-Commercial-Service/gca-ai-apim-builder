import uuid
from azure.storage.blob import ContainerClient, ExponentialRetry
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import tempfile
from generate_fast_api_openapi import create_fastapi_openapi_json
import os
from dotenv import load_dotenv

load_dotenv()

def upload_to_azure_storage(local_path, azure_folder_name, user_email):
    container_client = ContainerClient.from_connection_string(
        conn_str=os.getenv("BLOB_CONNECTION_STRING"),
        container_name=os.getenv("BLOB_CONTAINER_NAME"),
        retry_policy=ExponentialRetry(initial_backoff=2, retry_total=5),
    )
    blob_metadata = {"email": user_email}
    for file_path in Path(local_path).iterdir():
        if file_path.is_file():
            # Define the blob name (folder/filename.ext)
            blob_name = f"{azure_folder_name}/{file_path.name}"
            blob_client = container_client.get_blob_client(blob=blob_name)

            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True, metadata=blob_metadata)


def generate_api_package(data):
    """ Generates all the IAC files from user's input:
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

    with tempfile.TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir)
        if app_type == "fastapi":
            success, filepath, clean_data = create_fastapi_openapi_json(data, target_dir=working_dir)

        rendered_policy = policy_tmpl.render(data)
        rendered_terraform = terraform_tmpl.render(data)
        (working_dir / "policies.xml").write_text(rendered_policy, encoding='utf-8')
        (working_dir / "main.tf").write_text(rendered_terraform, encoding='utf-8')

        # Name for azure
        clean_display_name = data.get("display_name", "api").replace(" ", "_").lower()
        unique_id = str(uuid.uuid4())[:8]
        azure_folder_name = f"{clean_display_name}_{unique_id}"
        upload_to_azure_storage(working_dir, azure_folder_name, data["email"])

    return "Process Complete"