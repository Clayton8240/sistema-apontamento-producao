# -*- coding: utf-8 -*-

import ttkbootstrap as tb
from tkinter import Toplevel, BOTH, YES, X
from ttkbootstrap.constants import *
from config import LANGUAGES
from ui_components import LookupTableManagerWindow
from .production_app_window import App
from .pcp_window import PCPWindow
from .view_appointments_window import ViewAppointmentsWindow
from .dashboard_manager_view import DashboardManagerView

class MenuPrincipalWindow(tb.Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.db_config = db_config
        self.master = master
        self.current_language = self.db_config.get('language', 'portugues')
        self.set_localized_title()
        self.geometry("600x450")
        w, h = 600, 450
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.open_windows = {}

        self.create_menu()
        self.create_widgets()
    
    def get_string(self, key, **kwargs):
        return LANGUAGES.get(self.current_language, LANGUAGES['portugues']).get(key, f"_{key}_").format(**kwargs)

    def set_localized_title(self):
        self.title(self.get_string('main_menu_title'))

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=(20, 20))
        main_frame.pack(fill=BOTH, expand=YES)
        tb.Label(main_frame, text=self.get_string('main_menu_title'), bootstyle=PRIMARY, font=("Helvetica", 16, "bold")).pack(pady=(10, 30))
        btn_style = "primary-outline"
        btn_padding = {'pady': 8, 'padx': 20, 'ipadx': 10, 'ipady': 10}
        
        tb.Button(main_frame, text=self.get_string('btn_production_entry'), bootstyle=btn_style, command=self.open_production_window).pack(fill=X, **btn_padding)
        tb.Button(main_frame, text=self.get_string('btn_pcp_management'), bootstyle=btn_style, command=self.open_pcp_window).pack(fill=X, **btn_padding)
        tb.Button(main_frame, text=self.get_string('btn_view_entries'), bootstyle=btn_style, command=self.open_view_window).pack(fill=X, **btn_padding)
        
        # --- BOTÃO CORRIGIDO ---
        # O 'command' agora aponta para a função 'open_manager_dashboard'
        tb.Button(main_frame, text="Dashboard Gerencial", bootstyle="success-outline", command=self.open_manager_dashboard).pack(fill=X, **btn_padding)

    def create_menu(self):
        self.menubar = tb.Menu(self)
        config_menu = tb.Menu(self.menubar, tearoff=0)
        config_menu.add_command(label=self.get_string('menu_db_config'), command=lambda: self.master.open_configure_db_window(self))
        config_menu.add_command(label=self.get_string('menu_manage_lookup'), command=lambda: LookupTableManagerWindow(self, self.db_config, self.refresh_main_pcp_comboboxes))
        self.menubar.add_cascade(label=self.get_string('menu_settings'), menu=config_menu)
        self.config(menu=self.menubar)
    
    def refresh_main_pcp_comboboxes(self):
        if 'pcp' in self.open_windows and self.open_windows['pcp'].winfo_exists():
            self.open_windows['pcp'].load_all_combobox_data()

    def open_production_window(self):
        if 'production' not in self.open_windows or not self.open_windows['production'].winfo_exists():
            self.open_windows['production'] = App(master=self, db_config=self.db_config)
            self.open_windows['production'].protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('production'))
        else:
            self.open_windows['production'].lift()
    
    def open_pcp_window(self):
        if 'pcp' not in self.open_windows or not self.open_windows['pcp'].winfo_exists():
            self.open_windows['pcp'] = PCPWindow(master=self, db_config=self.db_config)
            self.open_windows['pcp'].protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('pcp'))
        else:
            self.open_windows['pcp'].lift()

    def open_view_window(self):
        if 'view' not in self.open_windows or not self.open_windows['view'].winfo_exists():
            self.open_windows['view'] = ViewAppointmentsWindow(master=self, db_config=self.db_config)
            self.open_windows['view'].protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('view'))
        else:
            self.open_windows['view'].lift()
    
    # --- FUNÇÃO PARA ABRIR O DASHBOARD ---
    # Esta função agora será chamada pelo botão corretamente
    def open_manager_dashboard(self):
        if 'dashboard' not in self.open_windows or not self.open_windows['dashboard'].winfo_exists():
            self.open_windows['dashboard'] = DashboardManagerView(master=self, db_config=self.db_config)
            self.open_windows['dashboard'].protocol("WM_DELETE_WINDOW", lambda: self.on_window_close('dashboard'))
        else:
            self.open_windows['dashboard'].lift()

    def on_window_close(self, window_key):
        if window_key in self.open_windows:
            if self.open_windows[window_key].winfo_exists():
                self.open_windows[window_key].destroy()
            del self.open_windows[window_key]