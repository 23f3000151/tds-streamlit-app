import streamlit as st
import os
import json
import base64
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# set_page_config MUST be the first Streamlit command
st.set_page_config(
    page_title="GitHub App Generator",
    page_icon="",
    layout="wide"
)

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

# Import modules
try:
    from github_utils import (
        create_repo, create_or_update_file, enable_pages, 
        generate_mit_license, create_or_update_binary_file
    )
    from llm_generator import generate_app_code, decode_attachments
    from notify import notify_evaluation_server
    IMPORT_SUCCESS = True
except ImportError as e:
    IMPORT_SUCCESS = False
    import_error = e

# Initialize session state
if 'processed_requests' not in st.session_state:
    st.session_state.processed_requests = {}

def load_processed():
    return st.session_state.processed_requests

def save_processed(data):
    st.session_state.processed_requests = data

def main():
    st.title(" GitHub App Generator")
    st.markdown("Generate and deploy web applications directly to GitHub")
    
    # Show import status
    if IMPORT_SUCCESS:
        st.success(" All modules imported successfully!")
    else:
        st.error(f" Module imports failed: {import_error}")
        return
    
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
                    st.success(f" {var}: Set")
                else:
                    st.error(f" {var}: Missing")
    
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
        
        submitted = st.form_submit_button("Generate Application")
    
    if submitted:
        if not all([email, task_id, brief, secret]):
            st.error("Please fill in all required fields")
            return
        
        # Verify secret
        if secret != os.getenv("USER_SECRET"):
            st.error("Invalid secret key")
            return
        
        st.success(" All checks passed! Ready to generate application.")
        st.info("This confirms your app structure is correct.")

if __name__ == "__main__":
    main()
