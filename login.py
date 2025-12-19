import tkinter as tk
from tkinter import messagebox
import sys

# --- Gestion des imports ---
try:
    import authentification
except ImportError:
    authentification = None

try:
    import interface
except ImportError:
    interface = None

class LoginApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sécurité - Authentification")
        self.root.geometry("400x550") 
        self.root.configure(bg="#2C3E50")

        self.is_register_mode = False

        self.frame = tk.Frame(self.root, bg="#34495E", padx=20, pady=20)
        self.frame.pack(pady=30, padx=20, fill="both", expand=True)

        self.lbl_title = tk.Label(self.frame, text="CONNEXION", font=("Arial", 18, "bold"), bg="#34495E", fg="white")
        self.lbl_title.pack(pady=10)
        
        tk.Label(self.frame, text="Nom d'utilisateur", bg="#34495E", fg="#BDC3C7").pack(anchor="w")
        self.entry_user = tk.Entry(self.frame, font=("Arial", 12))
        self.entry_user.pack(fill="x", pady=5)
        
        self.lbl_email = tk.Label(self.frame, text="Email", bg="#34495E", fg="#BDC3C7")
        self.entry_email = tk.Entry(self.frame, font=("Arial", 12))
        # On ne pack pas l'email tout de suite (mode connexion par défaut)
        
        tk.Label(self.frame, text="Mot de passe", bg="#34495E", fg="#BDC3C7").pack(anchor="w")
        self.entry_pass = tk.Entry(self.frame, font=("Arial", 12), show="*")
        self.entry_pass.pack(fill="x", pady=5)
        
        self.lbl_info = tk.Label(self.frame, text="Min 8 car, Maj, Min, Chiffre, Special", font=("Arial", 8), bg="#34495E", fg="#E74C3C")
        
        self.btn_action = tk.Button(self.frame, text="SE CONNECTER", bg="#2ECC71", fg="white", 
                                    font=("Arial", 12, "bold"), command=self.handle_action)
        self.btn_action.pack(fill="x", pady=20)

        self.btn_switch = tk.Button(self.frame, text="Créer un compte", bg="#34495E", fg="#3498DB", bd=0, command=self.toggle_mode)
        self.btn_switch.pack()

        if not authentification:
            messagebox.showwarning("Fichier Manquant", "Le fichier 'authentification.py' est introuvable.")

        self.root.mainloop()

    def toggle_mode(self):
        """Change l'interface entre Connexion et Inscription"""
        self.is_register_mode = not self.is_register_mode
        
        if self.is_register_mode:
            self.lbl_title.config(text="INSCRIPTION")
            self.lbl_email.pack(anchor="w", after=self.entry_user)
            self.entry_email.pack(fill="x", pady=5, after=self.lbl_email)
            self.btn_action.config(text="S'INSCRIRE", bg="#3498DB")
            self.btn_switch.config(text="Déjà un compte ? Se connecter")
            self.lbl_info.pack(after=self.entry_pass)
        else:
            self.lbl_title.config(text="CONNEXION")
            self.lbl_email.pack_forget()
            self.entry_email.pack_forget()
            self.btn_action.config(text="SE CONNECTER", bg="#2ECC71")
            self.btn_switch.config(text="Créer un compte")
            self.lbl_info.pack_forget()

    def handle_action(self):
        """Gère le clic sur le bouton (Connexion ou Inscription)"""
        identifiant = self.entry_user.get()
        password = self.entry_pass.get()

        try:
            # --- MODE INSCRIPTION ---
            if self.is_register_mode:
                email = self.entry_email.get()
                if not identifiant or not password or not email:
                    messagebox.showwarning("Attention", "Remplissez tous les champs")
                    return
                
                # Tentative d'inscription normale
                success, msg = authentification.register_user(identifiant, password, email, force=False)
                
                # Si mot de passe pwned
                if not success and msg == "PWNED_WARNING":
                    reponse = messagebox.askyesno("Alerte Sécurité", "Ce mot de passe a été trouvé dans des fuites de données (Pwned).\nEst-ce vraiment sûr de l'utiliser ?")
                    if reponse:
                        success, msg = authentification.register_user(identifiant, password, email, force=True)
                        if success:
                            messagebox.showinfo("Succès", "Compte créé (risqué)")
                            self.toggle_mode()
                
                elif success:
                    messagebox.showinfo("Succès", msg)
                    self.toggle_mode() # On bascule vers la connexion
                else:
                    messagebox.showerror("Erreur", msg)

            # --- MODE CONNEXION ---
            else:
                if not identifiant or not password:
                    messagebox.showwarning("Attention", "Remplissez les champs")
                    return

                # Appel à verify_credentials qui renvoie (True, Role) ou (False, Message)
                success, result = authentification.verify_credentials(identifiant, password)
                
                if success:
                    role_recupere = result # C'est "admin" ou "commercant"
                    self.root.destroy()
                    
                    if hasattr(interface, 'lancer_app'):
                        print(f"Connexion réussie ! Rôle détecté : {role_recupere}")
                        interface.lancer_app(role_recupere) 
                    else:
                        messagebox.showerror("Erreur", "Le fichier interface.py n'a pas de fonction lancer_app()")
                else:
                    messagebox.showerror("Echec", result) # Affiche "Mot de passe incorrect" etc.
                    self.entry_pass.delete(0, tk.END)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur Critique", f"Erreur: {e}")

if __name__ == "__main__":
    app = LoginApp()