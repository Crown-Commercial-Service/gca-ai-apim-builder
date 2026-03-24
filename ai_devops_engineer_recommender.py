from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()

class AIDevops(BaseModel):
    summary: str = Field(description="A high-level overview of the configuration.")
    security_advice: str = Field(description="Advice specifically regarding VNet, public access, and secrets.")
    cost_and_performance: str = Field(description="Advice regarding SKU tiers, rate limits, and scaling.")
    next_steps: str = Field(description="Specific actions TechOps should take before deploying.")


DEFAULT_PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "system_prompt.md"

pydantic_azure_client = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)
model = OpenAIChatModel(
    model_name=os.getenv("DEPLOYMENT_NAME"),
    provider=OpenAIProvider(openai_client=pydantic_azure_client),
)


def create_devops_recommedation_file(form_data, target_dir):
    # Read the prompt from the markdown file

    with open(DEFAULT_PROMPT_PATH, "r") as f:
        system_prompt_template = f.read()

    devops_model = Agent(
        model=model,
        output_type=AIDevops,
        model_settings=ModelSettings(temperature=0.0),
        system_prompt=system_prompt_template.format(form_data),
    )

    result = devops_model.run_sync("Perform the audit now.")
    audit_data =  result.output
    pretty_input = json.dumps(form_data, indent=4)

    # 6. Create the Document Content with Appendix
    report_content = f"""# 🚀 Azure DevOps Deployment Audit
    **Target API:** {form_data.get('display_name', 'N/A')}
    **Requester:** {form_data.get('email', 'N/A')}

    ---

    ## 📋 Executive Summary
    {audit_data.summary}

    ## 🔒 Security & Connectivity
    {audit_data.security_advice}

    ## 💰 Cost & Performance
    {audit_data.cost_and_performance}

    ## ✅ Next Steps & Verification
    {audit_data.next_steps}

    ---

    ## 📂 Appendix: Original Request Data
    The following data was used to generate this audit:

    ```json
    {pretty_input}

    """
    file_path = os.path.join(target_dir, "DEVOPS_ADVICE.md")
    with open(file_path, "w") as f:
        f.write(report_content)