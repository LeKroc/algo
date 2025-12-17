import csv
import os
import hashlib
import hmac
import secrets
import re
import requests
from datetime import datetime, timedelta

FILE_USERS = 'users.csv'
FILE_LOGS = 'security_logs.csv'


def init_auth_files():
    if not os.path.exists(FILE_USERS):
        with open(FILE_USERS, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["username", "salt", "password_hash", "email", "role", "created_at"])

    if not os.path.exists(FILE_LOGS):
        with open(FILE_LOGS, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "username", "status", "message"])
            
def check_pwned_password(password):
    """
    Vérifie l'API Pwned Passwords.
    Retourne True si le mot de passe est piraté (Mauvais).
    Retourne False si le mot de passe est sûr (Bon).
    """
    # 1. Hachage SHA-1
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_password[:5]
    suffix = sha1_password[5:]
    
    try:
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        response = requests.get(url, timeout=2) 
        
        if response.status_code != 200:
            return False # En cas d'erreur API, on laisse passer par défaut
        
        hashes = (line.split(':') for line in response.text.splitlines())
        for h, count in hashes:
            if h == suffix:
                return True # TROUVÉ dans la base des pirates !
        return False # Non trouvé
        
    except requests.exceptions.RequestException:
        return False # Pas d'internet -> On laisse passer


def register_user(username, password, email, role="commercant", force=False):
    
    if not force:
        if check_pwned_password(password):
            return False, "PWNED_WARNING"

    
    with open(FILE_USERS, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0] == username:
                return False, "Nom d'utilisateur déjà pris"

    
    user_count = 0
    with open(FILE_USERS, 'r', encoding='utf-8') as f:
         user_count = sum(1 for line in f)
    if user_count <= 1: role = "admin"

    
    salt = secrets.token_hex(16)
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    hashed_pwd = key.hex()
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(FILE_USERS, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([username, salt, hashed_pwd, email, role, created_at])
    
    log_attempt(username, "REGISTER_SUCCESS", "Nouveau compte créé")
    return True, "Compte créé avec succès"


def verify_credentials(identifiant, password):
    """
    Vérifie les identifiants (Pseudo OU Email).
    """
    if is_brute_force_detected(identifiant):
        log_attempt(identifiant, "LOCKED", "Tentative sur compte bloqué")
        return False, "Compte bloqué temporairement"

    user_found = None
    
    with open(FILE_USERS, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None) 
        
        for row in reader:
            if row:
                # Vérifie Pseudo (col 0) OU Email (col 3)
                if row[0] == identifiant or (len(row) > 3 and row[3] == identifiant):
                    user_found = row
                    break
    
    if not user_found:
        pwd_bytes = "dummy".encode('utf-8')
        salt_bytes = "dummy".encode('utf-8')
        hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
        log_attempt(identifiant, "LOGIN_FAIL", "Utilisateur inconnu")
        return False, "Identifiants incorrects"

    stored_salt = user_found[1]
    stored_hash = user_found[2]
    username_reel = user_found[0] 

    pwd_bytes = password.encode('utf-8')
    salt_bytes = stored_salt.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    new_hash = key.hex()

    if hmac.compare_digest(stored_hash, new_hash):
        log_attempt(username_reel, "LOGIN_SUCCESS", "Connexion réussie")
        return True, "Connexion réussie"
    else:
        log_attempt(username_reel, "LOGIN_FAIL", "Mot de passe incorrect")
        return False, "Identifiants incorrects"


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