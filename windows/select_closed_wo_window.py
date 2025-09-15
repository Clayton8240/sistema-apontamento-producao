# -*- coding: utf-8 -*- 

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from services import get_closed_production_orders, ServiceError
from languages import LANGUAGES

class SelectClosedWOWindow(tb.Toplevel):
    def __init__(self, master, db_config, on_select_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.on_select_callback = on_select_callback
        self.current_language = self.db_config.get('language', 'portugues')

        self.title(self.get_string('select_closed_wo_title'))
        self.geometry("1000x600")
        self.grab_set() # Make this window modal
        self.focus_set()

        self.closed_orders_data = []
        self.create_widgets()
        self.load_closed_orders()

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        # Search Frame
        search_frame = tb.Frame(main_frame)
        search_frame.pack(fill=X, pady=(0, 10))

        tb.Label(search_frame, text=self.get_string('search_label') + ":").pack(side=LEFT, padx=5)
        self.search_entry = tb.Entry(search_frame)
        self.search_entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_orders)
        
        self.placeholder_text = self.get_string('search_wo_pn_client_placeholder')
        self.search_entry.insert(0, self.placeholder_text)
        self.search_entry.config(foreground='grey')
        self.search_entry.bind("<FocusIn>", self._on_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)

        # Treeview for Closed Orders
        tree_frame = tb.LabelFrame(main_frame, text=self.get_string('closed_wo_list_label'), bootstyle=PRIMARY, padding=10)
        tree_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        cols = ('id', 'numero_wo', 'pn_partnumber', 'cliente', 'data_previsao_entrega')
        headers = ('ID', self.get_string('col_wo'), self.get_string('PN (Partnumber)'), self.get_string('col_cliente'), self.get_string('col_data_previsao'))
        
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=150, anchor=CENTER)
        self.tree.column('id', width=0, stretch=False) # Hide ID column
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)

        scrollbar = tb.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))

        tb.Button(button_frame, text=self.get_string('select_btn'), command=self.select_wo, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(button_frame, text=self.get_string('cancel_btn'), command=self.destroy, bootstyle=DANGER).pack(side=RIGHT, padx=5)

    def _on_focus_in(self, event):
        if self.search_entry.get() == self.placeholder_text:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(foreground='black')

    def _on_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, self.placeholder_text)
            self.search_entry.config(foreground='grey')

    def load_closed_orders(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            self.closed_orders_data = get_closed_production_orders()
            for order in self.closed_orders_data:
                data_formatada = order['data_previsao_entrega'].strftime('%d/%m/%Y') if order['data_previsao_entrega'] else ""
                values = (order['id'], order['numero_wo'], order['pn_partnumber'], order['cliente'], data_formatada)
                self.tree.insert("", "end", values=values, iid=order['id'])
        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"{self.get_string('load_wo_error')}: {e}", parent=self)

    def filter_orders(self, event=None):
        search_term = self.search_entry.get().lower()
        # If the search term is the placeholder, treat it as empty
        if search_term == self.placeholder_text.lower():
            search_term = ""

        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for order in self.closed_orders_data:
            if search_term in str(order['numero_wo']).lower() or \
               search_term in str(order['pn_partnumber']).lower() or \
               search_term in str(order['cliente']).lower():
                data_formatada = order['data_previsao_entrega'].strftime('%d/%m/%Y') if order['data_previsao_entrega'] else ""
                values = (order['id'], order['numero_wo'], order['pn_partnumber'], order['cliente'], data_formatada)
                self.tree.insert("", "end", values=values, iid=order['id'])

    def select_wo(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_wo_msg'), parent=self)
            return
        
        selected_wo_id = int(selected_item_id)
        selected_wo_data = next((wo for wo in self.closed_orders_data if wo['id'] == selected_wo_id), None)

        if selected_wo_data and self.on_select_callback:
            self.on_select_callback(selected_wo_data)
            self.destroy()

        tree_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        cols = ('id', 'numero_wo', 'pn_partnumber', 'cliente', 'data_previsao_entrega')
        headers = ('ID', self.get_string('col_wo'), self.get_string('PN (Partnumber)'), self.get_string('col_cliente'), self.get_string('col_data_previsao'))
        
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=150, anchor=CENTER)
        self.tree.column('id', width=0, stretch=False) # Hide ID column
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)

        scrollbar = tb.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))

        tb.Button(button_frame, text=self.get_string('select_btn'), command=self.select_wo, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(button_frame, text=self.get_string('cancel_btn'), command=self.destroy, bootstyle=DANGER).pack(side=RIGHT, padx=5)

    def load_closed_orders(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            self.closed_orders_data = get_closed_production_orders()
            for order in self.closed_orders_data:
                data_formatada = order['data_previsao_entrega'].strftime('%d/%m/%Y') if order['data_previsao_entrega'] else ""
                values = (order['id'], order['numero_wo'], order['pn_partnumber'], order['cliente'], data_formatada)
                self.tree.insert("", "end", values=values, iid=order['id'])
        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"{self.get_string('load_wo_error')}: {e}", parent=self)

    def filter_orders(self, event=None):
        search_term = self.search_entry.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for order in self.closed_orders_data:
            if search_term in str(order['numero_wo']).lower() or \
               search_term in str(order['pn_partnumber']).lower() or \
               search_term in str(order['cliente']).lower():
                data_formatada = order['data_previsao_entrega'].strftime('%d/%m/%Y') if order['data_previsao_entrega'] else ""
                values = (order['id'], order['numero_wo'], order['pn_partnumber'], order['cliente'], data_formatada)
                self.tree.insert("", "end", values=values, iid=order['id'])

    def select_wo(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_wo_msg'), parent=self)
            return
        
        selected_wo_id = int(selected_item_id)
        selected_wo_data = next((wo for wo in self.closed_orders_data if wo['id'] == selected_wo_id), None)

        if selected_wo_data and self.on_select_callback:
            self.on_select_callback(selected_wo_data)
            self.destroy()


