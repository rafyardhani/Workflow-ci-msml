import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Load credential service account
creds = json.loads(os.environ["GDRIVE_CREDENTIALS"])
credentials = Credentials.from_service_account_info(
    creds,
    scopes=["https://www.googleapis.com/auth/drive"]
)

# 2. Build Drive API
service = build('drive', 'v3', credentials=credentials)

# 3. Gunakan ID Shared Drive (atau folder di Shared Drive) sebagai "parent"
SHARED_DRIVE_ID = os.environ["GDRIVE_FOLDER_ID"]
# Pastikan service account sudah diundang ke Shared Drive sebagai Content Manager / Manager / Editor

def upload_directory(local_dir_path, parent_drive_id):
    """
    Rekursif:
     - Jika item folder, buat folder di Drive, lalu panggil upload_directory lagi.
     - Jika item file, langsung upload ke parent_drive_id.
    """
    for item_name in os.listdir(local_dir_path):
        item_path = os.path.join(local_dir_path, item_name)
        if os.path.isdir(item_path):
            folder_meta = {
                'name': item_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_drive_id]
            }
            created_folder = service.files().create(
                body=folder_meta,
                fields='id',
                supportsAllDrives=True
            ).execute()
            new_folder_id = created_folder["id"]
            print(f"Created folder: {item_name} (ID: {new_folder_id})")

            # Rekursif ke subfolder
            upload_directory(item_path, new_folder_id)
        else:
            print(f"Uploading file: {item_name}")
            file_meta = {
                'name': item_name,
                'parents': [parent_drive_id]
            }
            media = MediaFileUpload(item_path, resumable=True)
            service.files().create(
                body=file_meta,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()


# 4. Baca semua subfolder (run_id) di "./mlruns/0"
#    Kemudian buat folder sesuai run_id di Shared Drive (tanpa folder "mlruns" agar tidad redundant).
local_mlruns_0 = "./mlruns/0"

for run_id in os.listdir(local_mlruns_0):
    run_id_local_path = os.path.join(local_mlruns_0, run_id)
    # Pastikan hanya folder (bukan file)
    if os.path.isdir(run_id_local_path):
        # Buat folder dengan nama run_id di root Shared Drive (SHARED_DRIVE_ID)
        run_id_folder_meta = {
            'name': run_id,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [SHARED_DRIVE_ID]
        }
        run_id_folder = service.files().create(
            body=run_id_folder_meta,
            fields='id',
            supportsAllDrives=True
        ).execute()
        run_id_folder_id = run_id_folder["id"]
        print(f"=== Created run_id folder: {run_id} (ID: {run_id_folder_id}) ===")

        # Upload isinya (subfolder, file) secara rekursif
        upload_directory(run_id_local_path, run_id_folder_id)

print("=== All run_id folders and files have been uploaded directly to Shared Drive! ===")