from flask import Flask, render_template, request, jsonify
import asyncio
from crawler import run_crawler
import requests
import os
import json
import time
import logging
from urllib.parse import urlparse
from functools import partial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_file_paths(docs_url, github_url):
    """Generate file paths based on URLs"""
    docs_domain = urlparse(docs_url).netloc
    
    # Clean up GitHub URL before parsing
    github_url = github_url.strip().rstrip('/')
    if github_url.endswith('.git'):
        github_url = github_url[:-4]
    
    _, _, _, owner, repo = github_url.split('/')
    
    docs_path = f"documentation_output/{docs_domain}_documentation.json"
    github_path = f"uithub_repos/{owner}_{repo}_uithub.json"
    
    return docs_path, github_path

async def process_all(docs_url, github_url):
    """Process documentation and GitHub repo data"""
    try:
        # Get file paths
        docs_path, github_path = get_file_paths(docs_url, github_url)
        
        logger.info(f"Expected file paths - Docs: {docs_path}, GitHub: {github_path}")
        
        # Extract data sequentially to ensure proper order
        uithub_result = extract_uithub(github_url)
        logger.info("UIthub extraction completed")
        
        crawler_result = await run_crawler(docs_url)
        logger.info("Crawler completed")
        
        # Verify files exist immediately after creation
        if not os.path.exists(docs_path):
            logger.error(f"Documentation file not found at: {docs_path}")
            raise FileNotFoundError(f"Documentation file not created at: {docs_path}")
            
        if not os.path.exists(github_path):
            logger.error(f"UIthub file not found at: {github_path}")
            raise FileNotFoundError(f"UIthub file not created at: {github_path}")
        
        # Verify file contents
        try:
            with open(docs_path, 'r') as f:
                docs_data = json.load(f)
            with open(github_path, 'r') as f:
                github_data = json.load(f)
                
            if not docs_data or not github_data:
                raise ValueError("One or both files are empty")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in files: {str(e)}")
            raise
            
        
        return {
            "crawler_result": crawler_result,
            "uithub_result": uithub_result,
        }
        
    except Exception as e:
        logger.error(f"Error in processing: {str(e)}", exc_info=True)
        raise

@app.route('/', methods=['GET', 'POST'])
async def index():
    if request.method == 'POST':
        try:
            docs_url = request.form['url']
            github_url = request.form['github_url']
            
            # Now we can directly await process_all
            result = await process_all(docs_url, github_url)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    return render_template('index.html')

def extract_uithub(github_url):
    """Extract UIthub data"""
    try:
        # Clean up GitHub URL to extract owner and repo
        github_url = github_url.strip().rstrip('/')
        if github_url.endswith('.git'):
            github_url = github_url[:-4]
        
        # Extract owner and repo from GitHub URL
        parts = github_url.split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        # Construct UIthub URL
        uithub_url = f"https://uithub.com/{owner}/{repo}"
        logger.info(f"Attempting to fetch UIthub data from: {uithub_url}")
        
        # Make request with appropriate headers
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(uithub_url, headers=headers)
        
        if response.status_code == 200:
            uithub_data = response.json()
            
            # Create the correct file path
            file_path = f'uithub_repos/{owner}_{repo}_uithub.json'
            os.makedirs('uithub_repos', exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(uithub_data, f, indent=2)
            
            # Add verification after saving
            if not os.path.exists(file_path):
                logger.error(f"Failed to create file at: {file_path}")
                raise FileNotFoundError(f"Failed to create UIthub file at: {file_path}")
            
            return f'UIthub data extracted and saved to {file_path}'
        else:
            logger.error(f"UIthub request failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:200]}...")  # Log first 200 chars of response
            raise Exception(f'Failed to fetch UIthub data: HTTP {response.status_code}')
    except Exception as e:
        logger.error(f"Error in UIthub extraction: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    app.run(debug=True)
