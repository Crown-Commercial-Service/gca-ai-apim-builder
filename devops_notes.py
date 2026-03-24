import json
from pathlib import Path
from datetime import datetime

def save_users_input(form_data, target_dir):
    """
    Validates, formats, and saves deployment data into a Markdown receipt.
    """
    # 1. Initialize the Path object
    target_path = Path(target_dir)

    # 2. Ensure the directory exists (parents=True creates nested folders)
    target_path.mkdir(parents=True, exist_ok=True)

    # 3. Define the specific file name
    file_path = target_path / "DEPLOYMENT_RECEIPT.md"

    # 4. Prepare the Content with an f-string
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    receipt_content = f"""# 📝 Deployment Request Receipt
    **Generated On:** {timestamp}
    **Requester:** {form_data.get('email', 'N/A')}
    
    ---
    
    ## 🏗️ Core Configuration
    | Property | Value |
    | :--- | :--- |
    | **Display Name** | {form_data.get('display_name', 'N/A')} |
    | **API Suffix** | `/{form_data.get('api_suffix', 'unknown')}` |
    | **App Type** | {form_data.get('app_type', 'N/A')} |
    | **Backend URL** | {form_data.get('backend_url', 'N/A')} |
    
    ## 🌐 Connectivity & Security
    * **VNet Integration:** {form_data.get('vnet_type', 'None')}
    * **Subscription Required:** {'Yes' if form_data.get('sub_required') else 'No'}
    
    ## 🚦 Traffic Management
    * **Limit By:** {form_data.get('limit_by', 'N/A')}
    * **Rate Limit:** {form_data.get('rate_limit', '0')} calls per {form_data.get('rate_period', 'N/A')}
    * **Quota:** {form_data.get('quota', 'No Quota')}
    
    ---
    
    ## 📝 Description
    > {form_data.get('description', 'No description provided.')}
    
    ---
    
    ## 📂 Raw JSON Metadata
    <details>
    <summary>Click to view raw data</summary>
    
    ```json
    {json.dumps(form_data, indent=4)}
    </details>
    """
    file_path.write_text(receipt_content, encoding='utf-8')

    print(f"✅ Success! Receipt saved to: {file_path.absolute()}")
