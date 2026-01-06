import os
import re
from pathlib import Path

replacements = {
    r'core\.config\.manager': 'core.config',
    r'core\.agents\.decomposition': 'core.agents',
    r'core\.deimos\.vm': 'core.deimos',
    r'core\.services\.ngrok': 'core.services',
    r'core\.workers\.background': 'core.workers',
    r'core\.batch\.task_generator': 'core.batch_gen',
    r'core\.plugins\.base': 'core.plugin_base',
    r'core\.adapters\.base': 'core.adapter_base',
    r'core\.adapters\.linear': 'core.adapter_linear',
    r'core\.managers\.artifacts': 'core.artifact_manager',
    r'core\.managers\.batch': 'core.batch_manager',
    r'core\.managers\.collaboration': 'core.collaboration_manager',
    r'core\.managers\.health': 'core.health_manager',
    r'core\.managers\.knowledge': 'core.knowledge_manager',
    r'core\.managers\.patch': 'core.patch_manager',
    r'core\.managers\.protocol': 'core.protocol_manager',
    r'core\.managers\.self_healing': 'core.self_healing_manager',
    r'core\.managers\.tasks': 'core.task_manager',
    r'core\.managers\.workspace': 'core.workspace_manager',
    r'core\.web\.app': 'core.web_server',
    r'core\.ipc\.server': 'core.ipc_server',
    r'core\.ipc\.websockets': 'core.ws_manager',
    r'core\.database\.manager': 'core.db_manager',
    r'core\.database\.models': 'core.db_models',
    r'core\.database\.repositories': 'core.db_repositories',
    r'core\.database\.integration': 'core.db_integration',
    r'core\.handoff\.manager': 'core.handoff_manager',
    r'core\.handoff\.anything_llm': 'core.handoff_anything_llm',
    r'core\.handoff\.argo_client': 'core.handoff_argo_client',
    r'core\.handoff\.gitkraken': 'core.handoff_gitkraken',
    r'from core\.database import': 'from core.db_manager import', # Special case for common import pattern
}

def update_file(file_path):
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content = content
        for pattern, replacement in replacements.items():
            new_content = re.sub(pattern, replacement, new_content)
        
        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"Updated: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    root_dir = Path(".")
    extensions = {'.py', '.md', '.json', '.ps1', '.cs', '.csproj', '.sln'}
    
    for file_path in root_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix in extensions:
            if '.venv' in file_path.parts or 'node_modules' in file_path.parts or '.git' in file_path.parts:
                continue
            update_file(file_path)

if __name__ == "__main__":
    main()
