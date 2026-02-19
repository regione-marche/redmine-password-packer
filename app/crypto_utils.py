import subprocess
import os
import shutil

from config import SCRIPT_VISUAL

def run_visual_crypto(base_img_path):
    ticket_dir = os.path.dirname(base_img_path)
    print(ticket_dir)
    img_name = os.path.basename(base_img_path)
    
    # Copia immagine nella sottodirectory di lavoro
    temp_img_path = os.path.join(ticket_dir, img_name)
    if base_img_path != temp_img_path:
        shutil.copy(base_img_path, temp_img_path)

    # Esegui lo script dalla directory specifica
    subprocess.run(
        ['python', SCRIPT_VISUAL, img_name],
        check=True,
        cwd=ticket_dir
    )

    # File risultanti
    a_path = os.path.join(ticket_dir, "Password_A.png")
    b_path = os.path.join(ticket_dir, "Password_B.png")
    return a_path, b_path
