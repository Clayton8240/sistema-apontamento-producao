# Ficheiro: sistema-apontamento-producao/main.py

import tkinter as tk
from tkinter import messagebox
import os
import json
import base64
import traceback
import logging

# Configuração do logging para vermos mensagens detalhadas no terminal
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Importações dos Módulos Principais
from database import close_connection_pool, initialize_connection_pool
from windows.login_window import LoginWindow
from windows.main_menu_window import MenuPrincipalWindow
from windows.pcp_window import PCPWindow
from windows.production_app_window import App

class AppController:
    """Controlador principal da aplicação. Não é uma janela tk.Tk."""
    def __init__(self):
        self.root = tk.Tk()  # Cria a instância da janela raiz
       # self.root.withdraw() # Esconde a janela raiz imediatamente
        self.db_config = self.load_db_config()
        self.main_window = None

    def load_db_config(self):
        """Carrega a config e retorna sempre um dicionário."""
        config_path = 'db_config.json'
        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            logging.warning("Ficheiro 'db_config.json' não encontrado. Use a tela de login para configurar.")
            return {}
        try:
            with open(config_path, 'rb') as f:
                encoded_data = f.read()
                decoded_data = base64.b64decode(encoded_data)
                return json.loads(decoded_data)
        except Exception as e:
            logging.error(f"Não foi possível ler 'db_config.json'. Detalhes: {e}")
            messagebox.showerror("Erro de Configuração", f"Não foi possível ler 'db_config.json'.\n\nDetalhes: {e}")
            return {}

    def run(self):
        """Inicia a aplicação, mostrando a janela de login."""
        self.show_login_window()
        # O mainloop é chamado na janela raiz, que gere toda a aplicação
        self.root.mainloop()

    def show_login_window(self):
        """Cria e mostra a janela de login."""
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icon.ico')
        logo_path = os.path.join(base_path, 'logo.png')

        login_win = LoginWindow(self.root, self, self.db_config, icon_path, logo_path)
        login_win.protocol("WM_DELETE_WINDOW", self.on_app_close)
        login_win.grab_set()

    def on_login_success(self, db_config, permission):
        """Chamado pela LoginWindow após um login bem-sucedido."""
        self.db_config = db_config
        
        # Destrói a janela de login atual para abrir a próxima
        for widget in self.root.winfo_children():
            if isinstance(widget, LoginWindow):
                widget.destroy()

        try:
            initialize_connection_pool(self.db_config)
            
            if permission == 'admin':
                self.main_window = MenuPrincipalWindow(self.root, self.db_config)
            elif permission == 'pcp':
                self.main_window = PCPWindow(self.root, self.db_config)
            elif permission == 'offset':
                self.main_window = App(self.root, self.db_config)
            else:
                raise ValueError("Permissão de utilizador inválida.")
            
            self.main_window.protocol("WM_DELETE_WINDOW", self.on_app_close)

        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Não foi possível iniciar a aplicação principal:\n{e}")
            self.on_app_close()

    def on_app_close(self):
        """Fecha o pool de conexões e encerra a aplicação."""
        logging.info("Encerrando a aplicação.")
        close_connection_pool()
        self.root.destroy()

if __name__ == "__main__":
    try:
        app = AppController()
        app.run()
    except Exception:
        logging.critical("Ocorreu um erro fatal.", exc_info=True)
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro inesperado:\n\n{traceback.format_exc()}")
    
    print("Aplicação encerrada.")