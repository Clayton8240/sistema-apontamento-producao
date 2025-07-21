# -*- coding: utf-8 -*-
from PIL import Image, ImageTk
from tkinter import PhotoImage
import base64
import openpyxl
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import messagebox, Toplevel, END, W, E, S, N, CENTER, filedialog, simpledialog, Listbox
import psycopg2
from datetime import datetime, time, date, timedelta
import json
import os
import csv
import bcrypt

class ViewAppointmentsWindow(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.title(self.get_string("view_appointments_title"))
        self.geometry("1200x700")
        self.grab_set()

        self.create_widgets()
        self.load_appointments()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        filter_frame = tb.LabelFrame(main_frame, text=self.get_string("filter_section"), bootstyle=PRIMARY, padding=10)
        filter_frame.pack(fill=X, pady=5)
        
        tb.Label(filter_frame, text=self.get_string("date_start_label")).pack(side=LEFT, padx=(0, 5))
        self.date_start_entry = DateEntry(filter_frame, bootstyle=INFO, dateformat='%d/%m/%Y')
        self.date_start_entry.pack(side=LEFT, padx=5)
        
        tb.Label(filter_frame, text=self.get_string("date_end_label")).pack(side=LEFT, padx=(10, 5))
        self.date_end_entry = DateEntry(filter_frame, bootstyle=INFO, dateformat='%d/%m/%Y')
        self.date_end_entry.pack(side=LEFT, padx=5)

        tb.Button(filter_frame, text=self.get_string("apply_filters_btn"), command=self.load_appointments, bootstyle=SUCCESS).pack(side=LEFT, padx=10)
        tb.Button(filter_frame, text=self.get_string("clear_filters_btn"), command=self.clear_filters, bootstyle=WARNING).pack(side=LEFT)

        action_frame = tb.Frame(main_frame)
        action_frame.pack(fill=X, pady=5)
        tb.Button(action_frame, text=self.get_string("edit_appointment_btn"), command=self.edit_appointment, bootstyle="info-outline").pack(side=LEFT, padx=5)
        tb.Button(action_frame, text=self.get_string("delete_appointment_btn"), command=self.delete_appointment, bootstyle="danger-outline").pack(side=LEFT, padx=5)
        tb.Button(action_frame, text=self.get_string("view_stop_details_btn"), command=self.view_stops, bootstyle="secondary-outline").pack(side=LEFT, padx=5)
        tb.Button(action_frame, text=self.get_string("export_csv_btn"), command=self.export_to_csv, bootstyle="success-outline").pack(side=RIGHT, padx=5)

        tree_frame = tb.Frame(main_frame)
        tree_frame.pack(fill=BOTH, expand=True)

        self.cols = ("id", "data", "horainicio", "horafim", "wo", "equipamento", "impressor", "quantidadeproduzida")
        self.headers = [self.get_string(f'col_{c}') for c in self.cols]
        self.tree = tb.Treeview(tree_frame, columns=self.cols, show="headings", bootstyle=PRIMARY)
        
        for col, header in zip(self.cols, self.headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor=CENTER, width=120)
        
        self.tree.column("id", width=50)

        v_scroll = tb.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        h_scroll = tb.Scrollbar(main_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scroll.pack(side=RIGHT, fill=Y)
        h_scroll.pack(side=BOTTOM, fill=X)

    def load_appointments(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = self.get_db_connection()
        if not conn: return
        
        try:
            with conn.cursor() as cur:
                query = f"SELECT {', '.join(self.cols)} FROM {self.db_config['tabela']}"
                filters = []
                params = []
                
                start_date_str = self.date_start_entry.entry.get()
                end_date_str = self.date_end_entry.entry.get()

                if start_date_str:
                    filters.append("data >= %s")
                    params.append(datetime.strptime(start_date_str, '%d/%m/%Y').date())
                if end_date_str:
                    filters.append("data <= %s")
                    params.append(datetime.strptime(end_date_str, '%d/%m/%Y').date())

                if filters:
                    query += " WHERE " + " AND ".join(filters)
                
                query += " ORDER BY data DESC, horainicio DESC"
                
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    self.tree.insert("", END, values=row)

        except (psycopg2.Error, ValueError) as e:
            messagebox.showerror("Erro", self.get_string("db_load_appointments_failed", table_name=self.db_config['tabela'], error=e), parent=self)
        finally:
            if conn: conn.close()

    def clear_filters(self):
        self.date_start_entry.entry.delete(0, END)
        self.date_end_entry.entry.delete(0, END)
        self.load_appointments()

    def edit_appointment(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string("selection_required_title"), self.get_string("select_appointment_to_edit"), parent=self)
            return
        item_values = self.tree.item(selected_item, "values")
        appointment_id = item_values[0]
        messagebox.showinfo("Em Desenvolvimento", f"A função para editar o apontamento ID {appointment_id} ainda não foi implementada.", parent=self)

    def delete_appointment(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string("selection_required_title"), self.get_string("select_appointment_to_delete"), parent=self)
            return

        item_values = self.tree.item(selected_item, "values")
        app_id = item_values[0]

        if not messagebox.askyesno(self.get_string("confirm_delete_appointment_title"), self.get_string("confirm_delete_appointment_msg", id=app_id), parent=self):
            return

        conn = self.get_db_connection()
        if not conn: return

        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM paradas WHERE apontamento_id = %s", (app_id,))
                cur.execute(f"DELETE FROM {self.db_config['tabela']} WHERE id = %s", (app_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string("delete_appointment_success", id=app_id), parent=self)
            self.load_appointments()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", self.get_string("delete_appointment_failed", error=e), parent=self)
        finally:
            if conn: conn.close()
            
    def view_stops(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string("selection_required_title"), self.get_string("select_appointment_to_view_stops"), parent=self)
            return

        item_values = self.tree.item(selected_item, "values")
        app_id = item_values[0]

        stops_win = Toplevel(self)
        stops_win.title(self.get_string("stop_details_for_appointment", id=app_id))
        stops_win.geometry("600x400")
        stops_win.grab_set()

        cols = ("motivo", "inicio", "fim")
        headers = (self.get_string("col_motivos_parada"), self.get_string("col_horainicio"), self.get_string("col_horafim"))
        tree = tb.Treeview(stops_win, columns=cols, show="headings", bootstyle=INFO)
        for col, header in zip(cols, headers):
            tree.heading(col, text=header)
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT mt.descricao, p.hora_inicio_parada, p.hora_fim_parada
                    FROM paradas p
                    JOIN motivos_parada_tipos mt ON p.motivo_id = mt.id
                    WHERE p.apontamento_id = %s
                """
                cur.execute(query, (app_id,))
                rows = cur.fetchall()
                if not rows:
                    messagebox.showinfo(self.get_string("no_stops_for_appointment"), self.get_string("no_stops_for_appointment_full"), parent=stops_win)
                    stops_win.destroy()
                    return

                for row in rows:
                    tree.insert("", END, values=row)

        except psycopg2.Error as e:
            messagebox.showerror("Erro", self.get_string("db_load_stops_failed", error=e), parent=stops_win)
        finally:
            if conn: conn.close()

    def export_to_csv(self):
        if not self.tree.get_children():
            messagebox.showinfo("Exportar", self.get_string("no_data_to_export"), parent=self)
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[(self.get_string("csv_files_type"), "*.csv"), (self.get_string("all_files_type"), "*.*")],
            title=self.get_string("save_csv_dialog_title")
        )

        if not filepath: return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)
                for item_id in self.tree.get_children():
                    row = self.tree.item(item_id, 'values')
                    writer.writerow(row)
            messagebox.showinfo("Sucesso", self.get_string("export_success_message", path=filepath), parent=self)
        except Exception as e:
            messagebox.showerror("Erro", self.get_string("export_error", error=e), parent=self)
