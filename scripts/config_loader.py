"""
AEC Demo Portable — Config Loader
All scripts import this to get consistent paths and settings.
"""
import yaml, os
from pathlib import Path

# Always resolve relative to the AEC_Demo_Portable root
_HERE = Path(__file__).parent
ROOT  = _HERE.parent
CONFIG_PATH = ROOT / "config" / "user_config.yaml"

_cfg = None

def load():
    global _cfg
    if _cfg is not None:
        return _cfg
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"user_config.yaml not found at {CONFIG_PATH}\n"
            "Copy config/user_config.example.yaml to config/user_config.yaml and edit the local copy before running."
        )
    with open(CONFIG_PATH) as f:
        _cfg = yaml.safe_load(f)
    return _cfg

def comfyui_url():
    return load()["comfyui"]["url"]

def comfyui_python():
    c = load()["comfyui"]
    return Path(c["install_path"]) / c["python_exe"]

def comfyui_input():
    c = load()["comfyui"]
    return Path(c["install_path"]) / "ComfyUI" / "input"

def comfyui_output():
    c = load()["comfyui"]
    return Path(c["install_path"]) / "ComfyUI" / "output"

def comfyui_workflow():
    """Path to the workflow JSON bundled in this package."""
    return ROOT / "comfyui" / "workflows" / "AEC_Transform_Pipeline.json"

def project_root():
    return Path(load()["project"]["root"])

def sample_project():
    return ROOT / "sample_project"

def assets_hdri():
    return ROOT / "assets" / "hdri"

def blender_exe():
    return Path(load()["blender"]["exe"])

def render_cfg():
    return load()["render"]
