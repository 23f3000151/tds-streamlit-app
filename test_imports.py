import sys
import os

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

print("Testing imports...")

try:
    from github_utils import create_repo
    print(" github_utils imported successfully")
except ImportError as e:
    print(f" github_utils import failed: {e}")

try:
    from llm_generator import generate_app_code
    print(" llm_generator imported successfully")
except ImportError as e:
    print(f"❌ llm_generator import failed: {e}")

try:
    from notify import notify_evaluation_server
    print("✅ notify imported successfully")
except ImportError as e:
    print(f" notify import failed: {e}")

print("Import test completed.")
