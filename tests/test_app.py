import pytest
import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock
from generate_apim_files import generate_api_package
from generate_fast_api_openapi import create_fastapi_openapi_json, clean_fastapi_openapi_json


def test_clean_openapi_version():
    #Checks if the version is downgraded to 3.0.1 for APIM compatibility.
    raw_json = '{"openapi": "3.1.0", "paths": {}}'
    cleaned_json = clean_fastapi_openapi_json(raw_json)
    data = json.loads(cleaned_json)
    assert data["openapi"] == "3.0.1"

def test_clean_anyof_flattening():
    # Checks if 'anyOf' is removed since it is not compatible with APIM."
    raw_json = {
        "paths": {
            "/test": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    cleaned_json = clean_fastapi_openapi_json(json.dumps(raw_json))
    data = json.loads(cleaned_json)
    schema = data["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    assert "anyOf" not in schema
    assert schema["type"] == "string"

@patch('requests.get')
def test_create_openapi_success(mock_get, tmp_path):
    # Tests that a successful GET request saves a cleaned file. Note: We pass tmp_path directly as target_dir now.

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"openapi": "3.1.0", "info": {"title": "Test"}}'
    mock_get.return_value = mock_response

    user_data = {
        "app_type": "fastapi",
        "backend_url": "https://fake-api.com"
    }

    # Pass tmp_path as the target_dir to avoid needing monkeypatch here
    success, file_path, data = create_fastapi_openapi_json(user_data, target_dir=tmp_path)

    assert success is True
    assert file_path.exists()
    assert "3.0.1" in data



@patch('generate_apim_files.upload_to_azure_storage')
def test_generate_package_logic_app(mock_upload, tmp_path, monkeypatch):
    # Tests the logic app flow without hitting Azure.

    #  Mock CWD to a temp path for template finding
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Create dummy folders/templates that the function expects
    (tmp_path / "policies_templates").mkdir()
    (tmp_path / "terraform_template").mkdir()
    (tmp_path / "policies_templates/logic_app_policies.xml.j2").write_text("policy {{ display_name }}")
    (tmp_path / "terraform_template/logicapp_terraform.j2").write_text("terraform {{ display_name }}")

    data = {
        "app_type": "logic_app",
        "display_name": "Test Service"
    }


    result_message = generate_api_package(data)


    #  Check the return message contains the success string
    assert "Process Complete" in result_message

    # Check that the Azure upload function was actually called
    assert mock_upload.called

    #  Check that the Azure upload was called with a Path object (the temp dir)
    # and the expected folder name format
    args, kwargs = mock_upload.call_args
    local_path_arg = args[0]
    folder_name_arg = args[1]

    assert isinstance(local_path_arg, Path)
    assert "test_service_" in folder_name_arg


def test_generate_package_invalid_type():
    data = {"app_type": "invalid_type", "display_name": "Bad App"}
    with pytest.raises(ValueError, match="Unsupported app type"):
        generate_api_package(data)