import tkinter as tk
from tkinter import messagebox
import authentification
import interface


class LoginApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sécurité - Authentification")
        self.root.geometry("400x500") 
        self.root.configure(bg="#2C3E50")

        self.is_register_mode = False

        self.frame = tk.Frame(self.root, bg="#34495E", padx=20, pady=20)
        self.frame.pack(pady=30, padx=20, fill="both", expand=True)

        self.lbl_title = tk.Label(self.frame, text="CONNEXION", font=("Arial", 18, "bold"), bg="#34495E", fg="white")
        self.lbl_title.pack(pady=10)

        
        tk.Label(self.frame, text="Nom d'utilisateur ou Email", bg="#34495E", fg="#BDC3C7").pack(anchor="w")
        self.entry_user = tk.Entry(self.frame, font=("Arial", 12))
        self.entry_user.pack(fill="x", pady=5)

        
        self.lbl_email = tk.Label(self.frame, text="Email", bg="#34495E", fg="#BDC3C7")
        self.entry_email = tk.Entry(self.frame, font=("Arial", 12))
        
        tk.Label(self.frame, text="Mot de passe", bg="#34495E", fg="#BDC3C7").pack(anchor="w")
        self.entry_pass = tk.Entry(self.frame, font=("Arial", 12), show="*")
        self.entry_pass.pack(fill="x", pady=5)
        
        self.lbl_info = tk.Label(self.frame, text="Min 8 car, Maj, Min, Chiffre, Special", font=("Arial", 8), bg="#34495E", fg="#E74C3C")
        
        self.btn_action = tk.Button(self.frame, text="SE CONNECTER", bg="#2ECC71", fg="white", font=("Arial", 12, "bold"), command=self.handle_action)
        self.btn_action.pack(fill="x", pady=20)

        self.btn_switch = tk.Button(self.frame, text="Créer un compte", bg="#34495E", fg="#3498DB", bd=0, command=self.toggle_mode)
        self.btn_switch.pack()

        self.root.mainloop()

    def toggle_mode(self):
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
            # --- DÉBUT DU FILET DE SÉCURITÉ ---
            try:
                print("DEBUG: Bouton cliqué") # On vérifie si le bouton marche
                user = self.entry_user.get()
                pwd = self.entry_pass.get()

                # --- MODE INSCRIPTION ---
                if self.is_register_mode:
                    email = self.entry_email.get()
                    print(f"DEBUG: Tentative inscription pour {user}")
                    
                    if not user or not pwd or not email:
                        messagebox.showwarning("Attention", "Remplissez tous les champs")
                        return
                    
                    # Appel à l'inscription
                    # Note: On passe force=False par défaut
                    success, msg = authentification.register_user(user, pwd, email, force=False)
                    
                    if not success and msg == "PWNED_WARNING":
                        reponse = messagebox.askyesno(
                            "Alerte Sécurité", 
                            "Ce mot de passe est piraté !\nVoulez-vous vraiment le garder ?"
                        )
                        if reponse:
                            success, msg = authentification.register_user(user, pwd, email, force=True)
                            if success:
                                messagebox.showinfo("Succès", "Compte créé (risqué)")
                                self.toggle_mode()
                        else:
                            return

                    elif success:
                        messagebox.showinfo("Succès", msg)
                        self.toggle_mode()
                        self.entry_user.delete(0, tk.END)
                        self.entry_pass.delete(0, tk.END)
                        self.entry_email.delete(0, tk.END)
                    else:
                        messagebox.showerror("Erreur", msg)

                # --- MODE CONNEXION ---
                else:
                    print(f"DEBUG: Tentative connexion pour {user}")
                    
                    if not user or not pwd:
                        messagebox.showwarning("Attention", "Remplissez les champs")
                        return

                    # Appel à la connexion
                    # Attention : verify_credentials doit exister dans authentification.py
                    success, msg = authentification.verify_credentials(user, pwd)
                    
                    print(f"DEBUG: Résultat connexion : {success} / {msg}")

                    if success:
                        self.root.destroy()
                        if hasattr(interface, 'lancer_app'):
                            interface.lancer_app()
                        else:
                            messagebox.showerror("Erreur", "Fichier interface.py incomplet (pas de fonction lancer_app)")
                    else:
                        messagebox.showerror("Echec", msg)
                        self.entry_pass.delete(0, tk.END)

            except Exception as e:
                # C'EST ICI QUE L'ERREUR VA S'AFFICHER
                import traceback
                traceback.print_exc() # Affiche les détails dans la console noire
                messagebox.showerror("ERREUR DE CODE", f"Le programme a planté ici :\n{e}")

if __name__ == "__main__":
    app = LoginApp()