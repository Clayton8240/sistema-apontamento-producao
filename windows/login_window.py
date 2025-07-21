# -*- coding: utf-8 -*-

import base64
import json
import os
import bcrypt
import psycopg2
import ttkbootstrap as tb
from tkinter import messagebox, Toplevel, PhotoImage, END, BOTH, YES, X
from PIL import Image, ImageTk
from ttkbootstrap.constants import *

# Importações do nosso projeto
from config import LANGUAGES
from database import get_connection_params, get_db_connection
from .main_menu_window import MenuPrincipalWindow
from .pcp_window import PCPWindow
from .production_app_window import App
# NOTA: As duas importações abaixo são necessárias para que o MenuPrincipal saiba quais janelas abrir
from .view_appointments_window import ViewAppointmentsWindow
from ui_components import LookupTableManagerWindow

class LoginWindow(tb.Window):
    # Ajustado para receber os caminhos dos assets como argumentos
    def __init__(self, icon_path=None, logo_path=None):
        super().__init__(themename="flatly")
        self.db_config = {}
        self.load_db_config()
        self.current_language = self.db_config.get('language', 'portugues')
        self.title("Login - Sistema de Produção")
        self.geometry("450x400")
        
        # Guarda os caminhos para uso posterior
        self.icon_path = icon_path
        self.logo_path = logo_path

        try:
            if self.icon_path and os.path.exists(self.icon_path):
                icon_image = PhotoImage(file=self.icon_path)
                self.iconphoto(False, icon_image)
        except Exception as e:
            print(f"Erro ao carregar o ícone '{self.icon_path}': {e}")

        self.create_login_widgets()
        self.center_window()

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
        return LANGUAGES.get(self.current_language, LANGUAGES['portugues']).get(key, f"_{key}_").format(**kwargs)

    def load_db_config(self):
        config_path = 'db_config.json'
        if os.path.exists(config_path) and os.path.getsize(config_path) > 0:
            try:
                with open(config_path, 'rb') as f:
                    encoded_data = f.read()
                    decoded_data = base64.b64decode(encoded_data)
                    self.db_config = json.loads(decoded_data)
            except Exception as e:
                messagebox.showerror("Erro de Configuração", f"Não foi possível ler o arquivo 'db_config.json'.\n\nDetalhes: {e}")
                self.db_config = {}
        else:
            self.db_config = {}

    def get_db_connection(self):
        # Utiliza a função centralizada do database.py
        conn = get_db_connection(self.db_config)
        if not conn and self.winfo_exists():
             messagebox.showerror(self.get_string("db_conn_incomplete"), self.get_string("db_conn_incomplete"), parent=self)
        return conn

    def create_login_widgets(self):
        for widget in self.winfo_children(): widget.destroy()
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        try:
            if self.logo_path and os.path.exists(self.logo_path):
                logo_pil_image = Image.open(self.logo_path)
                base_width = 200
                w_percent = (base_width / float(logo_pil_image.size[0]))
                h_size = int((float(logo_pil_image.size[1]) * float(w_percent)))
                logo_pil_image = logo_pil_image.resize((base_width, h_size), Image.LANCZOS)
                
                self.logo_tk_image = ImageTk.PhotoImage(logo_pil_image)
                logo_label = tb.Label(main_frame, image=self.logo_tk_image)
                logo_label.pack(pady=(0, 20))
            else:
                raise FileNotFoundError
        except Exception as e:
            print(f"Erro ao carregar a imagem '{self.logo_path}': {e}")
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
        tb.Button(btn_frame, text="Entrar", bootstyle=SUCCESS, command=self.handle_login).pack(side=LEFT, expand=YES, fill=X, ipady=5)
        tb.Button(btn_frame, text="Configurar DB", bootstyle="secondary-outline", command=lambda: self.open_configure_db_window(self)).pack(side=LEFT, padx=(10,0))
    
    def handle_login(self, event=None):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha usuário e senha.", parent=self)
            return
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT senha_hash, permissao FROM usuarios WHERE nome_usuario = %s AND ativo = TRUE", (username,))
                user_data = cur.fetchone()
            if user_data:
                stored_hash, permission = user_data
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    self.withdraw()
                    self.redirect_user(permission)
                else:
                    messagebox.showerror("Erro de Login", "Senha incorreta.", parent=self)
            else:
                messagebox.showerror("Erro de Login", "Usuário não encontrado ou inativo.", parent=self)
        except psycopg2.Error as db_error:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível verificar as credenciais. Verifique a conexão e se a tabela 'usuarios' existe.\n\nDetalhes: {db_error}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro durante o login: {e}", parent=self)
            self.deiconify()
        finally:
            if conn: conn.close()

    def handle_child_window_close(self, child_window):
        child_window.destroy()
        self.deiconify()
        self.user_entry.delete(0, END)
        self.pass_entry.delete(0, END)
        self.user_entry.focus_set()

    def redirect_user(self, permission):
        if permission == 'offset':
            app_win = App(master=self, db_config=self.db_config)
            app_win.protocol("WM_DELETE_WINDOW", lambda: self.handle_child_window_close(app_win))
        elif permission == 'pcp':
            pcp_win = PCPWindow(master=self, db_config=self.db_config)
            pcp_win.protocol("WM_DELETE_WINDOW", lambda: self.handle_child_window_close(pcp_win))
        elif permission == 'admin':
            admin_menu = MenuPrincipalWindow(master=self, db_config=self.db_config)
            admin_menu.protocol("WM_DELETE_WINDOW", self.destroy)
        else:
            messagebox.showerror("Erro de Permissão", "Permissão de usuário desconhecida.", parent=self)
            self.deiconify()

    def open_configure_db_window(self, parent):
        win = Toplevel(parent)
        win.title(self.get_string('config_win_title'))
        win.transient(parent)
        win.grab_set()
        
        frame = tb.Frame(win, padding=10)
        frame.pack(expand=True, fill=BOTH)
        
        labels = [("host", 'host_label'), ("porta", 'port_label'), ("usuário", 'user_label'), ("senha", 'password_label'), ("banco", 'db_label'), ("tabela", 'table_label')]
        entries = {}
        for i, (key, label_key) in enumerate(labels):
            tb.Label(frame, text=self.get_string(label_key) + ":").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = tb.Entry(frame, show='*' if key == "senha" else '')
            e.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            e.insert(0, self.db_config.get(key, ''))
            entries[key] = e
        
        tb.Label(frame, text=self.get_string('language_label') + ":").grid(row=len(labels), column=0, padx=10, pady=5, sticky="w")
        lang_opts = [lang.capitalize() for lang in LANGUAGES.keys()]
        lang_selector = tb.Combobox(frame, values=lang_opts, state="readonly")
        lang_selector.grid(row=len(labels), column=1, padx=10, pady=5, sticky="ew")
        lang_selector.set(self.current_language.capitalize())

        frame.columnconfigure(1, weight=1)
        
        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=len(labels) + 1, columnspan=2, pady=15)
        tb.Button(btn_frame, text=self.get_string('test_connection_btn'), bootstyle="info-outline", command=lambda: self.test_db_connection(entries, win)).pack(side="left", padx=5)
        tb.Button(btn_frame, text=self.get_string('save_btn'), bootstyle="success", command=lambda: self.save_and_close_config(entries, lang_selector, win)).pack(side="left", padx=5)

    def save_and_close_config(self, entries, lang_selector, win):
        new_config = {k: v.get() for k, v in entries.items()}
        new_lang = lang_selector.get().lower()
        new_config['language'] = new_lang
        
        try:
            config_json = json.dumps(new_config, indent=4)
            encoded_data = base64.b64encode(config_json.encode('utf-8'))
            with open('db_config.json', 'wb') as f:
                f.write(encoded_data)
            self.db_config = new_config
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('config_save_success'), parent=win)
        except Exception as e:
            messagebox.showerror(self.get_string('save_btn'), self.get_string('config_save_error', error=e), parent=win)
        
        if self.current_language != new_lang:
            self.current_language = new_lang
            self.create_login_widgets()
        win.destroy()
    
    def test_db_connection(self, entries, parent_win):
        test_config = {k: v.get() for k, v in entries.items()}
        if not all(test_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            messagebox.showwarning(self.get_string('test_connection_btn'), self.get_string('test_connection_warning_fill_fields'), parent=parent_win)
            return
        
        conn_params = get_connection_params(test_config)
        try:
            with psycopg2.connect(**conn_params):
                messagebox.showinfo(self.get_string('test_connection_btn'), self.get_string('test_connection_success'), parent=parent_win)
        except Exception as e:
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('test_connection_failed_db', error=e), parent=parent_win)