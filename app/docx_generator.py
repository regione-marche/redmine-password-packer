import os
import os.path
# import shutil
import subprocess
from config import TEMPLATE_MD

def generate_md(ticket_dir, image_path):
    print(f"generate_md({ticket_dir}, {image_path})")

    # Prepara HTML nella directory del ticket
    # html_path = os.path.join(ticket_dir, "temp.html")
    md_path = os.path.join(ticket_dir, "temp.md")
    
    # Legge e personalizza il template
    # with open(TEMPLATE_HTML, 'r') as f:
    with open(TEMPLATE_MD, 'r') as f:
        md = f.read()
    #html = html.replace("Password_A.png", os.path.basename(image_path))
    
    # Copia immagine nella dir se non già lì
    # target_img_path = os.path.join(ticket_dir, os.path.basename(image_path))
    # if image_path != target_img_path:
    #     shutil.copy(image_path, target_img_path)

    # Scrive file HTML
    with open(md_path, 'w') as f:
        f.write(md)
    
    return md_path

def html_to_docx(html_path, output_path):
    ticket_dir = os.path.dirname(output_path)
    html_fname = os.path.basename(html_path)
    output_fname = os.path.basename(output_path)

    print(f"in {ticket_dir}: subprocess.run(['pandoc', {html_fname}, '-f', 'html', '-t', 'docx', '-o', {output_fname}]")
    p = subprocess.run(
        ['pandoc', html_fname, '-f', 'html', '-t', 'docx', '-o', output_fname #, '--standalone'
         ]
        , check=True
        , capture_output=True
        , cwd=ticket_dir
        )
    print(f"out: {p.stdout}")
    print(f"err: {p.stderr}")

def md_to_docx(md_path, output_path):
    ticket_dir = os.path.dirname(output_path)
    md_fname = os.path.basename(md_path)
    output_fname = os.path.basename(output_path)

    print(f"in {ticket_dir}: subprocess.run(['pandoc', {md_fname}, '-f', 'markdown', '-t', 'docx', '-o', {output_fname}]")
    p = subprocess.run(
        ['pandoc', md_fname, '-f', 'markdown', '-t', 'docx', '-o', output_fname #, '--standalone'
         ]
        , check=True
        , capture_output=True
        , cwd=ticket_dir
        )
    print(f"out: {p.stdout}")
    print(f"err: {p.stderr}")