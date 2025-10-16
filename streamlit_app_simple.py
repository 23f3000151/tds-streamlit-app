import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="GitHub App Generator",
    page_icon="🚀",
    layout="wide"
)

def main():
    st.title("🚀 GitHub App Generator - SIMPLE VERSION")
    st.markdown("This version works without the app modules")
    
    st.subheader("Environment Check")
    required_vars = ["GITHUB_TOKEN", "GITHUB_USERNAME", "OPENAI_API_KEY", "USER_SECRET"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            st.success(f"✅ {var}: Set")
        else:
            st.error(f"❌ {var}: Missing")
    
    st.subheader("Test Form")
    with st.form("test_form"):
        brief = st.text_area("Project Brief", "Create a simple web app")
        submitted = st.form_submit_button("Test")
        
        if submitted:
            st.success("Form submitted successfully!")
            st.info("This confirms the basic Streamlit app is working.")

if __name__ == "__main__":
    main()