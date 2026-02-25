import argparse
import logging
import os
import shutil
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
    LOG_LEVEL,
)

DIR_MODE = 0o700
FILE_MODE = 0o600
logger = logging.getLogger(__name__)


def _safe_chmod(path, mode):
    try:
        os.chmod(path, mode)
    except PermissionError:
        # On bind-mounted paths we may not own files/dirs; keep processing.
        pass


def _ensure_secure_dir(path):
    os.makedirs(path, mode=DIR_MODE, exist_ok=True)
    _safe_chmod(path, DIR_MODE)


def _ensure_secure_file(path):
    if os.path.isfile(path):
        _safe_chmod(path, FILE_MODE)


def _ensure_secure_tree(root):
    if not os.path.isdir(root):
        return
    _safe_chmod(root, DIR_MODE)
    for dirpath, dirnames, filenames in os.walk(root):
        _safe_chmod(dirpath, DIR_MODE)
        for dirname in dirnames:
            _safe_chmod(os.path.join(dirpath, dirname), DIR_MODE)
        for filename in filenames:
            _ensure_secure_file(os.path.join(dirpath, filename))


def _cleanup_sensitive_artifacts(ticket_dir, archive_path=None):
    if os.path.isdir(ticket_dir):
        shutil.rmtree(ticket_dir)
    if archive_path and os.path.exists(archive_path):
        os.remove(archive_path)


def _resolve_writable_output_dir(preferred_dir):
    """Return a writable output directory, falling back to /tmp when needed."""
    try:
        _ensure_secure_dir(preferred_dir)
        probe = os.path.join(preferred_dir, ".write_probe")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return preferred_dir
    except Exception as e:
        fallback = "/tmp/redmine-password-packer-output"
        logger.warning(
            "Output dir '%s' is not writable (%s). Falling back to '%s'.",
            preferred_dir,
            e,
            fallback,
        )
        _ensure_secure_dir(fallback)
        return fallback


def run(ticket_ids=None):
    if ticket_ids is None:
        tickets = list(get_tickets_nuovi())
        logger.info("Fetched %d ticket(s) assigned to current user with status 'New'", len(tickets))
    else:
        tickets = [{"id": tid} for tid in ticket_ids]
        logger.info("Running in manual mode for ticket ids: %s", ticket_ids)
    run_output_dir = _resolve_writable_output_dir(OUTPUT_DIR)

    # progetto->password già fornita da CONFIG YAML
    proj_pw = PROJECT_PASSWORDS or {}
    proj_docx_templates = PROJECT_DOCX_TEMPLATES or {}

    for ticket in tickets:
        ticket_id = ticket['id']
        ticket_dir = os.path.join(run_output_dir, f"ticket_{ticket_id}")
        _ensure_secure_dir(ticket_dir)
        logger.debug("Processing ticket id=%s in dir=%s", ticket_id, ticket_dir)

        project_key = None
        try:
            proj = getattr(ticket, 'project', None)
            if proj is not None:
                project_key = getattr(proj, 'identifier', None) or getattr(proj, 'name', None) or getattr(proj, 'id', None)
        except Exception:
            project_key = None
        logger.debug("Ticket %s project key resolved to: %s", ticket_id, project_key)

        # 1) genera password e la salva in ticket_dir
        password = genera_password()
        password_file = os.path.join(ticket_dir, f"ticket_{ticket_id}_password.txt")
        with open(password_file, 'w') as f:
            f.write(password)
        _ensure_secure_file(password_file)

        # 2) crea immagine base nella directory del ticket
        base_img = crea_immagine(password, ticket_id, ticket_dir)

        # 3) applica crittografia visuale -> Password_A.png, Password_B.png
        A_img, B_img = run_visual_crypto(base_img)
        _ensure_secure_file(base_img)
        _ensure_secure_file(A_img)
        _ensure_secure_file(B_img)

        # 4) genera il DOCX usando mkdocx.py e il template DOCX
        docx_out = os.path.join(ticket_dir, f"ticket_{ticket_id}.docx")
        mkdocx_py = os.path.join(os.path.dirname(__file__), 'mkdocx.py')
        project_docx_template = TEMPLATE_DOCX
        if project_key is not None and str(project_key) in proj_docx_templates:
            project_docx_template = proj_docx_templates[str(project_key)]
        logger.debug("Ticket %s DOCX template: %s", ticket_id, project_docx_template)
        subprocess.run([sys.executable, mkdocx_py, '--template', project_docx_template, '--image', A_img, '--out', docx_out], check=True)
        _ensure_secure_file(docx_out)

        # 6) comprimi la directory del ticket in 7z cifrato
        # Determina la password per il progetto del ticket (se presente nel YAML),
        # altrimenti usa ARCHIVE_PASSWORD. Se il progetto non è noto, apri un ticket di segnalazione e salta il ticket.
        pw = ARCHIVE_PASSWORD
        project_ticket_cfg = {}
        if project_key is not None:
            project_ticket_cfg = PROJECT_TICKET_PARAMS.get(str(project_key), {}) or {}
            if str(project_key) in proj_pw:
                pw = proj_pw.get(str(project_key), pw)
                logger.debug("Ticket %s using project-specific archive password", ticket_id)
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
                _cleanup_sensitive_artifacts(ticket_dir)
                continue

        _ensure_secure_tree(ticket_dir)
        archive_path = crea_7z_cifrato(ticket_dir, ticket_id, pw)
        logger.debug("Ticket %s archive created at %s", ticket_id, archive_path)
        _ensure_secure_file(archive_path)

        # 7) aggiorna il ticket su Redmine: allega, risolve, assegna (se configurato)
        notes = f"Automated: allegato {os.path.basename(archive_path)}. Chiudo ticket."
        update_assign_to_id = ASSIGN_TO_ID
        update_category_id = None
        if isinstance(project_ticket_cfg, dict):
            update_category_id = project_ticket_cfg.get('category_id')
            if project_ticket_cfg.get('assigned_to_id') not in (None, ''):
                update_assign_to_id = project_ticket_cfg.get('assigned_to_id')
        attach_and_update(
            ticket_id,
            archive_path,
            assign_to_id=update_assign_to_id,
            status_id=RESOLVED_STATUS_ID,
            notes=notes,
            category_id=update_category_id,
        )
        _cleanup_sensitive_artifacts(ticket_dir, archive_path)

        print(f"[✓] Ticket {ticket_id} completato: archivio caricato e artefatti locali rimossi")

if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.debug("current userid: %s", os.getuid())
    parser = argparse.ArgumentParser(description="Redmine Password Visual Packer")
    parser.add_argument('--ticket-id', type=int, nargs='*', help="Specifica uno o più ID ticket manualmente")
    args = parser.parse_args()
    run(ticket_ids=args.ticket_id)
