# -*- coding: utf-8 -*-

"""
Componentes de UI reutilizáveis, como janelas de gerenciamento.
"""

import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, END, CENTER

# Importações do nosso projeto
from config import LOOKUP_TABLE_SCHEMAS
   
class LookupTableManagerWindow(Toplevel):
    lookup_table_schemas = LOOKUP_TABLE_SCHEMAS

    def __init__(self, master, db_config, refresh_main_comboboxes_callback=None):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.refresh_main_comboboxes_callback = refresh_main_comboboxes_callback
        self.current_table = None
        self.current_table_display_name = None
        self.set_localized_title()
        self.create_manager_ui()
        self.update_idletasks()
        window_width = 800
        window_height = 600
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (window_width // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.grab_set()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def set_localized_title(self):
        self.title(self.get_string('manager_title'))

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_manager_ui(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        selection_frame = tb.LabelFrame(main_frame, text=self.get_string('manager_select_table'), bootstyle="primary", padding=10)
        selection_frame.pack(fill="x", pady=(0, 10))
        tb.Label(selection_frame, text=self.get_string('table_label') + ":", font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
        
        table_display_names_translated = sorted([self.get_string(schema["display_name_key"]) for schema in self.lookup_table_schemas.values()])

        self.table_selector_combobox = tb.Combobox(selection_frame, values=table_display_names_translated, font=("Helvetica", 10), state="readonly")
        self.table_selector_combobox.pack(side="left", padx=5, fill="x", expand=True)
        self.table_selector_combobox.bind("<<ComboboxSelected>>", self.on_table_selected)
        button_frame = tb.Frame(main_frame, padding=5)
        button_frame.pack(fill="x", pady=(0, 10))
        tb.Button(button_frame, text=self.get_string('add_new_btn'), bootstyle="success-outline", command=self.open_add_edit_window).pack(side="left", padx=5, expand=True)
        tb.Button(button_frame, text=self.get_string('edit_selected_btn'), bootstyle="info-outline", command=lambda: self.open_add_edit_window(edit_mode=True)).pack(side="left", padx=5, expand=True)
        tb.Button(button_frame, text=self.get_string('delete_selected_btn'), bootstyle="danger-outline", command=self.delete_selected_entry).pack(side="left", padx=5, expand=True)
        self.tree_frame = tb.Frame(main_frame)
        self.tree_frame.pack(fill="both", expand=True)
        self.treeview = tb.Treeview(self.tree_frame, columns=[], show="headings", bootstyle="primary")
        self.treeview.pack(side="left", fill="both", expand=True)
        tree_scrollbar_y = tb.Scrollbar(self.tree_frame, orient="vertical", command=self.treeview.yview)
        tree_scrollbar_y.pack(side="right", fill="y")
        self.treeview.configure(yscrollcommand=tree_scrollbar_y.set)
        tree_scrollbar_x = tb.Scrollbar(main_frame, orient="horizontal", command=self.treeview.xview)
        tree_scrollbar_x.pack(fill="x")
        self.treeview.configure(xscrollcommand=tree_scrollbar_x.set)
        if self.current_table_display_name:
            self.table_selector_combobox.set(self.current_table_display_name)
            self.on_table_selected()

    def on_table_selected(self, event=None):
        selected_display_name = self.table_selector_combobox.get()
        self.current_table = next((db_table_name for db_table_name, schema in self.lookup_table_schemas.items() if self.get_string(schema["display_name_key"]) == selected_display_name), None)
        if self.current_table:
            self.load_table_data(self.current_table)
        else:
            messagebox.showwarning(self.get_string('manager_select_table'), self.get_string('select_table_warning'), parent=self)

    def load_table_data(self, table_name):
        conn = self.get_db_connection()
        if not conn: return
        schema = self.lookup_table_schemas.get(table_name)
        if not schema:
            messagebox.showerror(self.get_string('db_load_table_failed'), self.get_string('schema_not_found', table_name=table_name), parent=self)
            return
        for item in self.treeview.get_children(): self.treeview.delete(item)
        display_headers = [self.get_string(col_data["display_key"]) for col_data in schema["columns"].values()]
        db_columns_order = [col_data["db_column"] for col_data in schema["columns"].values()]
        self.treeview.config(columns=db_columns_order)
        for db_col, display_header in zip(db_columns_order, display_headers):
            self.treeview.heading(db_col, text=display_header)
            self.treeview.column(db_col, width=100, anchor=CENTER)
        try:
            with conn.cursor() as cur:
                query_columns = ', '.join([f'"{col_data["db_column"]}"' for col_data in schema["columns"].values()])
                cur.execute(f"SELECT {query_columns} FROM {schema['table']} ORDER BY \"{schema['pk_column']}\"")
                for row in cur.fetchall(): self.treeview.insert("", END, values=row)
        except psycopg2.Error as e:
            messagebox.showerror(self.get_string('db_load_table_failed'), self.get_string('db_load_table_failed', display_name=self.get_string(schema['display_name_key']), error=e), parent=self)
        finally:
            if conn: conn.close()

    def open_add_edit_window(self, edit_mode=False):
        if not self.current_table:
            messagebox.showwarning(self.get_string('manager_select_table'), self.get_string('select_table_warning'), parent=self)
            return
        selected_item = self.treeview.focus()
        if edit_mode and not selected_item:
            messagebox.showwarning(self.get_string('edit_selected_btn'), self.get_string('select_entry_to_edit'), parent=self)
            return
        schema = self.lookup_table_schemas[self.current_table]
        current_values = {}
        pk_value = None
        if edit_mode:
            raw_values = self.treeview.item(selected_item, 'values')
            pk_index = list(schema["columns"].keys()).index(schema["pk_column"])
            pk_value = raw_values[pk_index]
            for i, (col_name, col_data) in enumerate(schema["columns"].items()):
                current_values[col_data["db_column"]] = raw_values[i]

        add_edit_win = Toplevel(self)
        add_edit_win.title(f"{self.get_string('edit_selected_btn') if edit_mode else self.get_string('add_new_btn')} - {self.get_string(schema['display_name_key'])}")
        add_edit_win.transient(self)
        add_edit_win.grab_set()
        form_entries = {}
        for i, (col_name, col_data) in enumerate(schema["columns"].items()):
            db_col = col_data["db_column"]
            if not edit_mode and col_name == schema["pk_column"]:
                continue
            
            tb.Label(add_edit_win, text=f"{self.get_string(col_data['display_key'])}:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = tb.Entry(add_edit_win)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            form_entries[db_col] = entry

            if edit_mode and db_col in current_values:
                entry.insert(0, current_values[db_col])
            
            if not col_data["editable"] or (edit_mode and col_name == schema["pk_column"]):
                 entry.config(state="readonly")

        action_frame = tb.Frame(add_edit_win)
        action_frame.grid(row=len(schema["columns"]) + 1, columnspan=2, pady=15)
        tb.Button(action_frame, text=self.get_string('save_btn'), bootstyle="success", command=lambda: self.save_entry(add_edit_win, form_entries, edit_mode, pk_value)).pack(side="left", padx=5)
        tb.Button(action_frame, text=self.get_string('cancel_btn'), bootstyle="secondary", command=add_edit_win.destroy).pack(side="left", padx=5)
    
    def save_entry(self, window, entries, edit_mode, pk_value=None):
        conn = self.get_db_connection()
        if not conn: return
        schema = self.lookup_table_schemas[self.current_table]
        data = {}
        
        try:
            for db_col, widget in entries.items():
                val = widget.get().strip()
                col_config = next((c for c in schema["columns"].values() if c["db_column"] == db_col), None)
                if col_config:
                    if col_config["type"] == "int" and val:
                        try:
                            data[db_col] = int(val)
                        except ValueError:
                             messagebox.showerror(self.get_string('invalid_input'), f"O campo para '{self.get_string(col_config['display_key'])}' deve ser um número inteiro.", parent=window)
                             return
                    else:
                        data[db_col] = val or None
        except ValueError as e:
            offending_field = next(self.get_string(c['display_key']) for c in schema["columns"].values() if c["db_column"] == db_col)
            messagebox.showerror(self.get_string('invalid_input'), self.get_string('save_entry_validation_error', field_name=offending_field), parent=window)
            return
        
        try:
            with conn.cursor() as cur:
                if edit_mode:
                    set_clauses = [f'"{db_col}" = %s' for db_col in data.keys()]
                    values = list(data.values()) + [pk_value]
                    query = f"UPDATE {schema['table']} SET {', '.join(set_clauses)} WHERE \"{schema['pk_column']}\" = %s"
                else:
                    cols = [f'"{db_col}"' for db_col in data.keys()]
                    values = list(data.values())
                    query = f"INSERT INTO {schema['table']} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(values))})"
                
                cur.execute(query, values)
            conn.commit()
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('entry_edited_success' if edit_mode else 'new_entry_added_success'), parent=window)
            window.destroy()
            self.load_table_data(self.current_table)
            if self.refresh_main_comboboxes_callback: self.refresh_main_comboboxes_callback()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror(self.get_string('db_save_failed'), self.get_string('db_save_failed', error=e), parent=window)
        finally:
            if conn: conn.close()

    def delete_selected_entry(self):
        item = self.treeview.focus()
        if not item:
            messagebox.showwarning(self.get_string('delete_selected_btn'), self.get_string('select_entry_to_delete'), parent=self)
            return
        
        schema = self.lookup_table_schemas[self.current_table]
        item_values = self.treeview.item(item, 'values')
        
        db_cols_order = [c["db_column"] for c in schema["columns"].values()]
        pk_index = db_cols_order.index(schema["pk_column"])
        pk_val = item_values[pk_index]
        display_name = self.get_string(schema['display_name_key'])

        if not messagebox.askyesno(self.get_string('confirm_delete_title'), self.get_string('confirm_delete_message', pk_value=pk_val, display_name=display_name), parent=self):
            return
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {schema['table']} WHERE \"{schema['pk_column']}\" = %s", (pk_val,))
            conn.commit()
            messagebox.showinfo(self.get_string('delete_selected_btn'), self.get_string('delete_success'), parent=self)
            self.load_table_data(self.current_table)
            if self.refresh_main_comboboxes_callback: self.refresh_main_comboboxes_callback()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror(self.get_string('delete_selected_btn'), self.get_string('db_delete_failed', error=e), parent=self)
        finally:
            if conn: conn.close()    