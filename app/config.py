import os

from dotenv import load_dotenv
import yaml

load_dotenv()

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Paths to configuration files
CONFIG_YAML = os.getenv("CONFIG_YAML", "config.yml")
PROJECTS_YAML = os.getenv("PROJECTS_YAML", "projects.yml")


# Default/fallback values
REDMINE_URL = os.getenv("REDMINE_URL", "https://pass.regione.marche.it")
API_KEY = os.getenv("REDMINE_API_KEY", "CHANGEME")
ARCHIVE_PASSWORD = os.getenv("ARCHIVE_PASSWORD", "pippo")

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
TEMPLATE_HTML = "/app/static/template.html"
TEMPLATE_MD = "/app/static/template.md"
SCRIPT_VISUAL = "/app/visual_cryptography_py3__versione2 1 1.py"
OUTPUT_DIR = "output"
ZIP_PWD = "Open@ctIPTS11"
TEMPLATE_DOCX = "/app/static/template.docx"

ASSIGN_TO_ID = os.getenv("ASSIGN_TO_ID")
RESOLVED_STATUS_ID = os.getenv("RESOLVED_STATUS_ID", "3")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

PROJECT_DEFINITIONS = {}
PROJECT_PASSWORDS = {}
PROJECT_TICKET_PARAMS = {}
PROJECT_DOCX_TEMPLATES = {}
REPORT_CONFIG = {}
_CFG = {}


def _resolve_path(path: str):
    """Resolve relative paths regardless of the current working directory."""
    if not path:
        return path
    if os.path.isabs(path):
        return path

    candidates = [
        path,
        os.path.join(PROJECT_ROOT, path),
        os.path.join(APP_DIR, path),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    # Fallback to project-root relative for consistency.
    return os.path.join(PROJECT_ROOT, path)


def _load_yaml(path: str):
    for candidate in [path, _resolve_path(path)]:
        if not candidate:
            continue
        try:
            with open(candidate, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            continue
    return {}


def _extract_projects_section(data):
    if not isinstance(data, dict):
        return {}
    if "projects" in data and isinstance(data["projects"], dict):
        return data["projects"] or {}
    return data


def _normalize_projects(projects_map):
    """Normalize project config into:
    - passwords: project_key -> archive password
    - ticket_params: project_key -> params for redmine.issue.create
    - docx_templates: project_key -> custom docx template path

    Supported format:
    projects:
      my-project:
        password: "password"
        docx_template: "/path/template_project.docx"
        ticket:
          project_id: 12
          category_id: 5
          assigned_to_id: 3
    """
    passwords = {}
    ticket_params = {}
    docx_templates = {}

    if not isinstance(projects_map, dict):
        return passwords, ticket_params, docx_templates

    for project_key, value in projects_map.items():
        key = str(project_key)

        if not isinstance(value, dict):
            raise ValueError(
                f"Invalid configuration for project '{key}': expected a mapping "
                f"(e.g. {{password: '...', ticket: {{...}}}}), got {type(value).__name__}"
            )

        archive_pw = value.get("password")
        if archive_pw is not None:
            passwords[key] = str(archive_pw)

        docx_tpl = value.get("docx_template")
        if docx_tpl is None and isinstance(value.get("templates"), dict):
            docx_tpl = value.get("templates", {}).get("docx")
        if docx_tpl:
            docx_templates[key] = str(docx_tpl)

        ticket_cfg = value.get("ticket")
        if isinstance(ticket_cfg, dict) and ticket_cfg:
            ticket_params[key] = dict(ticket_cfg)
            continue

        # Optional flat ticket params in the same project block
        flat_ticket = {
            k: v
            for k, v in value.items()
            if k
            not in {
                "password",
                "docx_template",
                "templates",
                "ticket",
            }
        }
        if flat_ticket:
            ticket_params[key] = flat_ticket

    return passwords, ticket_params, docx_templates


def _load_project_definitions(main_cfg):
    projects = {}

    inline_projects = _extract_projects_section(main_cfg.get("projects", {}))
    if isinstance(inline_projects, dict):
        projects.update(inline_projects)

    projects_file = main_cfg.get("projects_yaml") or main_cfg.get("projects_file") or PROJECTS_YAML
    file_payload = _load_yaml(projects_file)
    file_projects = _extract_projects_section(file_payload)
    if isinstance(file_projects, dict):
        projects.update(file_projects)

    return projects


def _load_config(path: str = None):
    return _load_yaml(path or CONFIG_YAML)


def load_project_passwords(path: str = None):
    """Backward-compatible helper to load only project passwords.

    If a file path is provided, it reads that file directly.
    Otherwise, it returns passwords from the merged runtime configuration.
    """
    if path:
        payload = _load_yaml(path)
        projects = _extract_projects_section(payload)
        passwords, _, _ = _normalize_projects(projects)
        return passwords
    return dict(PROJECT_PASSWORDS)


def _apply_config_values(cfg):
    global REDMINE_URL, API_KEY, OUTPUT_DIR, TEMPLATE_DOCX, SCRIPT_VISUAL, FONT_PATH
    global ARCHIVE_PASSWORD, PROJECT_DEFINITIONS, PROJECT_PASSWORDS, PROJECT_TICKET_PARAMS, PROJECT_DOCX_TEMPLATES
    global REPORT_CONFIG, ASSIGN_TO_ID, RESOLVED_STATUS_ID, LOG_LEVEL

    REDMINE_URL = cfg.get("redmine", {}).get("url", REDMINE_URL)
    API_KEY = cfg.get("redmine", {}).get("api_key", API_KEY)

    OUTPUT_DIR = cfg.get("output", {}).get("dir", OUTPUT_DIR)
    TEMPLATE_DOCX = _resolve_path(cfg.get("templates", {}).get("docx", TEMPLATE_DOCX))

    SCRIPT_VISUAL = _resolve_path(cfg.get("visual", {}).get("script", SCRIPT_VISUAL))
    FONT_PATH = _resolve_path(cfg.get("visual", {}).get("font", FONT_PATH))

    ARCHIVE_PASSWORD = cfg.get("archive", {}).get("default_password", ARCHIVE_PASSWORD)

    project_defs = _load_project_definitions(cfg)
    project_pw, project_ticket, project_docx_templates = _normalize_projects(project_defs)
    PROJECT_DEFINITIONS = project_defs
    PROJECT_PASSWORDS = project_pw
    PROJECT_TICKET_PARAMS = project_ticket
    PROJECT_DOCX_TEMPLATES = {k: _resolve_path(v) for k, v in project_docx_templates.items()}

    REPORT_CONFIG = cfg.get("report_missing_project", {}) or {}

    ASSIGN_TO_ID = cfg.get("redmine", {}).get("assign_to_id", ASSIGN_TO_ID)
    RESOLVED_STATUS_ID = cfg.get("redmine", {}).get("resolved_status_id", RESOLVED_STATUS_ID)
    LOG_LEVEL = str(cfg.get("logging", {}).get("level", LOG_LEVEL)).upper()


def reload_config(path: str = None):
    """Ricarica la configurazione da YAML e aggiorna le variabili in questo modulo."""
    global _CFG
    _CFG = _load_config(path)
    _apply_config_values(_CFG)


# Load configuration at import time
reload_config()
