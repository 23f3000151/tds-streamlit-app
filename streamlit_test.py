import streamlit as st
import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

st.set_page_config(page_title='Import Test', page_icon='')

try:
    from github_utils import create_repo
    st.success(' github_utils imported successfully')
except ImportError as e:
    st.error(f' github_utils import failed: {e}')

try:
    from llm_generator import generate_app_code
    st.success(' llm_generator imported successfully')
except ImportError as e:
    st.error(f'❌ llm_generator import failed: {e}')

try:
    from notify import notify_evaluation_server
    st.success('✅ notify imported successfully')
except ImportError as e:
    st.error(f'❌ notify import failed: {e}')

st.info('If all show , your app is ready for deployment!')
