import base64
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def get_github_config():
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO") 
    owner = os.getenv("GITHUB_OWNER")
    
    if not all([token, repo, owner]):
        return None, None, None, {
            "error": True,
            "message": "Missing required environment variables: GITHUB_TOKEN, GITHUB_REPO, GITHUB_OWNER"
        }
    
    return token, repo, owner, None

GITHUB_TOKEN, GITHUB_REPO, GITHUB_OWNER, config_error = get_github_config()
if config_error:
    print(f"Configuration Error: {config_error['message']}")
    exit(1)

API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


def get_file(filename_path):
    if not filename_path:
        return None, None, {"error": True, "message": "filename_path cannot be empty"}
    
    url = f"{API_BASE}/{filename_path}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            resp_json = response.json()
            try:
                content = base64.b64decode(resp_json['content']).decode('utf-8')
            except UnicodeDecodeError:
                content = base64.b64decode(resp_json['content'])
            sha = resp_json['sha']
            return content, sha, None
        elif response.status_code == 404:
            return None, None, {"error": True, "message": f"File not found: {filename_path}"}
        else:
            return None, None, {"error": True, "message": f"Error getting file: {response.status_code} - {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return None, None, {"error": True, "message": f"Request failed: {e}"}


def add_file(filename_path, data, commit_message=None, retries=3):
    if not filename_path or not data:
        return {"error": True, "message": "filename_path and data cannot be empty"}
    
    url = f"{API_BASE}/{filename_path}"
    message = commit_message or f"Add {filename_path}"
    
    payload = {
        "message": message,
        "content": base64.b64encode(str(data).encode('utf-8')).decode('ascii')
    }
    
    for attempt in range(retries):
        try:
            response = requests.put(url, headers=HEADERS, data=json.dumps(payload), timeout=30)
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 422:
                msg = response.json().get('message', 'Unknown error')
                return {"error": True, "message": f"Validation error: {msg}"}
            elif response.status_code == 409:
                return {"error": True, "message": f"Conflict - file may already exist: {filename_path}"}
            else:
                if attempt == retries - 1:
                    return {"error": True, "message": f"Failed to add file: {response.status_code} - {response.text}"}
                time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                return {"error": True, "message": f"Request failed: {e}"}
            time.sleep(2 ** attempt)

    return {"error": True, "message": f"Failed to add file after {retries} retries"}


def update_file(filename_path, data, commit_message=None, retries=3):
    if not filename_path or not data:
        return {"error": True, "message": "filename_path and data cannot be empty"}
    
    url = f"{API_BASE}/{filename_path}"
    message = commit_message or f"Update {filename_path}"
    
    sha_data = get_file(filename_path)
    if sha_data[2] is not None:
        return {"error": True, "message": f"Cannot update file - file not found or inaccessible: {sha_data[2]['message']}"}
    
    sha = sha_data[1]
    
    payload = {
        "message": message,
        "content": base64.b64encode(str(data).encode('utf-8')).decode('ascii'),
        "sha": sha
    }

    for attempt in range(retries):
        try:
            response = requests.put(url, headers=HEADERS, data=json.dumps(payload), timeout=30)
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 409:
                new_sha_data = get_file(filename_path)
                if new_sha_data[2] is not None:
                    return {"error": True, "message": "SHA conflict and unable to retrieve updated SHA"}
                payload["sha"] = new_sha_data[1]
                continue
            else:
                if attempt == retries - 1:
                    return {"error": True, "message": f"Failed to update file: {response.status_code} - {response.text}"}
                time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                return {"error": True, "message": f"Request failed: {e}"}
            time.sleep(2 ** attempt)

    return {"error": True, "message": f"Failed to update file after {retries} retries"}


def create_or_update_file(filename_path, data, commit_message=None):
    file_data = get_file(filename_path)
    if file_data[2] and "not found" in file_data[2]["message"].lower():
        return add_file(filename_path, data, commit_message)
    elif file_data[2]:
        return {"error": True, "message": file_data[2]["message"]}
    else:
        return update_file(filename_path, data, commit_message)
