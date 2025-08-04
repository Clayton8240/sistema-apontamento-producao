# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox
import os

# Importações dos Módulos Principais
from database import close_connection_pool, initialize_connection_pool
from windows.login_window import LoginWindow
from windows.main_menu_window import MenuPrincipalWindow
from windows.pcp_window import PCPWindow
from windows.production_app_window import App

class AppController(tk.Tk):
    """
    Controlador principal e invisível da aplicação.
    Ele gere o ciclo de vida, mostrando a janela de login e, depois, a janela principal.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()  # Mantém a janela raiz (root) sempre invisível.

        self.db_config = None
        self.current_user_permission = None
        self.main_window = None 
        self.login_window = None

        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icon.ico')
        logo_path = os.path.join(base_path, 'logo.png')
        
        self.show_login_window(icon_path, logo_path)

    def show_login_window(self, icon_path, logo_path):
        """Cria e exibe a janela de login."""
        self.login_window = LoginWindow(self, icon_path, logo_path)
        self.login_window.protocol("WM_DELETE_WINDOW", self.on_app_close)

    def on_login_success(self, db_config, permission):
        """
        Callback chamado pela janela de login após autenticação bem-sucedida.
        """
        self.db_config = db_config
        self.current_user_permission = permission
        
        # --- CORREÇÃO CRÍTICA: O controlador agora destrói a janela de login ---
        if self.login_window:
            self.login_window.destroy()
            self.login_window = None
        
        try:
            initialize_connection_pool(self.db_config)
            print("Pool de conexões com o banco de dados inicializado com sucesso.")
            self.show_main_window_for_user()
        except Exception as e:
            messagebox.showerror("Erro de Pool", f"Falha ao criar o pool de conexões:\n{e}")
            self.on_app_close()

    def show_main_window_for_user(self):
        """Cria a janela principal apropriada e guarda uma referência a ela."""
        if self.current_user_permission == 'admin':
            self.main_window = MenuPrincipalWindow(self, self.db_config)
        elif self.current_user_permission == 'pcp':
            self.main_window = PCPWindow(self, self.db_config)
        elif self.current_user_permission == 'offset':
            self.main_window = App(self, self.db_config)
        else:
            messagebox.showerror("Permissão Inválida", "O perfil de utilizador não tem uma janela principal definida.")
            self.on_app_close()
            return
        
        self.main_window.protocol("WM_DELETE_WINDOW", self.on_app_close)

    def on_app_close(self):
        """Função para garantir o fechamento limpo e seguro da aplicação."""
        print("Fechando a aplicação...")
        close_connection_pool()
        self.destroy()

if __name__ == "__main__":
    app = AppController()
    app.mainloop()
    print("Aplicação encerrada.")