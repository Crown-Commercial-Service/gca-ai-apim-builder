// Shows AI fields only when AI Foundry is selected
function toggleAIFields() {
    // Get all elements safely
    const appTypeEl = document.getElementById('app_type');
    const aiDiv = document.getElementById('ai-only-fields');
    const mappingSection = document.getElementById('mapping-section');
    const backendLabel = document.getElementById('backend-url-label');
    const corsSelectEl = document.getElementById('cors_select');
    const corsDiv = document.getElementById('cors-details');

    // 1. Logic for App Type & Mapping
    if (appTypeEl) {
        const type = appTypeEl.value;

        // Toggle AI Fields
        if (aiDiv) {
            aiDiv.style.display = (type === 'ai_foundry') ? 'block' : 'none';
        }

        // Toggle Mapping Section (Hide for FastAPI)
        if (mappingSection) {
            if (type === 'fastapi' || type == 'ai_foundry') {
                mappingSection.style.display = 'none';
                toggleRequired(mappingSection, false);
            } else {
                mappingSection.style.display = 'block';
                toggleRequired(mappingSection, true);
            }
        }

        // Update Backend Label Text
        if (backendLabel) {
            if (type === 'logic_app') {
                backendLabel.innerHTML = 'Logic App Workflow URL * <span style="color: #666; font-size: 0.8rem; font-weight: normal;">(Paste the full HTTP POST URL)</span>';
            } else if (type === 'ai_foundry') {
                backendLabel.innerHTML = 'Foundry Endpoint URL *';
            } else {
                backendLabel.innerHTML = 'Target Backend URL *';
            }
        }
    }

    // 2. Logic for CORS (Independent of App Type)
    if (corsSelectEl && corsDiv) {
        const corsInput = corsDiv.querySelector('input');
        if (corsSelectEl.value === 'yes') {
            corsDiv.style.display = 'block';
            if (corsInput) corsInput.required = true;
        } else {
            corsDiv.style.display = 'none';
            if (corsInput) corsInput.required = false;
        }
    }
}

// Helper function to handle 'required' validation on hidden fields
function toggleRequired(parent, isRequired) {
    const inputs = parent.querySelectorAll('input');
    inputs.forEach(input => {
        input.required = isRequired;
    });
}

// Run once on page load to set initial state
window.onload = toggleAIFields;
// Adds a new row to the operations mapping table
function addRow() {
    const table = document.getElementById('operations-table').getElementsByTagName('tbody')[0];
    const newRow = table.insertRow();

    newRow.innerHTML = `
        <td>
            <select name="methods[]">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
            </select>
        </td>
        <td><input type="text" name="f_paths[]" placeholder="/path" required></td>
        <td><input type="text" name="b_paths[]" placeholder="/target"></td>
        <td><button type="button" class="btn-remove" onclick="removeRow(this)">×</button></td>
    `;
}

// Allows users to delete a row if they made a mistake
function removeRow(btn) {
    const row = btn.parentNode.parentNode;
    row.parentNode.removeChild(row);
}

function addCorsRow() {
    const tbody = document.getElementById('cors-tbody');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><input type="url" name="cors_origins[]" placeholder="https://another-app.com" style="width: 90%;"></td>
        <td><button type="button" onclick="this.closest('tr').remove()" style="background:none; border:none; color:red; cursor:pointer;">&times;</button></td>
    `;
    tbody.appendChild(row);
}

