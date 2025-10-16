import streamlit as st
import os
import json
import base64
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Try to import modules with multiple approaches
try:
    # Approach 1: Direct import from app folder
    from app.github_utils import (
        create_repo, create_or_update_file, enable_pages, 
        generate_mit_license, create_or_update_binary_file
    )
    from app.llm_generator import generate_app_code, decode_attachments
    from app.notify import notify_evaluation_server
    st.success("? Modules imported successfully from app package")
except ImportError as e:
    st.error(f"First import attempt failed: {e}")
    try:
        # Approach 2: Try absolute import
        import importlib.util
        spec = importlib.util.spec_from_file_location("github_utils", "app/github_utils.py")
        github_utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(github_utils)
        
        spec = importlib.util.spec_from_file_location("llm_generator", "app/llm_generator.py")
        llm_generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(llm_generator)
        
        spec = importlib.util.spec_from_file_location("notify", "app/notify.py")
        notify = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(notify)
        
        # Create aliases
        create_repo = github_utils.create_repo
        create_or_update_file = github_utils.create_or_update_file
        enable_pages = github_utils.enable_pages
        generate_mit_license = github_utils.generate_mit_license
        create_or_update_binary_file = github_utils.create_or_update_binary_file
        generate_app_code = llm_generator.generate_app_code
        decode_attachments = llm_generator.decode_attachments
        notify_evaluation_server = notify.notify_evaluation_server
        
        st.success("? Modules imported successfully using importlib")
    except Exception as e2:
        st.error(f"Second import attempt failed: {e2}")
        st.stop()

# Initialize session state
if 'processed_requests' not in st.session_state:
    st.session_state.processed_requests = {}
if 'current_task' not in st.session_state:
    st.session_state.current_task = None

def load_processed():
    """Load processed requests from session state"""
    return st.session_state.processed_requests

def save_processed(data):
    """Save processed requests to session state"""
    st.session_state.processed_requests = data

def process_request(data):
    """Main processing function adapted from FastAPI"""
    try:
        round_num = data.get("round", 1)
        task_id = data["task"]
        
        st.info(f"Starting processing for task {task_id} (round {round_num})")
        
        # Process attachments
        attachments = data.get("attachments", [])
        saved_attachments = decode_attachments(attachments)
        
        # Generate code
        gen = generate_app_code(
            data["brief"],
            attachments=attachments,
            checks=data.get("checks", []),
            round_num=round_num,
            prev_readme=None
        )
        
        files = gen.get("files", {})
        
        # Create repository
        repo = create_repo(task_id, description=f"Auto-generated app for task: {data['brief']}")
        
        # Handle files based on round
        for fname, content in files.items():
            create_or_update_file(repo, fname, content, f"Add/Update {fname}")
        
        # Add LICENSE
        mit_text = generate_mit_license()
        create_or_update_file(repo, "LICENSE", mit_text, "Add MIT license")
        
        # Enable GitHub Pages for round 1
        username = os.getenv('GITHUB_USERNAME')
        if round_num == 1:
            pages_ok = enable_pages(task_id)
            pages_url = f"https://{username}.github.io/{task_id}/" if pages_ok else None
        else:
            pages_ok = True
            pages_url = f"https://{username}.github.io/{task_id}/"
        
        # Get commit SHA
        try:
            commit_sha = repo.get_commits()[0].sha
        except Exception:
            commit_sha = None
        
        # Prepare payload for evaluation server
        payload = {
            "email": data["email"],
            "task": data["task"],
            "round": round_num,
            "nonce": data["nonce"],
            "repo_url": repo.html_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url,
        }
        
        # Notify evaluation server
        notification_success = notify_evaluation_server(data["evaluation_url"], payload)
        
        # Store in processed requests
        processed = load_processed()
        key = f"{data['email']}::{data['task']}::round{round_num}::nonce{data['nonce']}"
        processed[key] = payload
        save_processed(processed)
        
        return payload, notification_success
        
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        return None, False

def main():
    st.set_page_config(
        page_title="GitHub App Generator",
        page_icon="??",
        layout="wide"
    )
    
    st.title("?? GitHub App Generator")
    st.markdown("Generate and deploy web applications directly to GitHub")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.info("Ensure your environment variables are set in Streamlit Secrets")
        
        # Display current configuration
        if st.button("Check Configuration"):
            required_vars = ["GITHUB_TOKEN", "GITHUB_USERNAME", "OPENAI_API_KEY", "USER_SECRET"]
            for var in required_vars:
                value = os.getenv(var)
                if value:
                    st.success(f"? {var}: Set")
                else:
                    st.error(f"? {var}: Missing")
    
    # Main form
    with st.form("app_generator_form"):
        st.header("Create New Application")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email", placeholder="user@example.com")
            task_id = st.text_input("Task ID", placeholder="my-web-app")
            round_num = st.selectbox("Round", [1, 2], help="Round 1: New app, Round 2: Update existing")
            secret = st.text_input("Secret Key", type="password")
        
        with col2:
            nonce = st.text_input("Nonce", value=str(int(time.time())))
            evaluation_url = st.text_input("Evaluation URL", placeholder="https://your-evaluation-server.com/notify")
        
        brief = st.text_area(
            "Project Brief", 
            placeholder="Describe the web application you want to create...",
            height=100
        )
        
        checks = st.text_area(
            "Evaluation Checks (one per line)",
            placeholder="Check 1: Must have responsive design\nCheck 2: Must include dark mode",
            height=80
        )
        
        # File upload for attachments
        uploaded_files = st.file_uploader(
            "Attachments (optional)",
            accept_multiple_files=True,
            help="Upload any reference files for the AI"
        )
        
        submitted = st.form_submit_button("Generate Application")
    
    # Process form submission
    if submitted:
        if not all([email, task_id, brief, secret]):
            st.error("Please fill in all required fields")
            return
        
        # Verify secret
        if secret != os.getenv("USER_SECRET"):
            st.error("Invalid secret key")
            return
        
        # Prepare data
        data = {
            "email": email,
            "task": task_id,
            "round": round_num,
            "nonce": nonce,
            "evaluation_url": evaluation_url,
            "brief": brief,
            "checks": checks.split('\n') if checks else [],
            "secret": secret,
            "attachments": []
        }
        
        # Process uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.getvalue()
                mime_type = uploaded_file.type or "application/octet-stream"
                b64_content = base64.b64encode(file_content).decode('utf-8')
                data_url = f"data:{mime_type};base64,{b64_content}"
                
                data["attachments"].append({
                    "name": uploaded_file.name,
                    "url": data_url
                })
        
        # Process the request
        with st.spinner("Generating your application..."):
            result, success = process_request(data)
            
            if result:
                st.success("? Application generated successfully!")
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Repository", result["task"])
                    st.write(f"[View Repo]({result['repo_url']})")
                
                with col2:
                    if result["pages_url"]:
                        st.metric("GitHub Pages", "Enabled")
                        st.write(f"[View Site]({result['pages_url']})")
                    else:
                        st.metric("GitHub Pages", "Not Enabled")
                
                with col3:
                    if result["commit_sha"]:
                        st.metric("Latest Commit", result["commit_sha"][:8])
                
                if not success:
                    st.warning("?? Could not notify evaluation server")
            else:
                st.error("? Failed to generate application")
    
    # Display processed requests
    st.header("Recent Requests")
    processed = load_processed()
    if processed:
        for key, request_data in list(processed.items())[-5:]:
            with st.expander(f"Request: {request_data['task']} - Round {request_data['round']}"):
                st.json(request_data)
    else:
        st.info("No processed requests yet")

if __name__ == "__main__":
    main()
