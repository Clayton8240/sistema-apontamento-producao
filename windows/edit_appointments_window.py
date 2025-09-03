# -*- coding: utf-8 -*-

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, END
from services import get_appointments_for_editing, update_appointment, delete_appointment, finish_service, ServiceError

class EditAppointmentsWindow(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Editar Apontamentos")
        self.geometry("1200x800")
        self.grab_set()

        self.appointments_data = []
        self.create_widgets()
        self.load_appointments()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        list_frame = tb.LabelFrame(main_frame, text="Apontamentos", bootstyle=PRIMARY, padding=10)
        list_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        cols = ['id', 'numero_wo', 'servico', 'operador', 'data', 'horainicio', 'horafim', 'quantidadeproduzida']
        headers = ['ID', 'Ordem', 'Serviço', 'Operador', 'Data', 'Início', 'Fim', 'Produzido']

        self.tree = tb.Treeview(list_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=100, anchor=CENTER)
        self.tree.column('servico', width=200, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        scrollbar_y = tb.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar_x = tb.Scrollbar(list_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=RIGHT, fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree.pack(fill=BOTH, expand=YES)

        edit_frame = tb.LabelFrame(main_frame, text="Editar Apontamento Selecionado", bootstyle=INFO, padding=10)
        edit_frame.pack(fill=X, pady=10)
        self.edit_fields = {}
        
        form_fields = {
            "data": "Data (dd/mm/yyyy)", "horainicio": "Hora Início (HH:MM:SS)", "horafim": "Hora Fim (HH:MM:SS)",
            "giros_rodados": "Giros Rodados", "quantidadeproduzida": "Qtd. Produzida", "perdas_producao": "Perdas",
            "ocorrencias": "Ocorrências", "impressor_id": "ID Impressor", "turno_id": "ID Turno", "motivo_perda_id": "ID Motivo Perda"
        }

        row = 0
        col = 0
        for name, text in form_fields.items():
            tb.Label(edit_frame, text=text).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            entry = tb.Entry(edit_frame, width=40)
            entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="ew")
            self.edit_fields[name] = entry
            col += 2
            if col >= 4:
                col = 0
                row += 1

        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        self.save_button = tb.Button(button_frame, text="Salvar Alterações", bootstyle=SUCCESS, state=DISABLED, command=self.save_changes)
        self.save_button.pack(side="left", padx=5)

        self.delete_button = tb.Button(button_frame, text="Deletar Apontamento", bootstyle=DANGER, state=DISABLED, command=self.delete_selected_appointment)
        self.delete_button.pack(side="left", padx=5)

        self.finish_button = tb.Button(button_frame, text="Finalizar Serviço (com residual)", bootstyle=WARNING, state=DISABLED, command=self.finish_selected_service)
        self.finish_button.pack(side="left", padx=5)

        self.refresh_button = tb.Button(button_frame, text="Atualizar Lista", bootstyle=PRIMARY, command=self.load_appointments)
        self.refresh_button.pack(side="right", padx=5)

    def load_appointments(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        try:
            self.appointments_data = get_appointments_for_editing()
            for app in self.appointments_data:
                values = (
                    app['id'], app['numero_wo'], app['servico'], app['operador'],
                    app['data'].strftime('%d/%m/%Y') if app['data'] else '',
                    app['horainicio'].strftime('%H:%M:%S') if app['horainicio'] else '',
                    app['horafim'].strftime('%H:%M:%S') if app['horafim'] else '',
                    app['quantidadeproduzida']
                )
                self.tree.insert("", "end", values=values, iid=app['id'])
        except ServiceError as e:
            messagebox.showerror("Erro de Serviço", str(e), parent=self)

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_id = int(selected_items[0])
        self.selected_appointment = next((item for item in self.appointments_data if item['id'] == selected_id), None)

        if self.selected_appointment:
            for name, widget in self.edit_fields.items():
                value = self.selected_appointment.get(name)
                widget.delete(0, END)
                if value is not None:
                    widget.insert(0, str(value))
            self.save_button.config(state="normal")
            self.delete_button.config(state="normal")
            self.finish_button.config(state="normal")

    def save_changes(self):
        if not self.selected_appointment:
            return

        updated_data = {}
        for name, widget in self.edit_fields.items():
            updated_data[name] = widget.get() or None

        try:
            update_appointment(self.selected_appointment['id'], updated_data)
            messagebox.showinfo("Sucesso", "Apontamento atualizado com sucesso!", parent=self)
            self.load_appointments()
        except ServiceError as e:
            messagebox.showerror("Erro ao Salvar", str(e), parent=self)

    def delete_selected_appointment(self):
        if not self.selected_appointment:
            return

        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja deletar este apontamento?", parent=self):
            try:
                delete_appointment(self.selected_appointment['id'])
                messagebox.showinfo("Sucesso", "Apontamento deletado com sucesso!", parent=self)
                self.load_appointments()
            except ServiceError as e:
                messagebox.showerror("Erro ao Deletar", str(e), parent=self)

    def finish_selected_service(self):
        if not self.selected_appointment:
            return

        servico_id = self.selected_appointment.get('servico_id')
        if not servico_id:
            messagebox.showerror("Erro", "Não foi possível identificar o serviço deste apontamento.", parent=self)
            return

        if messagebox.askyesno("Confirmar Finalização", f"Tem certeza que deseja finalizar o serviço ID {servico_id}? Isso impedirá novos apontamentos para ele.", parent=self):
            try:
                finish_service(servico_id)
                messagebox.showinfo("Sucesso", "Serviço finalizado com sucesso!", parent=self)
                self.load_appointments()
            except ServiceError as e:
                messagebox.showerror("Erro ao Finalizar", str(e), parent=self)
