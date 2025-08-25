# Ficheiro: sistema-apontamento-producao/windows/login_window.py

import os
import json
import base64
import bcrypt
import psycopg2
import ttkbootstrap as tb
import logging
import traceback
from tkinter import messagebox, Toplevel, PhotoImage, END, BOTH, YES, X
from PIL import Image, ImageTk
from ttkbootstrap.constants import *
import keyring  # Importa a biblioteca keyring

from languages import LANGUAGES
from database import test_db_connection, get_connection_params

# Nome do serviço para identificar a nossa aplicação no keyring
KEYRING_SERVICE_NAME = "sistema-apontamento-producao"

class LoginWindow(tb.Toplevel):
    def __init__(self, master, app_controller, db_config, icon_path=None, logo_path=None):
        logging.debug("LoginWindow: init start")
        try:
            super().__init__(master)
            self.app_controller = app_controller
            self.db_config = db_config

            self.current_language = self.db_config.get('language', 'portugues')
            self.title("Login - Sistema de Produção")
            self.geometry("450x400")

            self.logo_tk_image = None
            if logo_path and os.path.exists(logo_path):
                try:
                    logo_pil = Image.open(logo_path).resize((200, 60), Image.LANCZOS)
                    self.logo_tk_image = ImageTk.PhotoImage(logo_pil)
                except Exception as e:
                    logging.warning(f"Erro ao carregar logo: {e}")

            self.create_login_widgets()
            self.center_window()
            self.transient(master)
            
            logging.debug("LoginWindow: init complete")
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error("Erro ao iniciar LoginWindow:\n%s", tb_str)
            messagebox.showerror("Erro ao iniciar Login", f"Ocorreu um erro ao abrir a janela de login:\n\n{tb_str}", parent=master)
            try:
                self.destroy()
            except Exception:
                pass

    def handle_login(self, event=None):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha usuário e senha.", parent=self)
            return

        if not self.db_config or not self.db_config.get('usuário'):
            messagebox.showerror("Erro de Configuração", "A configuração do banco de dados não foi encontrada ou está incompleta.", parent=self)
            return
            
        # *** ALTERAÇÃO AQUI: Obter a senha do keyring ***
        db_password = keyring.get_password(KEYRING_SERVICE_NAME, self.db_config.get('usuário'))
        if not db_password:
            messagebox.showerror("Erro de Configuração", "Senha do banco de dados não encontrada. Por favor, configure a conexão novamente.", parent=self)
            return

        # Adiciona a senha ao dicionário de configuração temporariamente para a conexão
        temp_db_config = self.db_config.copy()
        temp_db_config['senha'] = db_password

        conn_check = None
        try:
            conn_params = get_connection_params(temp_db_config)
            conn_check = psycopg2.connect(**conn_params)
            with conn_check.cursor() as cur:
                cur.execute("SELECT senha_hash, permissao FROM usuarios WHERE nome_usuario = %s AND ativo = TRUE", (username,))
                user_data = cur.fetchone()

            if user_data:
                stored_hash, permission = user_data
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    self.destroy()
                    self.app_controller.on_login_success(temp_db_config, permission)
                else:
                    messagebox.showerror("Erro de Login", "Senha incorreta.", parent=self)
            else:
                messagebox.showerror("Erro de Login", "Usuário não encontrado ou inativo.", parent=self)
        except psycopg2.Error as db_error:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível verificar as credenciais.\nDetalhes: {db_error}", parent=self)
        finally:
            if conn_check: conn_check.close()
    
    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, f"_{key}_").format(**kwargs)

    def create_login_widgets(self):
        for widget in self.winfo_children(): widget.destroy()
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        if self.logo_tk_image:
            logo_label = tb.Label(main_frame, image=self.logo_tk_image)
            logo_label.pack(pady=(0, 20))
        else:
            tb.Label(main_frame, text="Sistema de Produção", font=("Helvetica", 16, "bold")).pack(pady=(10, 20))
        
        tb.Label(main_frame, text="Usuário:").pack(fill=X, padx=20)
        self.user_entry = tb.Entry(main_frame, bootstyle=PRIMARY)
        self.user_entry.pack(fill=X, pady=(0, 10), padx=20)
        
        tb.Label(main_frame, text="Senha:").pack(fill=X, padx=20)
        self.pass_entry = tb.Entry(main_frame, show="*", bootstyle=PRIMARY)
        self.pass_entry.pack(fill=X, pady=(0, 20), padx=20)
        self.pass_entry.bind("<Return>", self.handle_login)

        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill=X, padx=20)
        tb.Button(btn_frame, text="Entrar", bootstyle=SUCCESS, command=self.handle_login).pack(side='left', expand=YES, fill=X, ipady=5)
        tb.Button(btn_frame, text="Configurar DB", bootstyle="secondary-outline", command=lambda: self.app_controller.open_configure_db_window(self)).pack(side='left', padx=(10,0))
        
    

    

    def run_connection_test(self, entries, parent_win):
        test_config = {k: v.get() for k, v in entries.items()}
        if not all(test_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            messagebox.showwarning(self.get_string('test_connection_btn'), self.get_string('test_connection_warning_fill_fields'), parent=parent_win)
            return
        
        success, message = test_db_connection(test_config)
        if success:
            messagebox.showinfo(self.get_string('test_connection_btn'), self.get_string('test_connection_success'), parent=parent_win)
        else:
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('test_connection_failed_db', error=message), parent=parent_win)