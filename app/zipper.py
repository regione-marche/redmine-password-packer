import subprocess
import os
import glob
from typing import List

def crea_zip_cifrato(output_dir, ticket_id, password):
    zipfile = f"{output_dir}/ticket_{ticket_id}.zip"
    subprocess.run([
        'zip', '-j', '-P', password, zipfile,
        f"{output_dir}/ticket_{ticket_id}.docx",
        f"{output_dir}/Password_A.png",
        f"{output_dir}/Password_B.png",
        f"{output_dir}/ticket_{ticket_id}_base.png",
        f"{output_dir}/ticket_{ticket_id}_password.txt"
    ], check=True)
    return zipfile


def crea_7z_cifrato(ticket_dir, ticket_id, password):
    """Crea un archivio 7z cifrato contenente il contenuto di `ticket_dir`.
    Restituisce il percorso dell'archivio creato.
    """
    archive = os.path.join(os.path.dirname(ticket_dir), f"ticket_{ticket_id}.7z")

    # Raccogli tutti i file nella directory del ticket
    files = [os.path.join(ticket_dir, f) for f in os.listdir(ticket_dir)]
    if not files:
        raise RuntimeError(f"Nessun file in {ticket_dir} da archiviare")

    # Use '-p' without password so the password isn't visible in process list.
    # 7z will prompt twice for new archives; provide password twice via stdin.
    cmd: List[str] = ['7z', 'a', '-t7z', '-p', archive] + files
    # supply password twice (enter + re-enter) and a final newline
    pw_input = (password + '\n' + password + '\n').encode()
    subprocess.run(cmd, input=pw_input, check=True)
    return archive
