# -*- coding: utf-8 -*-

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, END
from services import (
    get_appointments_for_editing, update_appointment, delete_appointment, 
    finish_service, ServiceError, get_all_impressores, get_all_turnos, 
    get_all_motivos_perda, create_appointment, get_stops_for_appointment,
    create_stop, update_stop, delete_stop, get_all_motivos_parada,
    get_setup_appointment_by_service_id, create_setup_appointment,
    update_setup_appointment, delete_setup_appointment,
    get_stops_for_setup_appointment, create_setup_stop, update_setup_stop, delete_setup_stop
)

class EditStopsWindow(Toplevel):
    def __init__(self, master, appointment_id):
        super().__init__(master)
        self.master = master
        self.appointment_id = appointment_id
        self.title(f"Editar Paradas do Apontamento {appointment_id}")
        self.geometry("800x600")
        self.grab_set()

        self.stops_data = []
        self.motivos_parada = {m['id']: m['descricao'] for m in get_all_motivos_parada()}
        self.motivos_parada_rev = {v: k for k, v in self.motivos_parada.items()}

        self.create_widgets()
        self.load_stops()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        list_frame = tb.LabelFrame(main_frame, text="Paradas", bootstyle=PRIMARY, padding=10)
        list_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        cols = ['id', 'horainicio', 'horafim', 'motivo']
        headers = ['ID', 'Início', 'Fim', 'Motivo']

        self.tree = tb.Treeview(list_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=150, anchor=CENTER)
        self.tree.column('motivo', anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.pack(fill=BOTH, expand=YES)

        edit_frame = tb.LabelFrame(main_frame, text="Adicionar/Editar Parada", bootstyle=INFO, padding=10)
        edit_frame.pack(fill=X, pady=10)
        self.edit_fields = {}

        form_fields = {"horainicio": "Hora Início (HH:MM:SS)", "horafim": "Hora Fim (HH:MM:SS)"}
        row, col = 0, 0
        for name, text in form_fields.items():
            tb.Label(edit_frame, text=text).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            entry = tb.Entry(edit_frame, width=30)
            entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="ew")
            self.edit_fields[name] = entry
            col += 2

        tb.Label(edit_frame, text="Motivo").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.motivo_parada_combo = tb.Combobox(edit_frame, values=list(self.motivos_parada.values()), width=30)
        self.motivo_parada_combo.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        self.save_button = tb.Button(button_frame, text="Salvar Parada", command=self.save_stop)
        self.save_button.pack(side="left", padx=5)
        self.delete_button = tb.Button(button_frame, text="Deletar Parada", bootstyle=DANGER, command=self.delete_stop, state=DISABLED)
        self.delete_button.pack(side="left", padx=5)
        self.clear_button = tb.Button(button_frame, text="Limpar", command=self.clear_form)
        self.clear_button.pack(side="left", padx=5)

    def load_stops(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            self.stops_data = get_stops_for_appointment(self.appointment_id)
            for stop in self.stops_data:
                values = (stop['id'], stop['horainicio'], stop['horafim'], stop['motivo'])
                self.tree.insert("", "end", values=values, iid=stop['id'])
        except ServiceError as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as paradas: {e}", parent=self)

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        self.selected_stop_id = int(selected_items[0])
        stop = next((s for s in self.stops_data if s['id'] == self.selected_stop_id), None)
        if stop:
            self.edit_fields['horainicio'].delete(0, END)
            self.edit_fields['horainicio'].insert(0, stop['horainicio'])
            self.edit_fields['horafim'].delete(0, END)
            self.edit_fields['horafim'].insert(0, stop['horafim'])
            self.motivo_parada_combo.set(stop['motivo'])
            self.delete_button.config(state="normal")

    def save_stop(self):
        data = {name: widget.get() for name, widget in self.edit_fields.items()}
        motivo_desc = self.motivo_parada_combo.get()
        if not all(data.values()) or not motivo_desc:
            messagebox.showwarning("Atenção", "Todos os campos são obrigatórios.", parent=self)
            return
        
        data['motivo_parada_id'] = self.motivos_parada_rev.get(motivo_desc)
        
        try:
            if hasattr(self, 'selected_stop_id') and self.selected_stop_id:
                update_stop(self.selected_stop_id, data)
                messagebox.showinfo("Sucesso", "Parada atualizada!", parent=self)
            else:
                data['apontamento_id'] = self.appointment_id
                create_stop(data)
                messagebox.showinfo("Sucesso", "Parada criada!", parent=self)
            self.load_stops()
            self.clear_form()
        except ServiceError as e:
            messagebox.showerror("Erro", f"Não foi possível salvar a parada: {e}", parent=self)

    def delete_stop(self):
        if hasattr(self, 'selected_stop_id') and self.selected_stop_id:
            if messagebox.askyesno("Confirmar", "Deseja deletar a parada selecionada?", parent=self):
                try:
                    delete_stop(self.selected_stop_id)
                    messagebox.showinfo("Sucesso", "Parada deletada!", parent=self)
                    self.load_stops()
                    self.clear_form()
                except ServiceError as e:
                    messagebox.showerror("Erro", f"Não foi possível deletar a parada: {e}", parent=self)

    def clear_form(self):
        for widget in self.edit_fields.values():
            widget.delete(0, END)
        self.motivo_parada_combo.set('')
        self.selected_stop_id = None
        self.delete_button.config(state=DISABLED)
        self.tree.selection_remove(self.tree.selection())

class EditSetupStopsWindow(Toplevel):
    def __init__(self, master, setup_id):
        super().__init__(master)
        self.master = master
        self.setup_id = setup_id
        self.title(f"Editar Paradas do Setup {setup_id}")
        self.geometry("800x600")
        self.grab_set()

        self.stops_data = []
        self.motivos_parada = {m['id']: m['descricao'] for m in get_all_motivos_parada()}
        self.motivos_parada_rev = {v: k for k, v in self.motivos_parada.items()}

        self.create_widgets()
        self.load_stops()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        list_frame = tb.LabelFrame(main_frame, text="Paradas de Setup", bootstyle=PRIMARY, padding=10)
        list_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        cols = ['id', 'horainicio', 'horafim', 'motivo']
        headers = ['ID', 'Início', 'Fim', 'Motivo']

        self.tree = tb.Treeview(list_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=150, anchor=CENTER)
        self.tree.column('motivo', anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.pack(fill=BOTH, expand=YES)

        edit_frame = tb.LabelFrame(main_frame, text="Adicionar/Editar Parada de Setup", bootstyle=INFO, padding=10)
        edit_frame.pack(fill=X, pady=10)
        self.edit_fields = {}

        form_fields = {"horainicio": "Hora Início (HH:MM:SS)", "horafim": "Hora Fim (HH:MM:SS)"}
        row, col = 0, 0
        for name, text in form_fields.items():
            tb.Label(edit_frame, text=text).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            entry = tb.Entry(edit_frame, width=30)
            entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="ew")
            self.edit_fields[name] = entry
            col += 2

        tb.Label(edit_frame, text="Motivo").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.motivo_parada_combo = tb.Combobox(edit_frame, values=list(self.motivos_parada.values()), width=30)
        self.motivo_parada_combo.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)

        self.save_button = tb.Button(button_frame, text="Salvar Parada", command=self.save_stop)
        self.save_button.pack(side="left", padx=5)
        self.delete_button = tb.Button(button_frame, text="Deletar Parada", bootstyle=DANGER, command=self.delete_stop, state=DISABLED)
        self.delete_button.pack(side="left", padx=5)
        self.clear_button = tb.Button(button_frame, text="Limpar", command=self.clear_form)
        self.clear_button.pack(side="left", padx=5)

    def load_stops(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            self.stops_data = get_stops_for_setup_appointment(self.setup_id)
            for stop in self.stops_data:
                values = (stop['id'], stop['horainicio'], stop['horafim'], stop['motivo'])
                self.tree.insert("", "end", values=values, iid=stop['id'])
        except ServiceError as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as paradas de setup: {e}", parent=self)

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        self.selected_stop_id = int(selected_items[0])
        stop = next((s for s in self.stops_data if s['id'] == self.selected_stop_id), None)
        if stop:
            self.edit_fields['horainicio'].delete(0, END)
            self.edit_fields['horainicio'].insert(0, stop['horainicio'])
            self.edit_fields['horafim'].delete(0, END)
            self.edit_fields['horafim'].insert(0, stop['horafim'])
            self.motivo_parada_combo.set(stop['motivo'])
            self.delete_button.config(state="normal")

    def save_stop(self):
        data = {name: widget.get() for name, widget in self.edit_fields.items()}
        motivo_desc = self.motivo_parada_combo.get()
        if not all(data.values()) or not motivo_desc:
            messagebox.showwarning("Atenção", "Todos os campos são obrigatórios.", parent=self)
            return
        
        data['motivo_id'] = self.motivos_parada_rev.get(motivo_desc)
        
        try:
            if hasattr(self, 'selected_stop_id') and self.selected_stop_id:
                update_setup_stop(self.selected_stop_id, data)
                messagebox.showinfo("Sucesso", "Parada de setup atualizada!", parent=self)
            else:
                data['setup_id'] = self.setup_id
                create_setup_stop(data)
                messagebox.showinfo("Sucesso", "Parada de setup criada!", parent=self)
            self.load_stops()
            self.clear_form()
        except ServiceError as e:
            messagebox.showerror("Erro", f"Não foi possível salvar a parada de setup: {e}", parent=self)

    def delete_stop(self):
        if hasattr(self, 'selected_stop_id') and self.selected_stop_id:
            if messagebox.askyesno("Confirmar", "Deseja deletar a parada de setup selecionada?", parent=self):
                try:
                    delete_setup_stop(self.selected_stop_id)
                    messagebox.showinfo("Sucesso", "Parada de setup deletada!", parent=self)
                    self.load_stops()
                    self.clear_form()
                except ServiceError as e:
                    messagebox.showerror("Erro", f"Não foi possível deletar a parada de setup: {e}", parent=self)

    def clear_form(self):
        for widget in self.edit_fields.values():
            widget.delete(0, END)
        self.motivo_parada_combo.set('')
        self.selected_stop_id = None
        self.delete_button.config(state=DISABLED)
        self.tree.selection_remove(self.tree.selection())

class EditAppointmentsWindow(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Editar e Adicionar Apontamentos")
        self.geometry("1300x950")
        self.grab_set()

        self.appointments_data = []
        self.is_new_appointment_mode = False
        self.selected_setup_appointment = None
        self.load_lookup_data()
        self.create_widgets()
        self.load_appointments()

    def load_lookup_data(self):
        try:
            self.impressores = {i['id']: i['nome'] for i in get_all_impressores()}
            self.turnos = {t['id']: t['descricao'] for t in get_all_turnos()}
            self.motivos_perda = {m['id']: m['descricao'] for m in get_all_motivos_perda()}
            self.impressores_rev = {v: k for k, v in self.impressores.items()}
            self.turnos_rev = {v: k for k, v in self.turnos.items()}
            self.motivos_perda_rev = {v: k for k, v in self.motivos_perda.items()}
        except ServiceError as e:
            messagebox.showerror("Erro de Dados", f"Não foi possível carregar dados auxiliares: {e}", parent=self)
            self.destroy()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        list_frame = tb.LabelFrame(main_frame, text="Apontamentos de Produção", bootstyle=PRIMARY, padding=10)
        list_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        cols = ['id', 'numero_wo', 'servico', 'operador', 'data', 'horainicio', 'horafim', 'quantidadeproduzida']
        headers = ['ID', 'Ordem', 'Serviço', 'Operador', 'Data', 'Início', 'Fim', 'Produzido']
        self.tree = tb.Treeview(list_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=100, anchor=CENTER)
        self.tree.column('servico', width=200, anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.pack(fill=BOTH, expand=YES)

        # --- Frame de Edição Principal ---
        self.edit_frame = tb.LabelFrame(main_frame, text="Editar/Adicionar Apontamento de Produção", bootstyle=INFO, padding=10)
        self.edit_frame.pack(fill=X, pady=10)
        self.edit_fields = {}
        self.create_main_edit_fields(self.edit_frame)

        # --- Frame de Edição de Setup ---
        self.setup_frame = tb.LabelFrame(main_frame, text="Editar/Adicionar Apontamento de Setup", bootstyle=WARNING, padding=10)
        self.setup_frame.pack(fill=X, pady=10)
        self.setup_fields = {}
        self.create_setup_edit_fields(self.setup_frame)

    def create_main_edit_fields(self, parent_frame):
        form_fields = {
            "servico_id": "ID Serviço", "data": "Data (dd/mm/yyyy)", "horainicio": "Início (HH:MM:SS)",
            "horafim": "Fim (HH:MM:SS)", "giros_rodados": "Giros Rodados", "quantidadeproduzida": "Qtd. Produzida",
            "perdas_producao": "Perdas", "ocorrencias": "Ocorrências", "impressor_id": "Impressor",
            "turno_id": "Turno", "motivo_perda_id": "Motivo Perda"
        }
        row, col = 0, 0
        for name, text in form_fields.items():
            tb.Label(parent_frame, text=text).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            if name in ["impressor_id", "turno_id", "motivo_perda_id"]:
                combo = tb.Combobox(parent_frame, width=38, values=self.get_combobox_values(name))
                combo.grid(row=row, column=col+1, padx=5, pady=5, sticky="ew")
                self.edit_fields[name] = combo
            else:
                entry = tb.Entry(parent_frame, width=40)
                entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="ew")
                self.edit_fields[name] = entry
            col += 2
            if col >= 6:
                col = 0
                row += 1
        
        button_frame = tb.Frame(parent_frame)
        button_frame.grid(row=row+1, columnspan=6, pady=10)
        self.save_button = tb.Button(button_frame, text="Salvar Alterações", bootstyle=SUCCESS, state=DISABLED, command=self.save_changes)
        self.save_button.pack(side="left", padx=5)
        self.new_button = tb.Button(button_frame, text="Novo Apontamento", bootstyle=INFO, command=self.prepare_new_appointment)
        self.new_button.pack(side="left", padx=5)
        self.delete_button = tb.Button(button_frame, text="Deletar Apontamento", bootstyle=DANGER, state=DISABLED, command=self.delete_selected_appointment)
        self.delete_button.pack(side="left", padx=5)
        self.stops_button = tb.Button(button_frame, text="Editar Paradas", bootstyle=SECONDARY, state=DISABLED, command=self.open_stops_editor)
        self.stops_button.pack(side="left", padx=5)
        self.finish_button = tb.Button(button_frame, text="Finalizar Serviço", bootstyle=WARNING, state=DISABLED, command=self.finish_selected_service)
        self.finish_button.pack(side="left", padx=5)
        self.refresh_button = tb.Button(button_frame, text="Atualizar Lista", bootstyle=PRIMARY, command=self.load_appointments)
        self.refresh_button.pack(side="right", padx=5)

    def create_setup_edit_fields(self, parent_frame):
        form_fields = {
            "data_apontamento": "Data (dd/mm/yyyy)", "hora_inicio": "Início (HH:MM:SS)", "hora_fim": "Fim (HH:MM:SS)",
            "perdas": "Perdas", "malas": "Malas", "total_lavagens": "Total Lavagens", "numero_inspecao": "Nº Inspeção"
        }
        row, col = 0, 0
        for name, text in form_fields.items():
            tb.Label(parent_frame, text=text).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            entry = tb.Entry(parent_frame, width=40)
            entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="ew")
            self.setup_fields[name] = entry
            col += 2
            if col >= 4:
                col = 0
                row += 1

        button_frame = tb.Frame(parent_frame)
        button_frame.grid(row=row+1, columnspan=4, pady=10)
        self.save_setup_button = tb.Button(button_frame, text="Salvar Setup", bootstyle=SUCCESS, state=DISABLED, command=self.save_setup_changes)
        self.save_setup_button.pack(side="left", padx=5)
        self.delete_setup_button = tb.Button(button_frame, text="Deletar Setup", bootstyle=DANGER, state=DISABLED, command=self.delete_selected_setup)
        self.delete_setup_button.pack(side="left", padx=5)
        self.setup_stops_button = tb.Button(button_frame, text="Editar Paradas de Setup", bootstyle=SECONDARY, state=DISABLED, command=self.open_setup_stops_editor)
        self.setup_stops_button.pack(side="left", padx=5)

    def get_combobox_values(self, field_name):
        if field_name == "impressor_id": return list(self.impressores.values())
        if field_name == "turno_id": return list(self.turnos.values())
        if field_name == "motivo_perda_id": return list(self.motivos_perda.values())
        return []

    def load_appointments(self):
        self.clear_form()
        self.clear_setup_form()
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            self.appointments_data = get_appointments_for_editing()
            for app in self.appointments_data:
                values = (
                    app['id'], app['numero_wo'], app['servico'], 
                    self.impressores.get(app['impressor_id'], 'N/A'),
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
        self.is_new_appointment_mode = False
        self.save_button.config(text="Salvar Alterações")

        selected_id = int(selected_items[0])
        self.selected_appointment = next((item for item in self.appointments_data if item['id'] == selected_id), None)

        if self.selected_appointment:
            # Populate main form
            for name, widget in self.edit_fields.items():
                value = self.selected_appointment.get(name)
                if isinstance(widget, tb.Combobox):
                    widget.set(self.get_lookup_value(name, value))
                else:
                    widget.delete(0, END)
                    if value is not None:
                        widget.insert(0, str(value))
            
            self.edit_fields['servico_id'].config(state=DISABLED)
            self.save_button.config(state="normal")
            self.delete_button.config(state="normal")
            self.finish_button.config(state="normal")
            self.stops_button.config(state="normal")

            # Populate setup form
            self.load_setup_appointment(self.selected_appointment['servico_id'])

    def load_setup_appointment(self, service_id):
        self.clear_setup_form()
        try:
            self.selected_setup_appointment = get_setup_appointment_by_service_id(service_id)
            if self.selected_setup_appointment:
                for name, widget in self.setup_fields.items():
                    value = self.selected_setup_appointment.get(name)
                    widget.delete(0, END)
                    if value is not None:
                        widget.insert(0, str(value))
                self.save_setup_button.config(state="normal")
                self.delete_setup_button.config(state="normal")
                self.setup_stops_button.config(state="normal")
            else:
                 self.save_setup_button.config(state="normal") # Allow creating a new one
        except ServiceError as e:
            messagebox.showerror("Erro de Setup", f"Não foi possível carregar o apontamento de setup: {e}", parent=self)

    def get_lookup_value(self, field_name, key):
        if key is None: return ""
        if field_name == 'impressor_id': return self.impressores.get(key, "")
        if field_name == 'turno_id': return self.turnos.get(key, "")
        if field_name == 'motivo_perda_id': return self.motivos_perda.get(key, "")
        return ""

    def get_lookup_id(self, field_name, value):
        if not value: return None
        if field_name == 'impressor_id': return self.impressores_rev.get(value)
        if field_name == 'turno_id': return self.turnos_rev.get(value)
        if field_name == 'motivo_perda_id': return self.motivos_perda_rev.get(value)
        return None

    def save_changes(self):
        updated_data = {}
        for name, widget in self.edit_fields.items():
            value = widget.get() or None
            if name in ["impressor_id", "turno_id", "motivo_perda_id"]:
                updated_data[name] = self.get_lookup_id(name, value)
            else:
                updated_data[name] = value

        try:
            if self.is_new_appointment_mode:
                if not updated_data.get('servico_id'):
                    messagebox.showwarning("Atenção", "O campo 'ID Serviço' é obrigatório para novos apontamentos.", parent=self)
                    return
                create_appointment(updated_data)
                messagebox.showinfo("Sucesso", "Apontamento criado com sucesso!", parent=self)
            else:
                if not self.selected_appointment:
                    return
                update_appointment(self.selected_appointment['id'], updated_data)
                messagebox.showinfo("Sucesso", "Apontamento atualizado com sucesso!", parent=self)
            
            self.load_appointments()
        except ServiceError as e:
            messagebox.showerror("Erro ao Salvar", str(e), parent=self)

    def save_setup_changes(self):
        if not self.selected_appointment:
            messagebox.showwarning("Atenção", "Selecione um apontamento de produção primeiro.", parent=self)
            return

        setup_data = {name: widget.get() or None for name, widget in self.setup_fields.items()}
        setup_data['servico_id'] = self.selected_appointment['servico_id']

        try:
            if self.selected_setup_appointment:
                update_setup_appointment(self.selected_setup_appointment['id'], setup_data)
                messagebox.showinfo("Sucesso", "Apontamento de setup atualizado!", parent=self)
            else:
                create_setup_appointment(setup_data)
                messagebox.showinfo("Sucesso", "Apontamento de setup criado!", parent=self)
            self.load_setup_appointment(setup_data['servico_id'])
        except ServiceError as e:
            messagebox.showerror("Erro ao Salvar Setup", str(e), parent=self)

    def prepare_new_appointment(self):
        self.clear_form()
        self.clear_setup_form()
        self.is_new_appointment_mode = True
        self.save_button.config(text="Criar Apontamento", state="normal")
        self.edit_frame.config(text="Novo Apontamento de Produção")
        self.edit_fields['servico_id'].config(state="normal")
        self.edit_fields['servico_id'].focus()

    def clear_form(self):
        self.tree.selection_remove(self.tree.selection())
        self.selected_appointment = None
        self.is_new_appointment_mode = False
        for widget in self.edit_fields.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            else:
                widget.delete(0, END)
        self.save_button.config(text="Salvar Alterações", state=DISABLED)
        self.delete_button.config(state=DISABLED)
        self.finish_button.config(state=DISABLED)
        self.stops_button.config(state=DISABLED)
        self.edit_frame.config(text="Editar/Adicionar Apontamento de Produção")
        self.edit_fields['servico_id'].config(state=DISABLED)

    def clear_setup_form(self):
        self.selected_setup_appointment = None
        for widget in self.setup_fields.values():
            widget.delete(0, END)
        self.save_setup_button.config(state=DISABLED)
        self.delete_setup_button.config(state=DISABLED)
        self.setup_stops_button.config(state=DISABLED)

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

    def delete_selected_setup(self):
        if not self.selected_setup_appointment:
            messagebox.showwarning("Atenção", "Nenhum apontamento de setup selecionado para deletar.", parent=self)
            return
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja deletar o apontamento de setup?", parent=self):
            try:
                delete_setup_appointment(self.selected_setup_appointment['id'])
                messagebox.showinfo("Sucesso", "Apontamento de setup deletado com sucesso!", parent=self)
                self.load_setup_appointment(self.selected_setup_appointment['servico_id'])
            except ServiceError as e:
                messagebox.showerror("Erro ao Deletar Setup", str(e), parent=self)

    def finish_selected_service(self):
        if not self.selected_appointment:
            return
        servico_id = self.selected_appointment.get('servico_id')
        if not servico_id:
            messagebox.showerror("Erro", "Não foi possível identificar o serviço deste apontamento.", parent=self)
            return
        if messagebox.askyesno("Confirmar Finalização", f"Tem certeza que deseja finalizar o serviço ID {servico_id}?", parent=self):
            try:
                finish_service(servico_id)
                messagebox.showinfo("Sucesso", "Serviço finalizado com sucesso!", parent=self)
                self.load_appointments()
            except ServiceError as e:
                messagebox.showerror("Erro ao Finalizar", str(e), parent=self)

    def open_stops_editor(self):
        if not self.selected_appointment:
            messagebox.showwarning("Atenção", "Selecione um apontamento para editar suas paradas.", parent=self)
            return
        EditStopsWindow(self, self.selected_appointment['id'])

    def open_setup_stops_editor(self):
        if not self.selected_setup_appointment:
            messagebox.showwarning("Atenção", "Selecione um apontamento de setup para editar suas paradas.", parent=self)
            return
        EditSetupStopsWindow(self, self.selected_setup_appointment['id'])
