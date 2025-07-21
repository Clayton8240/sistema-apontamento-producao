# -*- coding: utf-8 -*-

import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, END, BOTH, YES, X, W, LEFT, CENTER, EW

from config import LANGUAGES

class ServiceManagerWindow(Toplevel):
    def __init__(self, master, db_config, ordem_id, wo_number, refresh_callback=None):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.ordem_id = ordem_id
        self.wo_number = wo_number
        self.refresh_callback = refresh_callback

        self.title(self.get_string("service_manager_title", wo=self.wo_number))
        self.geometry("700x500")
        self.transient(master)
        self.grab_set()

        self.create_widgets()
        self.load_services()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(0, 10))
        tb.Button(btn_frame, text=self.get_string("add_service_btn"), command=self.add_edit_service, bootstyle="success-outline").pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text=self.get_string("edit_service_btn"), command=lambda: self.add_edit_service(edit_mode=True), bootstyle="info-outline").pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text=self.get_string("delete_service_btn"), command=self.delete_service, bootstyle="danger-outline").pack(side=LEFT, padx=5)

        tree_frame = tb.LabelFrame(main_frame, text=self.get_string("services_section_title"), bootstyle=PRIMARY, padding=10)
        tree_frame.pack(fill=BOTH, expand=YES)

        cols = ("id", "sequencia", "descricao", "status")
        headers = (self.get_string("col_id"), self.get_string("col_sequencia"), self.get_string("col_servico_descricao"), self.get_string("col_servico_status"))
        
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=100, anchor=W)
        self.tree.column("id", width=40, anchor=CENTER)
        self.tree.column("sequencia", width=80, anchor=CENTER)
        self.tree.column("descricao", width=300)
        self.tree.pack(fill=BOTH, expand=YES)

    def load_services(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, sequencia, descricao, status FROM ordem_servicos WHERE ordem_id = %s ORDER BY sequencia", (self.ordem_id,))
                for row in cur.fetchall():
                    self.tree.insert("", END, values=row)
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Falha ao carregar etapas: {e}", parent=self)
        finally:
            if conn: conn.close()

    def add_edit_service(self, edit_mode=False):
        service_id, current_seq, current_desc = None, "", ""
        if edit_mode:
            selected_item = self.tree.focus()
            if not selected_item:
                messagebox.showwarning(self.get_string("selection_required_title"), self.get_string("select_service_to_edit"), parent=self)
                return
            values = self.tree.item(selected_item, "values")
            service_id, current_seq, current_desc = values[0], values[1], values[2]

        win = Toplevel(self)
        title_key = "edit_service_title" if edit_mode else "add_service_title"
        win.title(self.get_string(title_key))
        win.grab_set()

        form_frame = tb.Frame(win, padding=10)
        form_frame.pack(fill=BOTH, expand=YES)

        tb.Label(form_frame, text=self.get_string("col_sequencia") + ":").grid(row=0, column=0, padx=10, pady=5, sticky=W)
        seq_entry = tb.Entry(form_frame)
        seq_entry.grid(row=0, column=1, padx=10, pady=5, sticky=EW)
        if current_seq: seq_entry.insert(0, current_seq)

        tb.Label(form_frame, text=self.get_string("col_servico_descricao") + ":").grid(row=1, column=0, padx=10, pady=5, sticky=W)
        desc_entry = tb.Entry(form_frame, width=50)
        desc_entry.grid(row=1, column=1, padx=10, pady=5, sticky=EW)
        desc_entry.insert(0, current_desc)
        
        form_frame.grid_columnconfigure(1, weight=1)

        btn_save = tb.Button(form_frame, text=self.get_string("save_btn"), bootstyle=SUCCESS,
                             command=lambda: self.save_service(win, service_id, seq_entry.get(), desc_entry.get()))
        btn_save.grid(row=2, columnspan=2, pady=10)

    def save_service(self, win, service_id, seq, desc):
        if not desc:
            messagebox.showwarning(self.get_string("required_field_warning", field_name=self.get_string("col_servico_descricao")), parent=win)
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                if service_id:
                    query = "UPDATE ordem_servicos SET sequencia = %s, descricao = %s WHERE id = %s"
                    params = (int(seq) if seq and seq.isdigit() else None, desc, service_id)
                else:
                    query = "INSERT INTO ordem_servicos (ordem_id, sequencia, descricao) VALUES (%s, %s, %s)"
                    params = (self.ordem_id, int(seq) if seq and seq.isdigit() else None, desc)
                cur.execute(query, params)
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string("service_saved_success"), parent=self)
            win.destroy()
            self.load_services()
            if self.refresh_callback: self.refresh_callback()
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro", self.get_string("service_save_failed", error=e), parent=win)
        finally:
            if conn: conn.close()
    
    def delete_service(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string("selection_required_title"), self.get_string("select_service_to_delete"), parent=self)
            return
        
        values = self.tree.item(selected_item, "values")
        service_id, desc = values[0], values[2]
        
        if not messagebox.askyesno(self.get_string("confirm_delete_title"), self.get_string("confirm_delete_service_msg", desc=desc), parent=self):
            return
            
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ordem_servicos WHERE id = %s", (service_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string("service_deleted_success"), parent=self)
            self.load_services()
            if self.refresh_callback: self.refresh_callback()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", self.get_string("service_delete_failed", error=e), parent=self)
        finally:
            if conn: conn.close()