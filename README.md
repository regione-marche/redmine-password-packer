# 🔐 Redmine Password Packer
Versione: `0.1`

Un sistema automatico per elaborare ticket Redmine e generare archivi `.7z` cifrati contenenti:
- Password generate da ticket Redmine
- Immagini della password (bianco e nero)
- Crittografia visuale (condivisione di segreti visivi)
- Documento Word `.docx` generato con template personalizzato a partire dalla prima parte della password visuale

## 📋 Caratteristiche

- **Configurazione centralizzata YAML**: tutti i parametri in un unico file `config.yml`
- **Archivi 7z cifrati**: password passate via stdin (non visibili in `ps`) e header cifrato (`-mhe=on`)
- **Password per progetto**: possibilità di usare password diverse per ogni progetto Redmine
- **Template DOCX per progetto**: possibilità di specificare `docx_template` per singolo progetto
- **Parametri ticket per progetto**: supporto a `category_id` e `assigned_to_id` per update ticket
- **Segnalazione automatica**: se un progetto non è configurato, apre automaticamente un ticket di segnalazione
- **Hardening locale**: file sensibili con permessi stretti e cleanup automatico degli artefatti locali dopo upload
- **Test suite integrata**: verifica connessione, elenca ticket/progetti, testa creazione archivi

## 🔧 Setup

### 1. Clonare/scaricare il repository

```bash
git clone <repo-url>
cd redmine-password-packer
```

### 2. Configurare

Copiare il file di esempio e personalizzare:

```bash
cp config.yml.example config.yml
```

Editare `config.yml` con le tue impostazioni:
- URL e API key di Redmine
- Password di default e per-progetto per gli archivi 7z
- Configurazione per i ticket di segnalazione (per progetti mancanti)

Esempio di config.yml:

```yaml
redmine:
  url: "https://your-redmine-instance.com"
  api_key: "YOUR_API_KEY"
  assign_to_id: 123
  resolved_status_id: 3

output:
  dir: "output"

archive:
  default_password: "fallback_password"

logging:
  level: "DEBUG"

# opzionale: file esterno (default: projects.yml)
# projects_file: "projects.yml"

projects:
  project-identifier-1:
    password: "password_1"
    docx_template: "app/static/template-project-1.docx"
    ticket:
      project_id: "admin"
      category_id: 10
      assigned_to_id: 1
  project-identifier-2:
    password: "password_2"
    docx_template: "app/static/template-project-2.docx"
    ticket:
      project_id: "admin"
      category_id: 20
      assigned_to_id: 2

report_missing_project:
  project: "admin"
  assigned_to_id: 1
  subject: "Missing project {project} in ticket {ticket}"
  description: "..."
```

### 3. Installare dipendenze (per esecuzione locale)

```bash
pip install -r requirements.txt
```

Inoltre assicurarsi che sia installato `7z`:
- **Ubuntu/Debian**: `sudo apt install p7zip-full`
- **Alpine**: `apk add p7zip`
- **macOS**: `brew install p7zip`

## 🚀 Utilizzo

### Con Docker Compose (consigliato)

```bash
# Build
docker-compose build

# Eseguire elaborazione principale
docker-compose run --rm pwd-gen

# Eseguire i test
docker-compose run --rm pwd-gen-test
```

### Con Docker direttamente

```bash
# Build
docker build -t redmine-password-packer .

# Elaborazione principale
docker run --rm -v $(pwd)/config.yml:/app/config.yml:ro -v $(pwd)/output:/app/output redmine-password-packer python main.py

# Test
docker run --rm -v $(pwd)/config.yml:/app/config.yml:ro -v $(pwd)/output:/app/output redmine-password-packer python test_runner.py
```

### Localmente (Linux/macOS)

```bash
# Installare dipendenze
pip install -r requirements.txt

# Eseguire elaborazione
python app/main.py

# Eseguire test
python app/test_runner.py
```

### Logging di debug

Per abilitare log dettagliato, imposta in `config.yml`:

```yaml
logging:
  level: "DEBUG"
```

