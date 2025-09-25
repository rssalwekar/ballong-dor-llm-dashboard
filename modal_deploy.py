import shlex
import subprocess
from pathlib import Path
import os
from dotenv import load_dotenv

import modal

# Load environment variables from .env file
load_dotenv()

streamlit_script_local_path = Path(__file__).parent / "app.py"
streamlit_script_remote_path = "/root/app.py"

# Create Modal image with all required dependencies
image = (
    modal.Image.debian_slim()
    .uv_pip_install(
        "streamlit", 
        "supabase", 
        "pandas", 
        "plotly", 
        "python-dotenv"
    )
    .env({"FORCE_REBUILD": "true", "BUILD_TIMESTAMP": str(int(__import__("time").time()))})  # Force rebuild to get latest changes
    .add_local_file(streamlit_script_local_path, streamlit_script_remote_path)
)

# Create secret for environment variables
secret = modal.Secret.from_name("my-secret")

# Create Modal app
volume = modal.Volume.from_name("my-data")
app = modal.App(
    image=image, 
    secrets=[secret], 
    volumes={"/mnt/data": volume},
    name="ballon-dor-2025",
) 

# Check if streamlit script exists
if not streamlit_script_local_path.exists():
    raise RuntimeError(
        "Streamlit script not found. Make sure app.py exists in the same directory."
    )

@app.function()
@modal.web_server(8000)
def run():
    target = shlex.quote(streamlit_script_remote_path)
    cmd = f"streamlit run {target} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false"
    
    # Build environment variables, filtering out None values
    env_vars = {}
    if os.getenv("SUPABASE_KEY"):
        env_vars["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY")
    if os.getenv("SUPABASE_URL"):
        env_vars["SUPABASE_URL"] = os.getenv("SUPABASE_URL")
    
    # Include current environment to ensure PATH and other essential vars are available
    env_vars.update(os.environ)
        
    subprocess.Popen(cmd, shell=True, env=env_vars)
