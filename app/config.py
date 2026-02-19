import os
from dotenv import load_dotenv
import yaml

load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL", "https://pass.regione.marche.it")
API_KEY = os.getenv("REDMINE_API_KEY", "CHANGEME")
ARCHIVE_PASSWORD = os.getenv("ARCHIVE_PASSWORD", "pippo")

FONT_PATH = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
TEMPLATE_HTML = '/app/static/template.html'
TEMPLATE_MD = '/app/static/template.md'
SCRIPT_VISUAL = '/app/visual_cryptography_py3__versione2 1 1.py'
OUTPUT_DIR = 'output'
ZIP_PWD = 'Open@ctIPTS11'
TEMPLATE_DOCX = '/app/static/template.docx'

# Redmine update defaults
ASSIGN_TO_ID = os.getenv('ASSIGN_TO_ID')  # leave None to not reassign
RESOLVED_STATUS_ID = os.getenv('RESOLVED_STATUS_ID', '3')  # default to 3 (Resolved)
PROJECTS_YAML = os.getenv('PROJECTS_YAML', 'projects.yaml')


def load_project_passwords(path: str = None):
	"""Carica la mappa progetto -> password da file YAML.
	Restituisce un dizionario; se il file non esiste ritorna {}.
	"""
	p = path or PROJECTS_YAML
	try:
		with open(p, 'r') as f:
			data = yaml.safe_load(f) or {}
			# aspettarsi struttura {'projects': {<key>: <password>, ...}}
			if isinstance(data, dict) and 'projects' in data:
				return data['projects'] or {}
			# fallback: file può essere direttamente mappa
			if isinstance(data, dict):
				return data
	except FileNotFoundError:
		return {}
	import os
	import yaml

	# Path to main YAML config (can be overridden via env var)
	CONFIG_YAML = os.getenv('CONFIG_YAML', 'config.yaml')


	def _load_config(path: str = None):
		p = path or CONFIG_YAML
		try:
			with open(p, 'r') as f:
				return yaml.safe_load(f) or {}
		except FileNotFoundError:
			return {}


	# Load configuration at import time
	_CFG = _load_config()

	# Redmine / app settings
	REDMINE_URL = _CFG.get('redmine', {}).get('url', 'https://pass.regione.marche.it')
	API_KEY = _CFG.get('redmine', {}).get('api_key')

	# Output and template settings
	OUTPUT_DIR = _CFG.get('output', {}).get('dir', 'output')
	TEMPLATE_DOCX = _CFG.get('templates', {}).get('docx', '/app/static/template.docx')

	# Visual script and fonts
	SCRIPT_VISUAL = _CFG.get('visual', {}).get('script', '/app/visual_cryptography_py3__versione2 1 1.py')
	FONT_PATH = _CFG.get('visual', {}).get('font', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')

	# Archive defaults
	ARCHIVE_PASSWORD = _CFG.get('archive', {}).get('default_password', None)

	# Project-specific passwords: mapping project_identifier -> password
	PROJECT_PASSWORDS = _CFG.get('projects', {}) or {}

	# Behavior for reporting missing projects
	REPORT_CONFIG = _CFG.get('report_missing_project', {}) or {}

	# Redmine update defaults
	ASSIGN_TO_ID = _CFG.get('redmine', {}).get('assign_to_id')
	RESOLVED_STATUS_ID = _CFG.get('redmine', {}).get('resolved_status_id', '3')


	def reload_config(path: str = None):
		"""Ricarica la configurazione da YAML e aggiorna le variabili in questo modulo.
		(utile per i test)
		"""
		global _CFG, REDMINE_URL, API_KEY, OUTPUT_DIR, TEMPLATE_DOCX, SCRIPT_VISUAL, FONT_PATH, ARCHIVE_PASSWORD, PROJECT_PASSWORDS, REPORT_CONFIG, ASSIGN_TO_ID, RESOLVED_STATUS_ID
		_CFG = _load_config(path)
		REDMINE_URL = _CFG.get('redmine', {}).get('url', REDMINE_URL)
		API_KEY = _CFG.get('redmine', {}).get('api_key', API_KEY)
		OUTPUT_DIR = _CFG.get('output', {}).get('dir', OUTPUT_DIR)
		TEMPLATE_DOCX = _CFG.get('templates', {}).get('docx', TEMPLATE_DOCX)
		SCRIPT_VISUAL = _CFG.get('visual', {}).get('script', SCRIPT_VISUAL)
		FONT_PATH = _CFG.get('visual', {}).get('font', FONT_PATH)
		ARCHIVE_PASSWORD = _CFG.get('archive', {}).get('default_password', ARCHIVE_PASSWORD)
		PROJECT_PASSWORDS = _CFG.get('projects', {}) or PROJECT_PASSWORDS
		REPORT_CONFIG = _CFG.get('report_missing_project', {}) or REPORT_CONFIG
		ASSIGN_TO_ID = _CFG.get('redmine', {}).get('assign_to_id', ASSIGN_TO_ID)
		RESOLVED_STATUS_ID = _CFG.get('redmine', {}).get('resolved_status_id', RESOLVED_STATUS_ID)
