#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for Redmine Password Visual Packer.

Performs the following checks:
1. Verifies Redmine connectivity and authentication
2. Lists assigned tickets for the current user
3. Lists projects where the current user is enabled
4. Creates a test 7z archive with a dummy ticket ID
"""

import argparse
import os
import sys
import shutil

from redminelib import Redmine
from config import REDMINE_URL, API_KEY, OUTPUT_DIR, ARCHIVE_PASSWORD, PROJECT_PASSWORDS
from zipper import crea_7z_cifrato
from password_utils import genera_password, crea_immagine
from crypto_utils import run_visual_crypto


def test_connectivity():
    """Verifica la connessione e autenticazione con Redmine."""
    print("[*] Testing Redmine connectivity...")
    try:
        redmine = Redmine(REDMINE_URL, key=API_KEY)
        user = redmine.auth.get_current_user()
        print(f"[✓] Connected to {REDMINE_URL} as user: {user.login} (ID: {user.id})")
        return redmine, user
    except Exception as e:
        print(f"[✗] Connection failed: {e}")
        return None, None


def test_assigned_tickets(redmine):
    """Lista i ticket assegnati all'utente corrente."""
    print("\n[*] Fetching assigned tickets...")
    try:
        tickets = redmine.issue.filter(assigned_to_id='me', status_id='1')  # status 1 = "Nuovo"
        tickets_list = list(tickets)
        if tickets_list:
            print(f"[✓] Found {len(tickets_list)} assigned ticket(s):")
            for t in tickets_list[:10]:  # Show first 10
                proj = getattr(t, 'project', None)
                proj_name = proj.name if proj else "Unknown"
                print(f"    - Ticket #{t.id}: {t.subject} (Project: {proj_name})")
            if len(tickets_list) > 10:
                print(f"    ... and {len(tickets_list) - 10} more")
        else:
            print("[!] No assigned tickets found")
        return tickets_list
    except Exception as e:
        print(f"[✗] Error fetching tickets: {e}")
        return []


def test_user_projects(redmine, user_id):
    """Lista i progetti su cui l'utente è abilitato."""
    print("\n[*] Fetching user projects...")
    try:
        projects = redmine.project.all()
        user_projects = []
        for p in projects:
            try:
                members = redmine.project_member.filter(project_id=p.id)
                for m in members:
                    if m.user.id == user_id:
                        user_projects.append(p)
                        break
            except Exception:
                pass

        if user_projects:
            print(f"[✓] User is enabled on {len(user_projects)} project(s):")
            for p in user_projects[:10]:
                print(f"    - {p.name} (ID: {p.id}, Identifier: {p.identifier})")
            if len(user_projects) > 10:
                print(f"    ... and {len(user_projects) - 10} more")
        else:
            print("[!] User is not enabled on any projects")
        return user_projects
    except Exception as e:
        print(f"[✗] Error fetching projects: {e}")
        return []


def test_7z_creation(test_ticket_id=9999):
    """Crea un file 7z cifrato di prova usando un ticket ID fittizio.
    
    Ricrea la directory di test da zero se già presente.
    """
    print(f"\n[*] Creating test 7z archive (ticket_id={test_ticket_id})...")
    
    # Prepara directory di test
    test_dir = os.path.join(OUTPUT_DIR, f"ticket_{test_ticket_id}")
    if os.path.exists(test_dir):
        print(f"    Removing existing test directory: {test_dir}")
        shutil.rmtree(test_dir)
    
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # 1) Genera e salva password
        password = genera_password()
        pwd_file = os.path.join(test_dir, f"ticket_{test_ticket_id}_password.txt")
        with open(pwd_file, 'w') as f:
            f.write(password)
        print(f"    [✓] Created password file: {pwd_file}")
        
        # 2) Crea immagine base
        base_img = crea_immagine(password, test_ticket_id, test_dir)
        print(f"    [✓] Created base image: {base_img}")
        
        # 3) Applica crittografia visuale
        A_img, B_img = run_visual_crypto(base_img)
        print(f"    [✓] Created visual crypto images: {A_img}, {B_img}")
        
        # 4) Crea un file DOCX fittizio (solo un placeholder)
        docx_out = os.path.join(test_dir, f"ticket_{test_ticket_id}.docx")
        with open(docx_out, 'wb') as f:
            f.write(b"Test DOCX placeholder")
        print(f"    [✓] Created DOCX file: {docx_out}")
        
        # 5) Crea archivio 7z cifrato
        archive_pwd = ARCHIVE_PASSWORD
        archive = crea_7z_cifrato(test_dir, test_ticket_id, archive_pwd)
        print(f"    [✓] Created encrypted 7z archive: {archive}")
        
        # Verifica che il file esista
        if os.path.exists(archive):
            size = os.path.getsize(archive)
            print(f"    [✓] Archive size: {size} bytes")
        else:
            print(f"    [✗] Archive file not found!")
            return False
        
        return True
    
    except Exception as e:
        print(f"    [✗] Error creating 7z archive: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for Redmine Password Visual Packer"
    )
    parser.add_argument('--test-id', type=int, default=9999,
                        help="Ticket ID to use for 7z test (default: 9999)")
    parser.add_argument('--skip-connectivity', action='store_true',
                        help="Skip Redmine connectivity test")
    parser.add_argument('--skip-tickets', action='store_true',
                        help="Skip assigned tickets listing")
    parser.add_argument('--skip-projects', action='store_true',
                        help="Skip user projects listing")
    parser.add_argument('--skip-7z', action='store_true',
                        help="Skip 7z archive creation test")
    args = parser.parse_args()

    print("=" * 60)
    print("Redmine Password Visual Packer - Test Suite")
    print("=" * 60)

    redmine = None
    user = None

    if not args.skip_connectivity:
        redmine, user = test_connectivity()
        if not redmine:
            print("\n[!] Cannot proceed without Redmine connectivity")
            return 1
    else:
        print("[*] Skipping connectivity test")

    if not args.skip_tickets and redmine:
        test_assigned_tickets(redmine)
    elif args.skip_tickets:
        print("[*] Skipping tickets test")

    if not args.skip_projects and redmine and user:
        test_user_projects(redmine, user.id)
    elif args.skip_projects:
        print("[*] Skipping projects test")

    if not args.skip_7z:
        success = test_7z_creation(args.test_id)
        if not success:
            return 1
    else:
        print("[*] Skipping 7z creation test")

    print("\n" + "=" * 60)
    print("[✓] All tests completed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
