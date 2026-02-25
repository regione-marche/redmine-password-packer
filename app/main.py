import argparse
import os
import subprocess
import sys

from redmine_utils import get_tickets_nuovi, attach_and_update, create_report_issue
from password_utils import genera_password, crea_immagine
from crypto_utils import run_visual_crypto
# No markdown generation needed when using mkdocx.py directly
from zipper import crea_7z_cifrato
from config import (
    OUTPUT_DIR,
    ARCHIVE_PASSWORD,
    TEMPLATE_DOCX,
    ASSIGN_TO_ID,
    RESOLVED_STATUS_ID,
    PROJECT_PASSWORDS,
    PROJECT_TICKET_PARAMS,
    PROJECT_DOCX_TEMPLATES,
    REPORT_CONFIG,
)

def run(ticket_ids=None):
    tickets = get_tickets_nuovi() if ticket_ids is None else [{"id": tid} for tid in ticket_ids]
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # progetto->password già fornita da CONFIG YAML
    proj_pw = PROJECT_PASSWORDS or {}
    proj_docx_templates = PROJECT_DOCX_TEMPLATES or {}

    for ticket in tickets:
        ticket_id = ticket['id']
        ticket_dir = os.path.join(OUTPUT_DIR, f"ticket_{ticket_id}")
        os.makedirs(ticket_dir, exist_ok=True)

        project_key = None
        try:
            proj = getattr(ticket, 'project', None)
            if proj is not None:
                project_key = getattr(proj, 'identifier', None) or getattr(proj, 'name', None) or getattr(proj, 'id', None)
        except Exception:
            project_key = None

        # 1) genera password e la salva in ticket_dir
        password = genera_password()
        with open(os.path.join(ticket_dir, f"ticket_{ticket_id}_password.txt"), 'w') as f:
            f.write(password)

        # 2) crea immagine base nella directory del ticket
        base_img = crea_immagine(password, ticket_id, ticket_dir)

        # 3) applica crittografia visuale -> Password_A.png, Password_B.png
        A_img, B_img = run_visual_crypto(base_img)

        # 4) genera il DOCX usando mkdocx.py e il template DOCX
        docx_out = os.path.join(ticket_dir, f"ticket_{ticket_id}.docx")
        mkdocx_py = os.path.join(os.path.dirname(__file__), 'mkdocx.py')
        project_docx_template = TEMPLATE_DOCX
        if project_key is not None and str(project_key) in proj_docx_templates:
            project_docx_template = proj_docx_templates[str(project_key)]
        subprocess.run([sys.executable, mkdocx_py, '--template', project_docx_template, '--image', A_img, '--out', docx_out], check=True)

        # 6) comprimi la directory del ticket in 7z cifrato
        # Determina la password per il progetto del ticket (se presente nel YAML),
        # altrimenti usa ARCHIVE_PASSWORD. Se il progetto non è noto, apri un ticket di segnalazione e salta il ticket.
        pw = ARCHIVE_PASSWORD
        if project_key is not None:
            if str(project_key) in proj_pw:
                pw = proj_pw.get(str(project_key), pw)
            else:
                # progetto non trovato nella mappa: apri ticket di segnalazione usando la configurazione
                report = REPORT_CONFIG or {}
                report_project = report.get('project')
                report_assignee = report.get('assigned_to_id')
                # Allow per-project overrides for issue creation fields.
                report_ticket_defaults = {}
                if isinstance(report.get('ticket'), dict):
                    report_ticket_defaults.update(report.get('ticket'))
                project_ticket_overrides = PROJECT_TICKET_PARAMS.get(str(project_key), {})
                if isinstance(project_ticket_overrides, dict):
                    report_ticket_defaults.update(project_ticket_overrides)
                subj_t = report.get('subject', 'Segnalazione: progetto mancante {project}')
                desc_t = report.get('description', 'Il progetto {project} (ticket {ticket}) non è presente nella configurazione.')
                subject = subj_t.format(project=project_key, ticket=ticket_id)
                description = desc_t.format(project=project_key, ticket=ticket_id)
                report_created = False
                try:
                    project_id = report_ticket_defaults.pop('project_id', report_project)
                    assigned_to_id = report_ticket_defaults.pop('assigned_to_id', report_assignee)
                    if report_ticket_defaults.get('project') and not project_id:
                        project_id = report_ticket_defaults.pop('project')
                    category_id = report_ticket_defaults.get('category_id')
                    if category_id in (None, "") and assigned_to_id in (None, ""):
                        raise ValueError(
                            "Configurazione ticket non valida: se 'category_id' non è valorizzato, "
                            "'assigned_to_id' è obbligatorio."
                        )
                    create_report_issue(
                        project_id,
                        subject,
                        description,
                        assigned_to_id=assigned_to_id,
                        **report_ticket_defaults,
                    )
                    report_created = True
                except Exception as e:
                    print(f"Errore creando ticket di segnalazione per progetto {project_key}: {e}")
                if report_created:
                    print(f"[!] Progetto {project_key} non in configurazione: aperto ticket di segnalazione, skip ticket {ticket_id}")
                else:
                    print(f"[!] Progetto {project_key} non in configurazione: ticket di segnalazione non creato, skip ticket {ticket_id}")
                continue

        archive_path = crea_7z_cifrato(ticket_dir, ticket_id, pw)

        # 7) aggiorna il ticket su Redmine: allega, risolve, assegna (se configurato)
        notes = f"Automated: allegato {os.path.basename(archive_path)}. Chiudo ticket."
        attach_and_update(ticket_id, archive_path, assign_to_id=ASSIGN_TO_ID, status_id=RESOLVED_STATUS_ID, notes=notes)

        print(f"[✓] Ticket {ticket_id} completato: {archive_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redmine Password Visual Packer")
    parser.add_argument('--ticket-id', type=int, nargs='*', help="Specifica uno o più ID ticket manualmente")
    args = parser.parse_args()
    run(ticket_ids=args.ticket_id)
