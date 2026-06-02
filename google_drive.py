import os
import io
from google_auth import get_google_service
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import config

def get_drive_service():
    """Returns a Google Drive API service instance."""
    return get_google_service('drive', 'v3')

def list_drive_files(search_query=None, max_results=10):
    """Lists files in Google Drive. Optionally filters by a search query."""
    service = get_drive_service()
    
    q = "trashed = false"
    if search_query:
        # Sanitize query by escaping single quotes
        escaped_query = search_query.replace("'", "\\'")
        q += f" and name contains '{escaped_query}'"
        
    results = service.files().list(
        q=q,
        pageSize=max_results,
        fields="nextPageToken, files(id, name, mimeType, size)",
        orderBy="modifiedTime desc"
    ).execute()
    
    return results.get('files', [])

def download_drive_file(file_id):
    """
    Downloads a file from Google Drive.
    Applies strict path sanitization to prevent directory traversal.
    """
    service = get_drive_service()
    
    # 1. Get file metadata to determine the original name
    file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
    original_name = file_metadata.get('name', f'downloaded_{file_id}')
    mime_type = file_metadata.get('mimeType', '')
    
    # 2. Sanitize name to prevent path traversal
    # Extract only the base name (ignores directory prefixes)
    safe_name = os.path.basename(original_name)
    if not safe_name or safe_name in ['.', '..']:
        safe_name = f'downloaded_{file_id}'
        
    # 3. Resolve and verify boundaries
    # Construct target path inside DOWNLOADS_DIR
    target_path = os.path.join(config.DOWNLOADS_DIR, safe_name)
    abs_target_path = os.path.abspath(target_path)
    abs_downloads_dir = os.path.abspath(config.DOWNLOADS_DIR)
    
    # Enforce trailing slash on prefix check to prevent partial matching bypasses
    # e.g., /sandbox-malicious bypassing a /sandbox check
    boundary_prefix = abs_downloads_dir + os.sep
    if not abs_target_path.startswith(boundary_prefix):
        raise PermissionError("Security alert: Directory traversal attempt detected during file download!")

    # 4. Do not download Google Workspace Docs directly (Docs, Sheets, Slides) as they have no size
    # We must export them instead. For simplicity, we raise an error or export to PDF.
    if 'vnd.google-apps' in mime_type:
        # Export Google Docs to PDF
        request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
        abs_target_path += '.pdf'
    else:
        request = service.files().get_media(fileId=file_id)
        
    # Download content
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        
    # Save file contents
    with open(abs_target_path, 'wb') as f:
        f.write(fh.getvalue())
        
    return abs_target_path

def upload_to_drive(local_file_path, original_filename):
    """
    Uploads a local file to Google Drive.
    Verifies that the local file path lies within the designated sandbox.
    """
    # 1. Sanitize input path
    abs_local_path = os.path.abspath(local_file_path)
    abs_downloads_dir = os.path.abspath(config.DOWNLOADS_DIR)
    
    # Verify the local file is within config.DOWNLOADS_DIR
    boundary_prefix = abs_downloads_dir + os.sep
    if not abs_local_path.startswith(boundary_prefix):
        raise PermissionError("Security alert: Attempted to upload a file from outside the designated download folder!")
        
    if not os.path.exists(abs_local_path):
        raise FileNotFoundError(f"Local file not found: {abs_local_path}")
        
    service = get_drive_service()
    
    # Sanitize metadata filename
    safe_metadata_name = os.path.basename(original_filename)
    
    file_metadata = {'name': safe_metadata_name}
    media = MediaFileUpload(abs_local_path, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()
    
    return file
