import base64
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    pass


def get_github_config():
    """Get and validate GitHub configuration from environment variables"""
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO") 
    owner = os.getenv("GITHUB_OWNER")
    
    if not all([token, repo, owner]):
        raise GitHubAPIError("Missing required environment variables: GITHUB_TOKEN, GITHUB_REPO, GITHUB_OWNER")
    
    return token, repo, owner


# Initialize configuration
try:
    GITHUB_TOKEN, GITHUB_REPO, GITHUB_OWNER = get_github_config()
    API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"
    print(f"API Base URL: {API_BASE}")
    
    HEADERS = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
except GitHubAPIError as e:
    print(f"Configuration Error: {e}")
    exit(1)


def get_file(filename_path):
    """
    Get a file's content from the GitHub repository.
    
    Args:
        filename_path (str): Path to the file in the repository
        
    Returns:
        tuple: (content, sha, full_response)
        
    Raises:
        GitHubAPIError: If the request fails
    """
    if not filename_path:
        raise GitHubAPIError("filename_path cannot be empty")
        
    url = f"{API_BASE}/{filename_path}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            resp_json = response.json()
            
            # Handle binary files or files that might not be base64 encoded
            try:
                content = base64.b64decode(resp_json['content']).decode('utf-8')
            except UnicodeDecodeError:
                # Return raw bytes for binary files
                content = base64.b64decode(resp_json['content'])
            
            sha = resp_json['sha']
            return content, sha, resp_json
            
        elif response.status_code == 404:
            raise GitHubAPIError(f"File not found: {filename_path}")
        else:
            raise GitHubAPIError(f"Error getting file: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Request failed: {e}")


def add_file(filename_path, data, commit_message=None, retries=3):
    """
    Create a new file in GitHub repository.
    
    Args:
        filename_path (str): Path where the file will be created
        data (str): Content of the file
        commit_message (str): Custom commit message
        retries (int): Number of retry attempts
        
    Returns:
        dict: GitHub API response
        
    Raises:
        GitHubAPIError: If the request fails or file already exists
    """
    if not filename_path or not data:
        raise GitHubAPIError("filename_path and data cannot be empty")
        
    url = f"{API_BASE}/{filename_path}"
    message = commit_message or f"Add {filename_path}"
    
    payload = {
        "message": message,
        "content": base64.b64encode(data.encode('utf-8')).decode('ascii')
    }
    
    for attempt in range(retries):
        try:
            response = requests.put(
                url, 
                headers=HEADERS, 
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code in [201, 200]:
                return response.json()
            elif response.status_code == 422:
                error_msg = response.json().get('message', 'Unknown error')
                if "already exists" in error_msg.lower():
                    raise GitHubAPIError(f"File already exists: {filename_path}")
                else:
                    raise GitHubAPIError(f"Validation error: {error_msg}")
            elif response.status_code == 409:
                raise GitHubAPIError(f"Conflict - file may already exist: {filename_path}")
            else:
                if attempt == retries - 1:  # Last attempt
                    raise GitHubAPIError(f"Failed to add file: {response.status_code} - {response.text}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise GitHubAPIError(f"Request failed: {e}")
            time.sleep(2 ** attempt)
    
    raise GitHubAPIError(f"Failed to add file after {retries} retries")


def update_file(filename_path, data, commit_message=None, retries=3):
    """
    Update an existing file in the GitHub repository.
    
    Args:
        filename_path (str): Path to the file to update
        data (str): New content of the file
        commit_message (str): Custom commit message
        retries (int): Number of retry attempts
        
    Returns:
        dict: GitHub API response
        
    Raises:
        GitHubAPIError: If the request fails or file doesn't exist
    """
    if not filename_path or not data:
        raise GitHubAPIError("filename_path and data cannot be empty")
        
    url = f"{API_BASE}/{filename_path}"
    message = commit_message or f"Update {filename_path}"
    
    # Get current file info
    try:
        _, sha, _ = get_file(filename_path)
    except GitHubAPIError as e:
        raise GitHubAPIError(f"Cannot update file - file not found or inaccessible: {e}")

    payload = {
        "message": message,
        "content": base64.b64encode(data.encode('utf-8')).decode('ascii'),
        "sha": sha
    }
    
    for attempt in range(retries):
        try:
            response = requests.put(
                url, 
                headers=HEADERS, 
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 409:
                # SHA conflict - try to get updated SHA and retry
                try:
                    _, new_sha, _ = get_file(filename_path)
                    payload["sha"] = new_sha
                    continue
                except:
                    raise GitHubAPIError(f"SHA conflict and unable to retrieve updated SHA")
            else:
                if attempt == retries - 1:
                    raise GitHubAPIError(f"Failed to update file: {response.status_code} - {response.text}")
                time.sleep(2 ** attempt)
                
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise GitHubAPIError(f"Request failed: {e}")
            time.sleep(2 ** attempt)
    
    raise GitHubAPIError(f"Failed to update file after {retries} retries")


def create_or_update_file(filename_path, data, commit_message=None):
    """
    Create a file if it doesn't exist, or update it if it does.
    
    Args:
        filename_path (str): Path to the file
        data (str): Content of the file  
        commit_message (str): Custom commit message
        
    Returns:
        dict: GitHub API response
    """
    try:
        # Try to get the file first
        get_file(filename_path)
        # If successful, file exists - update it
        return update_file(filename_path, data, commit_message)
    except GitHubAPIError as e:
        if "not found" in str(e).lower():
            # File doesn't exist - create it
            return add_file(filename_path, data, commit_message)
        else:
            # Some other error occurred
            raise e


# Example usage with error handling
# if __name__ == "__main__":
#     try:
#         # Test getting README.md
#         print(get_file("README.md"))
#         print(add_file('new1.txt', "no data\ncreated", "just cheking", 1))
#         print(update_file('new.txt', "no data\nbut updated", "just cheking", 1))
        
#     except GitHubAPIError as e:
#         print(f"Error: {e}")
#     except Exception as e:
#         print(f"Unexpected error: {e}")