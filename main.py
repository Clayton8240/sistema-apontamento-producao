# Ficheiro: sistema-apontamento-producao/main.py

import tkinter as tk
from tkinter import messagebox
import os
import json
import base64
import traceback

# Importações dos Módulos Principais
from database import close_connection_pool, initialize_connection_pool
from windows.login_window import LoginWindow
from windows.main_menu_window import MenuPrincipalWindow
from windows.pcp_window import PCPWindow
from windows.production_app_window import App

class AppController(tk.Tk):
    """Controlador principal da aplicação."""
    def __init__(self):
        super().__init__()
        self.withdraw()  # Mantém a janela raiz invisível.

        self.db_config = self.load_db_config()
        self.main_window = None
        self.show_login_window()

    def load_db_config(self):
        """Carrega a config e retorna sempre um dicionário."""
        config_path = 'db_config.json'
        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            messagebox.showwarning("Configuração Ausente", "Ficheiro 'db_config.json' não encontrado. Por favor, configure o acesso na tela de login.")
            return {}
        try:
            with open(config_path, 'rb') as f:
                encoded_data = f.read()
                decoded_data = base64.b64decode(encoded_data)
                return json.loads(decoded_data)
        except Exception as e:
            messagebox.showerror("Erro de Configuração", f"Não foi possível ler 'db_config.json'.\n\nDetalhes: {e}")
            return {}

    def show_login_window(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icon.ico')
        logo_path = os.path.join(base_path, 'logo.png')

        print("AppController: criando LoginWindow")
        login_win = LoginWindow(self, self, self.db_config, icon_path, logo_path)
        self.after(100, lambda: self.deiconify()) 
        self.after(500, lambda: print(f"janela login ainda existe? {login_win.winfo_exists()}"))
        login_win.lift()
        login_win.focus_force()
        login_win.grab_set()
        print("AppController: LoginWindow criada e grab_set aplicada")


    def on_login_success(self, db_config, permission):
        self.db_config = db_config
        
        try:
            initialize_connection_pool(self.db_config)
            
            if permission == 'admin':
                self.main_window = MenuPrincipalWindow(self, self.db_config)
            elif permission == 'pcp':
                self.main_window = PCPWindow(self, self.db_config)
            elif permission == 'offset':
                self.main_window = App(self, self.db_config)
            else:
                raise ValueError("Permissão de utilizador inválida.")
            
            self.main_window.protocol("WM_DELETE_WINDOW", self.on_app_close)

        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Não foi possível iniciar a aplicação principal:\n{e}")
            self.on_app_close()

    def on_app_close(self):
        print("⚠️ on_app_close() foi chamado - a aplicação será destruída")
        close_connection_pool()
        self.destroy()

if __name__ == "__main__":
    try:
        app = AppController()
        app.mainloop()
    except Exception:
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro inesperado:\n\n{traceback.format_exc()}")
    
    print("Aplicação encerrada.")