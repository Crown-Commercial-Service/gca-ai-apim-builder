from flask import Flask, render_template, request, send_file
from azure.storage.blob import ContainerClient
import io
import zipfile
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_container_client():
    return ContainerClient.from_connection_string(
        conn_str=os.getenv("BLOB_CONNECTION_STRING"),
        container_name=os.getenv("BLOB_CONTAINER_NAME")
    )


@app.route('/')
def dashboard():
    client = get_container_client()
    search_query = request.args.get('search', '').lower()

    # 1. List all blobs and group them by folder
    folders = {}
    blobs = client.list_blobs(include=['metadata'])

    for blob in blobs:
        parts = blob.name.split('/')
        if len(parts) > 1:
            folder_name = parts[0]
            # Get email from metadata (which you saved during upload)
            email = blob.metadata.get('email', 'Unknown')

            if folder_name not in folders:
                folders[folder_name] = {
                    "name": folder_name,
                    "email": email,
                    "files": []
                }
            folders[folder_name]["files"].append(parts[1])

    # 2. Filter by Search (Email or Folder Name)
    filtered_folders = [
        f for f in folders.values()
        if search_query in f['email'].lower() or search_query in f['name'].lower()
    ]

    # 3. Sort by Email
    filtered_folders.sort(key=lambda x: x['email'])

    return render_template('dashboard.html', folders=filtered_folders)


@app.route('/download/<folder_name>')
def download_folder(folder_name):
    client = get_container_client()
    blobs = client.list_blobs(name_starts_with=f"{folder_name}/")

    # Create a ZIP file in memory (RAM) so we don't use server disk space
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for blob in blobs:
            blob_client = client.get_blob_client(blob.name)
            data = blob_client.download_blob().readall()
            filename = blob.name.split('/')[-1]
            zf.writestr(filename, data)

    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{folder_name}.zip"
    )

if __name__ == '__main__':
    app.run(debug=True)