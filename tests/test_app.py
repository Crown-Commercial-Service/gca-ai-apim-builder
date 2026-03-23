from generate_apim_files import generate_api_package
from generate_fast_api_openapi import create_fastapi_openai_json, clean_fastapi_openai_json
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

def test_clean_openapi_version():
    # checks if the version of openapi is compatible with APIM
    raw_json = '{"openapi": "3.1.0", "paths": {}}'
    cleaned_json = clean_fastapi_openai_json(raw_json)
    data = json.loads(cleaned_json)
    assert data["openapi"] == "3.0.1"


def test_clean_anyof_flattening():
    # Checks if anyof is removed because that key is not compatible with APIM
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
    cleaned_json = clean_fastapi_openai_json(json.dumps(raw_json))
    data = json.loads(cleaned_json)
    schema = data["paths"]["/test"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]


    assert "anyOf" not in schema
    assert schema["type"] == "string"


@patch('requests.get')
def test_create_openapi_success(mock_get, tmp_path, monkeypatch):
    # Tests that a successful GET request saves a cleaned file
    # 1. Setup Mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"openapi": "3.1.0", "info": {"title": "Test"}}'
    mock_get.return_value = mock_response

    # 2. Redirect 'output' folder to a temp directory so we don't create real files
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    user_data = {
        "app_type": "fastapi",
        "backend_url": "https://fake-api.com"
    }

    # 3. Execute
    success, file_path, data = create_fastapi_openai_json(user_data)

    # 4. Assert
    assert success is True
    assert file_path.name == "openapi.json"
    assert file_path.exists()

def test_generate_package_creates_files(tmp_path, monkeypatch):
    # Using temporary folder instead of your real project
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    # Create the dummy folders the function expects to find
    (tmp_path / "policies_templates").mkdir()
    (tmp_path / "terraform_template").mkdir()

    # Create dummy .j2 files so Jinja doesn't crash
    (tmp_path / "policies_templates/logic_app_policies.xml.j2").write_text("policy")
    (tmp_path / "terraform_template/logicapp_terraform.j2").write_text("terraform")

    data = {
        "app_type": "logic_app",
        "display_name": "Test Service"
    }

    # Run the function
    folder_path_str = generate_api_package(data)
    folder_path = Path(folder_path_str)

    # Assertions: Did it work?
    assert folder_path.exists()
    assert (folder_path / "policies.xml").exists()
    assert (folder_path / "main.tf").exists()


def test_generate_package_invalid_type():
    # Checks when invalid app type is inputted and not known by APIM-Builder
    data = {"app_type": "invalid_type", "display_name": "Bad App"}

    # We expect a ValueError to be raised
    with pytest.raises(ValueError, match="Unsupported app type"):
        generate_api_package(data)