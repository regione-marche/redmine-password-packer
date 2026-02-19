from redminelib import Redmine
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

    redmine.issue.update(issue_id, **params)


def create_report_issue(project_identifier, subject, description, assigned_to_id=None):
    """Crea un nuovo issue su Redmine per segnalare progetti mancanti.
    `project_identifier` può essere l'id numerico o l'identificatore del progetto.
    Restituisce l'issue creato.
    """
    params = {
        'project_id': project_identifier,
        'subject': subject,
        'description': description,
    }
    if assigned_to_id:
        params['assigned_to_id'] = assigned_to_id

    issue = redmine.issue.create(**params)
    return issue
