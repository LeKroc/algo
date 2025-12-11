import csv
import os
import hashlib
import hmac
import secrets
import re
from datetime import datetime, timedelta

FILE_USERS = 'users.csv'
FILE_LOGS = 'security_logs.csv'

# --- INITIALISATION DES FICHIERS ---
def init_auth_files():
    if not os.path.exists(FILE_USERS):
        with open(FILE_USERS, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # NOUVEAUX HEADERS ICI :
            writer.writerow(["username", "salt", "password_hash", "email", "role", "created_at"])

    if not os.path.exists(FILE_LOGS):
        with open(FILE_LOGS, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "username", "status", "message"])

# --- 1. CRÉATION DE COMPTE (SECURE) ---

def validate_password_strength(password):
    """Vérifie la complexité du mot de passe"""
    if len(password) < 8: return False, "Trop court (min 8 car.)"
    if not re.search(r"[A-Z]", password): return False, "Manque une majuscule"
    if not re.search(r"[a-z]", password): return False, "Manque une minuscule"
    if not re.search(r"[0-9]", password): return False, "Manque un chiffre"
    # Caractères spéciaux acceptés
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return False, "Manque un caractère spécial"
    return True, "OK"

# MODIFICATION : Ajout des arguments email et role
def register_user(username, password, email, role="commercant"):
    # 1. Validation complexité
    is_valid, msg = validate_password_strength(password)
    if not is_valid: return False, msg

    # 2. Vérifier si l'utilisateur existe déjà
    with open(FILE_USERS, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0] == username:
                return False, "Nom d'utilisateur déjà pris"

    # 3. Hachage et Stockage
    salt = secrets.token_hex(16)
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    hashed_pwd = key.hex()
    
    # Date de création
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(FILE_USERS, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # ECRITURE DES NOUVELLES COLONNES
        writer.writerow([username, salt, hashed_pwd, email, role, created_at])
    
    log_attempt(username, "REGISTER_SUCCESS", "Nouveau compte créé")
    return True, "Compte créé avec succès"

# --- 2. CONNEXION (SECURE CHECK) ---
# ... (Le reste de auth.py ne change pas, copiez la fonction verify_credentials d'avant) ...
def verify_credentials(username, password):
    if is_brute_force_detected(username):
        log_attempt(username, "LOCKED", "Tentative sur compte bloqué")
        return False, "Compte bloqué temporairement"

    user_found = None
    with open(FILE_USERS, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row and row[0] == username:
                user_found = row
                break
    
    if not user_found:
        # Fake work
        pwd_bytes = "dummy".encode('utf-8')
        salt_bytes = "dummy".encode('utf-8')
        hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
        log_attempt(username, "LOGIN_FAIL", "Utilisateur inconnu")
        return False, "Identifiants incorrects"

    stored_salt = user_found[1]
    stored_hash = user_found[2]
    
    # Re-calcul du hash
    pwd_bytes = password.encode('utf-8')
    salt_bytes = stored_salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    new_hash = key.hex()

    if hmac.compare_digest(stored_hash, new_hash):
        log_attempt(username, "LOGIN_SUCCESS", "Connexion réussie")
        return True, "Connexion réussie"
    else:
        log_attempt(username, "LOGIN_FAIL", "Mot de passe incorrect")
        return False, "Identifiants incorrects"

# --- 3. AUDIT ---
def log_attempt(username, status, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(FILE_LOGS, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, username, status, message])

def is_brute_force_detected(username):
    limit_time = datetime.now() - timedelta(minutes=5)
    fail_count = 0
    if not os.path.exists(FILE_LOGS): return False
    with open(FILE_LOGS, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        for row in reversed(reader):
            if len(row) < 3: continue
            try:
                log_time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                if log_time < limit_time: break
                if row[1] == username and row[2] == "LOGIN_FAIL":
                    fail_count += 1
            except: continue
    return fail_count >= 3

init_auth_files()