import subprocess
import os
import shutil
import sys

from config import SCRIPT_VISUAL


def _validate_visual_script(path):
    """Allow execution only of trusted visual script inside app directory."""
    script_path = os.path.abspath(path)
    app_dir = os.path.dirname(os.path.abspath(__file__))
    script_name = os.path.basename(script_path)

    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Visual script not found: {script_path}")
    if os.path.dirname(script_path) != app_dir:
        raise ValueError(f"Visual script must be inside {app_dir}: {script_path}")
    if not script_name.startswith("visual_cryptography_py3__"):
        raise ValueError(f"Visual script name not allowed: {script_name}")
    return script_path


def run_visual_crypto(base_img_path):
    ticket_dir = os.path.dirname(base_img_path)
    script_visual = _validate_visual_script(SCRIPT_VISUAL)
    img_name = os.path.basename(base_img_path)
    
    # Copia immagine nella sottodirectory di lavoro
    temp_img_path = os.path.join(ticket_dir, img_name)
    if base_img_path != temp_img_path:
        shutil.copy(base_img_path, temp_img_path)

    # Esegui lo script dalla directory specifica
    subprocess.run(
        [sys.executable, script_visual, img_name],
        check=True,
        cwd=ticket_dir
    )

    # File risultanti
    a_path = os.path.join(ticket_dir, "Password_A.png")
    b_path = os.path.join(ticket_dir, "Password_B.png")
    return a_path, b_path