## 📊 Flusso di elaborazione

Quando un ticket con stato "Nuovo" viene assegnato all'utente associato all'applicativo:

1. Viene generata una password casuale per il ticket.
2. La password viene trasformata in immagine base e poi divisa in due immagini (`Password_A.png` e `Password_B.png`) tramite crittografia visuale.
3. Viene creato un documento `.docx` usando il template configurato, includendo la prima immagine della password (`Password_A.png`).
4. Tutti gli artefatti del ticket vengono inseriti in un archivio `.7z` cifrato.
5. La password dell'archivio `.7z` è quella dedicata al progetto del ticket (presa dalla configurazione progetto; in fallback viene usata quella di default).
6. L'archivio viene allegato al ticket Redmine originale.
7. Il ticket viene aggiornato con stato, categoria (`category_id`) e assegnatario (`assigned_to_id`) in base alla configurazione del progetto (con fallback ai default globali).
8. Dopo l'upload, gli artefatti locali temporanei (directory ticket e archivio locale) vengono rimossi.

### Comportamento per progetti mancanti

Se un ticket appartiene a un progetto non presente in `config.yml`:
- Apre automaticamente un ticket nel progetto di segnalazione
- Salta l'elaborazione del ticket originale
- Continua con i ticket successivi

## 🧪 Test Runner

Verifica la configurazione prima dell'elaborazione:

```bash
python app/test_runner.py [OPTIONS]
```

Opzioni principali:
- `--test-id N`: ID ticket fittizio per test 7z (default: 9999)
- `--skip-connectivity`: salta test connessione Redmine
- `--skip-tickets`: salta lista ticket
- `--skip-projects`: salta lista progetti
- `--skip-7z`: salta test creazione archivio

## 📁 Struttura directory

```
.
├── config.yml                              # Configurazione (non committare)
├── config.yml.example                      # Esempio di configurazione
├── docker-compose.yml                      # Orchestrazione Docker
├── Dockerfile                              # Build immagine
├── README.md                               # Questo file
├── requirements.txt                        # Dipendenze Python
├── .gitignore                              # Git exclude patterns
├── app/
│   ├── main.py                             # Elaborazione principale
│   ├── test_runner.py                      # Test suite
│   ├── config.py                           # Caricamento config YAML
│   ├── redmine_utils.py                    # API Redmine
│   ├── password_utils.py                   # Generazione password/immagini
│   ├── crypto_utils.py                     # Crittografia visuale
│   ├── mkdocx.py                           # Generazione DOCX
│   ├── zipper.py                           # Creazione archivi 7z
│   ├── static/
│   │   └── template.docx                   # Template DOCX da personalizzare
│   └── visual_cryptography_py3__*.py       # Script crittografia visuale
└── output/                                 # Directory risultati (non committare)
    └── (artefatti temporanei durante l'elaborazione)
```

## 🔐 Sicurezza

- **Password non visibili**: passate via stdin a `7z`, non in argv
- **Header archivio cifrato**: `7z` usa `-mhe=on`
- **Permessi stretti**: directory `0700`, file sensibili `0600`
- **Pulizia post-upload**: eliminazione automatica di file password/immagini/docx/archivio locale
- **Configurazione centralizzata**: credenziali in unico file
- **Segnalazione**: tickets avvisano di problemi di configurazione
- `.gitignore` protegge `config.yml`, `output/` e `ticket_*` da commit accidentali

## 🛠️ Sviluppo

### Setup locale

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Personalizzare template DOCX

Editare `app/static/template.docx` con un editor compatibile (LibreOffice, Word, ecc).
Lo script `mkdocx.py` inserirà l'immagine della password nel template.

## 📝 Note importanti

- L'API key Redmine deve avere permessi su: lettura ticket, creazione ticket, upload file
- `config.yml` è nel `.gitignore` - configurare prima di eseguire
- `output/` e `ticket_*/` sono automaticamente esclusi da git

## 📄 Licenza

Questo progetto è distribuito sotto licenza **GNU GPL v3.0 o successiva**.
