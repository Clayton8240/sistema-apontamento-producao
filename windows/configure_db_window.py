# Ficheiro: sistema-apontamento-producao/windows/configure_db_window.py

import json
import base64
import keyring
import ttkbootstrap as tb
from tkinter import Toplevel, messagebox, END, BOTH
from languages import LANGUAGES
from database import test_db_connection

KEYRING_SERVICE_NAME = "sistema-apontamento-producao"

class ConfigureDBWindow(Toplevel):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app_controller = app_controller
        self.db_config = app_controller.db_config
        self.current_language = self.db_config.get('language', 'portugues')

        self.title(self.get_string('config_win_title'))
        self.transient(parent)
        self.grab_set()

        frame = tb.Frame(self, padding=10)
        frame.pack(expand=True, fill=BOTH)

        labels = [("host", 'host_label'), ("porta", 'port_label'), ("usuário", 'user_label'), ("senha", 'password_label'), ("banco", 'db_label')]
        self.entries = {}

        db_user = self.db_config.get('usuário', '')
        saved_password = keyring.get_password(KEYRING_SERVICE_NAME, db_user) if db_user else ''

        for i, (key, label_key) in enumerate(labels):
            tb.Label(frame, text=self.get_string(label_key) + ":").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            e = tb.Entry(frame, show='*' if key == "senha" else '')
            e.grid(row=i, column=1, padx=5, pady=5, sticky="ew")

            if key == "senha":
                if saved_password:
                    e.insert(0, saved_password)
            else:
                e.insert(0, self.db_config.get(key, ''))

            self.entries[key] = e

        tb.Label(frame, text=self.get_string('language_label') + ":").grid(row=len(labels), column=0, padx=5, pady=5, sticky="w")
        lang_opts = [lang.capitalize() for lang in LANGUAGES.keys()]
        self.lang_selector = tb.Combobox(frame, values=lang_opts, state="readonly")
        self.lang_selector.grid(row=len(labels), column=1, padx=5, pady=5, sticky="ew")
        self.lang_selector.set(self.current_language.capitalize())

        frame.columnconfigure(1, weight=1)

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=len(labels) + 1, columnspan=2, pady=15)
        tb.Button(btn_frame, text=self.get_string('test_connection_btn'), bootstyle="info-outline", command=self.run_connection_test).pack(side="left", padx=5)
        tb.Button(btn_frame, text=self.get_string('save_btn'), bootstyle="success", command=self.save_and_close_config).pack(side="left", padx=5)

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, f"_{key}_").format(**kwargs)

    def save_and_close_config(self):
        new_config = {}
        password_to_save = None
        db_user_to_save = None

        for key, widget in self.entries.items():
            if key == "senha":
                password_to_save = widget.get()
            else:
                new_config[key] = widget.get()
                if key == "usuário":
                    db_user_to_save = widget.get()

        new_config['tabela'] = self.db_config.get('tabela', 'apontamento')
        new_lang = self.lang_selector.get().lower()
        new_config['language'] = new_lang

        try:
            if db_user_to_save and password_to_save:
                keyring.set_password(KEYRING_SERVICE_NAME, db_user_to_save, password_to_save)
            elif db_user_to_save:
                try:
                    keyring.delete_password(KEYRING_SERVICE_NAME, db_user_to_save)
                except keyring.errors.PasswordDeleteError:
                    pass

            config_json = json.dumps(new_config, indent=4)
            encoded_data = base64.b64encode(config_json.encode('utf-8'))
            with open('db_config.json', 'wb') as f:
                f.write(encoded_data)

            self.app_controller.db_config = new_config
            self.current_language = new_lang
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('config_save_success'), parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror(self.get_string('save_btn'), self.get_string('config_save_error', error=e), parent=self)

    def run_connection_test(self):
        test_config = {k: v.get() for k, v in self.entries.items()}
        if not all(test_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            messagebox.showwarning(self.get_string('test_connection_btn'), self.get_string('test_connection_warning_fill_fields'), parent=self)
            return

        success, message = test_db_connection(test_config)
        if success:
            messagebox.showinfo(self.get_string('test_connection_btn'), self.get_string('test_connection_success'), parent=self)
        else:
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('test_connection_failed_db', error=message), parent=self)
