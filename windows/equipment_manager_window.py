import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import psycopg2

from database import get_db_connection, release_db_connection
from languages import LANGUAGES
from schemas import LOOKUP_TABLE_SCHEMAS # <-- NEW IMPORT
from services import ServiceError, get_all_equipment_types, create_equipment_type, update_equipment_type, delete_equipment_type, get_all_equipment_fields, create_equipment_field, update_equipment_field, delete_equipment_field, get_equipment_type_fields, add_equipment_type_field, remove_equipment_type_field

class EquipmentManagerWindow(tb.Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')
        self.title(self.get_string('equipment_manager_title'))
        self.geometry("1000x700")
        self.transient(master)
        self.grab_set()

        self.create_widgets()
        self.load_data()

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        # --- Equipment Types Section ---
        equip_types_frame = tb.LabelFrame(main_frame, text=self.get_string('equipment_types_section'), bootstyle=PRIMARY, padding=10)
        equip_types_frame.pack(fill=X, pady=5)
        equip_types_frame.grid_columnconfigure(0, weight=1)

        self.equip_types_tree = ttk.Treeview(equip_types_frame, columns=("id", "description", "time_per_sheet"), show="headings")
        self.equip_types_tree.heading("id", text=self.get_string('col_id'))
        self.equip_types_tree.heading("description", text=self.get_string('col_description'))
        self.equip_types_tree.heading("time_per_sheet", text=self.get_string('col_time_per_sheet'))
        self.equip_types_tree.column("id", width=50, anchor=tk.CENTER)
        self.equip_types_tree.column("description", width=200, anchor=tk.W)
        self.equip_types_tree.column("time_per_sheet", width=150, anchor=tk.CENTER)
        self.equip_types_tree.pack(fill=BOTH, expand=True)

        equip_types_buttons_frame = tb.Frame(equip_types_frame)
        equip_types_buttons_frame.pack(pady=5)
        tb.Button(equip_types_buttons_frame, text=self.get_string('add_btn'), command=self.add_equip_type).pack(side=tk.LEFT, padx=5)
        tb.Button(equip_types_buttons_frame, text=self.get_string('edit_btn'), command=self.edit_equip_type).pack(side=tk.LEFT, padx=5)
        tb.Button(equip_types_buttons_frame, text=self.get_string('delete_btn'), command=self.delete_equip_type).pack(side=tk.LEFT, padx=5)

        # --- Dynamic Fields Section ---
        dynamic_fields_frame = tb.LabelFrame(main_frame, text=self.get_string('dynamic_fields_section'), bootstyle=INFO, padding=10)
        dynamic_fields_frame.pack(fill=X, pady=5)
        dynamic_fields_frame.grid_columnconfigure(0, weight=1)

        self.dynamic_fields_tree = ttk.Treeview(dynamic_fields_frame, columns=("id", "name", "label", "data_type", "widget_type", "lookup_table"), show="headings")
        self.dynamic_fields_tree.heading("id", text=self.get_string('col_id'))
        self.dynamic_fields_tree.heading("name", text=self.get_string('col_field_name'))
        self.dynamic_fields_tree.heading("label", text=self.get_string('col_translation_key'))
        self.dynamic_fields_tree.heading("data_type", text=self.get_string('col_data_type'))
        self.dynamic_fields_tree.heading("widget_type", text=self.get_string('col_widget_type'))
        self.dynamic_fields_tree.heading("lookup_table", text=self.get_string('col_lookup_table'))
        self.dynamic_fields_tree.column("id", width=50, anchor=tk.CENTER)
        self.dynamic_fields_tree.column("name", width=100, anchor=tk.W)
        self.dynamic_fields_tree.column("label", width=100, anchor=tk.W)
        self.dynamic_fields_tree.column("data_type", width=80, anchor=tk.CENTER)
        self.dynamic_fields_tree.column("widget_type", width=80, anchor=tk.CENTER)
        self.dynamic_fields_tree.column("lookup_table", width=100, anchor=tk.W)
        self.dynamic_fields_tree.pack(fill=BOTH, expand=True)

        dynamic_fields_buttons_frame = tb.Frame(dynamic_fields_frame)
        dynamic_fields_buttons_frame.pack(pady=5)
        tb.Button(dynamic_fields_buttons_frame, text=self.get_string('add_btn'), command=self.add_dynamic_field).pack(side=tk.LEFT, padx=5)
        tb.Button(dynamic_fields_buttons_frame, text=self.get_string('edit_btn'), command=self.edit_dynamic_field).pack(side=tk.LEFT, padx=5)
        tb.Button(dynamic_fields_buttons_frame, text=self.get_string('delete_btn'), command=self.delete_dynamic_field).pack(side=tk.LEFT, padx=5)

        # --- Association Section ---
        association_frame = tb.LabelFrame(main_frame, text=self.get_string('field_association_section'), bootstyle=SUCCESS, padding=10)
        association_frame.pack(fill=BOTH, expand=True, pady=5)
        association_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Left: Equipment Type Selection
        equip_type_select_frame = tb.Frame(association_frame)
        equip_type_select_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        tb.Label(equip_type_select_frame, text=self.get_string('select_equipment_type') + ":").pack(pady=5)
        self.equip_type_combobox = tb.Combobox(equip_type_select_frame, state="readonly")
        self.equip_type_combobox.pack(fill=X, pady=5)
        self.equip_type_combobox.bind("<<ComboboxSelected>>", self.on_equip_type_selected)

        # Middle: Available Fields
        available_fields_frame = tb.Frame(association_frame)
        available_fields_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        tb.Label(available_fields_frame, text=self.get_string('available_fields') + ":").pack(pady=5)
        self.available_fields_listbox = tk.Listbox(available_fields_frame, selectmode=tk.MULTIPLE)
        self.available_fields_listbox.pack(fill=BOTH, expand=True)

        # Right: Assigned Fields
        assigned_fields_frame = tb.Frame(association_frame)
        assigned_fields_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        tb.Label(assigned_fields_frame, text=self.get_string('assigned_fields') + ":").pack(pady=5)
        self.assigned_fields_listbox = tk.Listbox(assigned_fields_frame, selectmode=tk.MULTIPLE)
        self.assigned_fields_listbox.pack(fill=BOTH, expand=True)

        # Association Buttons
        association_buttons_frame = tb.Frame(association_frame)
        association_buttons_frame.grid(row=1, column=1, pady=10)
        tb.Button(association_buttons_frame, text=self.get_string('assign_btn'), command=self.assign_field).pack(side=tk.LEFT, padx=2)
        tb.Button(association_buttons_frame, text=self.get_string('unassign_btn'), command=self.unassign_field).pack(side=tk.LEFT, padx=2)

    def load_data(self):
        self.load_equip_types()
        self.load_dynamic_fields()

    def load_equip_types(self):
        for i in self.equip_types_tree.get_children():
            self.equip_types_tree.delete(i)
        try:
            equip_types = get_all_equipment_types()
            for et in equip_types:
                self.equip_types_tree.insert("", tk.END, values=(et["id"], et["descricao"], et["tempo_por_folha_ms"])) # Assuming these keys
            
            # Populate combobox for association
            self.equip_type_combobox['values'] = [et["descricao"] for et in equip_types]
            self.equip_type_map = {et["descricao"]: et["id"] for et in equip_types}

        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"Erro ao carregar tipos de equipamento: {e}", parent=self)

    def load_dynamic_fields(self):
        for i in self.dynamic_fields_tree.get_children():
            self.dynamic_fields_tree.delete(i)
        try:
            fields = get_all_equipment_fields()
            for f in fields:
                self.dynamic_fields_tree.insert("", tk.END, values=(f["id"], f["nome_campo"], f["label_traducao"], f["tipo_dado"], f["widget_type"], f["lookup_table"])) # Assuming these keys
            
            self.available_fields_map = {f["nome_campo"]: f["id"] for f in fields}
            self.load_available_fields_listbox()

        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"Erro ao carregar campos dinâmicos: {e}", parent=self)

    def load_available_fields_listbox(self):
        self.available_fields_listbox.delete(0, tk.END)
        for field_name in self.available_fields_map.keys():
            self.available_fields_listbox.insert(tk.END, field_name)

    def on_equip_type_selected(self, event=None):
        selected_equip_type_desc = self.equip_type_combobox.get()
        equip_type_id = self.equip_type_map.get(selected_equip_type_desc)
        if equip_type_id:
            self.load_assigned_fields(equip_type_id)
        else:
            self.assigned_fields_listbox.delete(0, tk.END)

    def load_assigned_fields(self, equip_type_id):
        self.assigned_fields_listbox.delete(0, tk.END)
        try:
            assigned_fields = get_equipment_type_fields(equip_type_id)
            self.assigned_fields_map = {f["nome_campo"]: f["id"] for f in assigned_fields}
            for field_name in self.assigned_fields_map.keys():
                self.assigned_fields_listbox.insert(tk.END, field_name)
        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"Erro ao carregar campos atribuídos: {e}", parent=self)

    def _open_equip_type_dialog(self, edit_mode=False, equip_type_data=None):
        dialog = tb.Toplevel(self)
        dialog.title(self.get_string('edit_equip_type_title') if edit_mode else self.get_string('add_equip_type_title'))
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x200")

        frame = tb.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Description
        tb.Label(frame, text=self.get_string('col_description') + ":").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        desc_entry = tb.Entry(frame)
        desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Time per Sheet
        tb.Label(frame, text=self.get_string('col_time_per_sheet') + ":").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        time_entry = tb.Entry(frame)
        time_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        if edit_mode and equip_type_data:
            desc_entry.insert(0, equip_type_data['descricao'])
            time_entry.insert(0, str(equip_type_data['tempo_por_folha_ms']))

        def save_action():
            description = desc_entry.get().strip()
            tempo_por_folha_ms_str = time_entry.get().strip()

            if not description or not tempo_por_folha_ms_str:
                messagebox.showwarning(self.get_string('warning_title'), self.get_string('required_field_warning').format(field_name=self.get_string('col_description')) + " / " + self.get_string('required_field_warning').format(field_name=self.get_string('col_time_per_sheet')), parent=dialog)
                return
            
            try:
                tempo_por_folha_ms = int(tempo_por_folha_ms_str)
                if tempo_por_folha_ms <= 0:
                    raise ValueError("Tempo por folha deve ser positivo.")
            except ValueError:
                messagebox.showwarning(self.get_string('warning_title'), self.get_string('run_value_must_be_number'), parent=dialog)
                return

            try:
                if edit_mode and equip_type_data:
                    update_equipment_type(equip_type_data['id'], description, tempo_por_folha_ms)
                else:
                    create_equipment_type(description, tempo_por_folha_ms)
                messagebox.showinfo(self.get_string('success_title'), self.get_string('config_save_success'), parent=dialog)
                self.load_equip_types() # Refresh the treeview
                dialog.destroy()
            except ServiceError as e:
                messagebox.showerror(self.get_string('error_title'), f"{self.get_string('db_save_failed')}: {e}", parent=dialog)

        buttons_frame = tb.Frame(frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        tb.Button(buttons_frame, text=self.get_string('save_btn'), command=save_action, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        tb.Button(buttons_frame, text=self.get_string('cancel_btn'), command=dialog.destroy, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)

        frame.grid_columnconfigure(1, weight=1)

    def add_equip_type(self):
        self._open_equip_type_dialog(edit_mode=False)

    def edit_equip_type(self):
        selected_item = self.equip_types_tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_item_to_edit'), parent=self)
            return
        
        item_values = self.equip_types_tree.item(selected_item, 'values')
        equip_type_data = {
            'id': item_values[0],
            'descricao': item_values[1],
            'tempo_por_folha_ms': item_values[2]
        }
        self._open_equip_type_dialog(edit_mode=True, equip_type_data=equip_type_data)

    def delete_equip_type(self):
        selected_item = self.equip_types_tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_item_to_delete'), parent=self)
            return
        
        item_values = self.equip_types_tree.item(selected_item, 'values')
        equip_type_id = item_values[0]
        equip_type_desc = item_values[1]

        if messagebox.askyesno(self.get_string('confirm_delete_title'), self.get_string('confirm_delete_message').format(pk_value=equip_type_desc, display_name=self.get_string('equipment_types_section')), parent=self):
            try:
                delete_equipment_type(equip_type_id)
                messagebox.showinfo(self.get_string('success_title'), self.get_string('delete_success'), parent=self)
                self.load_equip_types()
            except ServiceError as e:
                messagebox.showerror(self.get_string('error_title'), f"{self.get_string('db_delete_failed')}: {e}", parent=self)

    def _open_dynamic_field_dialog(self, edit_mode=False, field_data=None):
        dialog = tb.Toplevel(self)
        dialog.title(self.get_string('edit_dynamic_field_title') if edit_mode else self.get_string('add_dynamic_field_title'))
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("500x300")

        frame = tb.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Field Name
        tb.Label(frame, text=self.get_string('col_field_name') + ":").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        name_entry = tb.Entry(frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # Label Translation Key
        tb.Label(frame, text=self.get_string('col_translation_key') + ":").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        label_entry = tb.Entry(frame)
        label_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        # Data Type
        tb.Label(frame, text=self.get_string('col_data_type') + ":").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        data_type_combobox = tb.Combobox(frame, values=["INTEGER", "TEXT", "BOOLEAN", "DATE", "TIME", "DATETIME"])
        data_type_combobox.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        # Widget Type
        tb.Label(frame, text=self.get_string('col_widget_type') + ":").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        widget_type_combobox = tb.Combobox(frame, values=["Entry", "Combobox", "DateEntry", "Checkbox"])
        widget_type_combobox.grid(row=3, column=1, padx=5, pady=5, sticky='ew')

        # Lookup Table
        tb.Label(frame, text=self.get_string('col_lookup_table') + ":").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        lookup_table_combobox = tb.Combobox(frame, values=[""] + list(LOOKUP_TABLE_SCHEMAS.keys()))
        lookup_table_combobox.grid(row=4, column=1, padx=5, pady=5, sticky='ew')

        if edit_mode and field_data:
            name_entry.insert(0, field_data['nome_campo'])
            label_entry.insert(0, field_data['label_traducao'])
            data_type_combobox.set(field_data['tipo_dado'])
            widget_type_combobox.set(field_data['widget_type'])
            lookup_table_combobox.set(field_data['lookup_table'] if field_data['lookup_table'] else "")

        def save_action():
            nome_campo = name_entry.get().strip()
            label_traducao = label_entry.get().strip()
            tipo_dado = data_type_combobox.get().strip()
            widget_type = widget_type_combobox.get().strip()
            lookup_table = lookup_table_combobox.get().strip() if lookup_table_combobox.get().strip() else None

            if not nome_campo or not label_traducao or not tipo_dado or not widget_type:
                messagebox.showwarning(self.get_string('warning_title'), self.get_string('required_field_warning').format(field_name=self.get_string('col_field_name')) + " / " + self.get_string('required_field_warning').format(field_name=self.get_string('col_translation_key')) + " / " + self.get_string('required_field_warning').format(field_name=self.get_string('col_data_type')) + " / " + self.get_string('required_field_warning').format(field_name=self.get_string('col_widget_type')), parent=dialog)
                return
            
            try:
                if edit_mode and field_data:
                    update_equipment_field(field_data['id'], nome_campo, label_traducao, tipo_dado, widget_type, lookup_table)
                else:
                    create_equipment_field(nome_campo, label_traducao, tipo_dado, widget_type, lookup_table)
                messagebox.showinfo(self.get_string('success_title'), self.get_string('config_save_success'), parent=dialog)
                self.load_dynamic_fields() # Refresh the treeview
                dialog.destroy()
            except ServiceError as e:
                messagebox.showerror(self.get_string('error_title'), f"{self.get_string('db_save_failed')}: {e}", parent=dialog)

        buttons_frame = tb.Frame(frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=10)
        tb.Button(buttons_frame, text=self.get_string('save_btn'), command=save_action, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        tb.Button(buttons_frame, text=self.get_string('cancel_btn'), command=dialog.destroy, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)

        frame.grid_columnconfigure(1, weight=1)

    def add_dynamic_field(self):
        self._open_dynamic_field_dialog(edit_mode=False)

    def edit_dynamic_field(self):
        selected_item = self.dynamic_fields_tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_item_to_edit'), parent=self)
            return
        
        item_values = self.dynamic_fields_tree.item(selected_item, 'values')
        field_data = {
            'id': item_values[0],
            'nome_campo': item_values[1],
            'label_traducao': item_values[2],
            'tipo_dado': item_values[3],
            'widget_type': item_values[4],
            'lookup_table': item_values[5]
        }
        self._open_dynamic_field_dialog(edit_mode=True, field_data=field_data)

    def delete_dynamic_field(self):
        selected_item = self.dynamic_fields_tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_item_to_delete'), parent=self)
            return
        
        item_values = self.dynamic_fields_tree.item(selected_item, 'values')
        field_id = item_values[0]
        field_name = item_values[1]

        if messagebox.askyesno(self.get_string('confirm_delete_title'), self.get_string('confirm_delete_message').format(pk_value=field_name, display_name=self.get_string('dynamic_fields_section')), parent=self):
            try:
                delete_equipment_field(field_id)
                messagebox.showinfo(self.get_string('success_title'), self.get_string('delete_success'), parent=self)
                self.load_dynamic_fields()
            except ServiceError as e:
                messagebox.showerror(self.get_string('error_title'), f"{self.get_string('db_delete_failed')}: {e}", parent=self)

    def assign_field(self):
        selected_fields = self.available_fields_listbox.curselection()
        if not selected_fields:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_field_to_assign'), parent=self)
            return

        selected_equip_type_desc = self.equip_type_combobox.get()
        equip_type_id = self.equip_type_map.get(selected_equip_type_desc)
        if not equip_type_id:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_equipment_type_first'), parent=self)
            return

        try:
            for index in selected_fields:
                field_name = self.available_fields_listbox.get(index)
                field_id = self.available_fields_map.get(field_name)
                if field_id:
                    # Need to determine order. For simplicity, just add to end for now.
                    add_equipment_type_field(equip_type_id, field_id, 0) # Order is placeholder
            self.load_assigned_fields(equip_type_id)
            messagebox.showinfo(self.get_string('success_title'), self.get_string('fields_assigned_success'), parent=self)
        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"Erro ao atribuir campos: {e}", parent=self)

    def unassign_field(self):
        selected_fields = self.assigned_fields_listbox.curselection()
        if not selected_fields:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_field_to_unassign'), parent=self)
            return

        selected_equip_type_desc = self.equip_type_combobox.get()
        equip_type_id = self.equip_type_map.get(selected_equip_type_desc)
        if not equip_type_id:
            messagebox.showwarning(self.get_string('warning_title'), self.get_string('select_equipment_type_first'), parent=self)
            return

        try:
            for index in selected_fields:
                field_name = self.assigned_fields_listbox.get(index)
                field_id = self.assigned_fields_map.get(field_name)
                if field_id:
                    remove_equipment_type_field(equip_type_id, field_id)
            self.load_assigned_fields(equip_type_id)
            messagebox.showinfo(self.get_string('success_title'), self.get_string('fields_unassigned_success'), parent=self)
        except ServiceError as e:
            messagebox.showerror(self.get_string('error_title'), f"Erro ao desatribuir campos: {e}", parent=self)