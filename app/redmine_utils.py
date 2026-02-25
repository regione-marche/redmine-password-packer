from redminelib import Redmine
from redminelib.exceptions import ValidationError
import os
from config import REDMINE_URL, API_KEY

redmine = Redmine(REDMINE_URL, key=API_KEY)

def get_tickets_nuovi():
    return redmine.issue.filter(assigned_to_id='me', status_id='1')  # 1 = "Nuovo"


def attach_and_update(issue_id, archive_path, assign_to_id=None, status_id=None, notes=None):
    """Allega `archive_path` all'issue e aggiorna stato/assegnatario se forniti."""
    with open(archive_path, 'rb') as f:
        upload = redmine.upload(f)

    uploads = [{
        'token': upload['token'],
        'filename': os.path.basename(archive_path),
        'content_type': 'application/x-7z-compressed'
    }]

    params = {}
    if notes:
        params['notes'] = notes
    if status_id:
        params['status_id'] = status_id
    if assign_to_id:
        params['assigned_to_id'] = assign_to_id

    params['uploads'] = uploads

    try:
        redmine.issue.update(issue_id, **params)
    except ValidationError as e:
        # Fallback: some projects reject the configured assignee
        # (e.g. user not member of that project). Retry without reassignment.
        err = str(e).lower()
        if assign_to_id and ('assigned' in err or 'assegnato' in err):
            print(f"[!] Assignee {assign_to_id} non valido per ticket {issue_id}: retry senza riassegnazione")
            params.pop('assigned_to_id', None)
            redmine.issue.update(issue_id, **params)
            return
        raise


def create_report_issue(project_identifier, subject, description, assigned_to_id=None, **extra_params):
    """Crea un nuovo issue su Redmine per segnalare progetti mancanti.
    `project_identifier` può essere l'id numerico o l'identificatore del progetto.
    Restituisce l'issue creato.
    """
    params = {
        'subject': subject,
        'description': description,
    }
    if project_identifier:
        params['project_id'] = project_identifier
    if assigned_to_id:
        params['assigned_to_id'] = assigned_to_id
    if extra_params:
        params.update(extra_params)

    if not params.get('project_id'):
        raise ValueError("project_id is required to create an issue")

    issue = redmine.issue.create(**params)
    return issue
