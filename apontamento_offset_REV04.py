# Versão Final com Todas as Correções de Estrutura e Lógica

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import messagebox, Toplevel, END, W, E, S, N, CENTER, filedialog
import psycopg2
from datetime import datetime, time, date, timedelta
import json
import os
import csv

# ==============================================================================
# 1. I18N STRINGS (Traduções)
# ==============================================================================
LANGUAGES = {
    'portugues': {
        'app_title': 'Sistema de Apontamento de Produção',
        'main_menu_title': 'Menu Principal - Sistema de Produção',
        'btn_production_entry': 'Apontamento de Produção',
        'btn_pcp_management': 'Gerenciamento PCP',
        'btn_view_entries': 'Visualizar Apontamentos',
        'btn_manage_tables': 'Gerenciar Tabelas de Apoio',
        'start_production_btn': 'Iniciar Produção',
        'finish_production_btn': 'Finalizar Produção',
        'register_entry_btn': 'Registar Apontamento Final',
        'production_status_running': 'EM PRODUÇÃO',
        'production_status_stopped': 'PARADO',
        'production_status_idle': 'AGUARDANDO INÍCIO',
        'elapsed_time_label': 'Tempo Decorrido:',
        'stop_tracking_window_title': 'Apontamento de Parada em Tempo Real',
        'stop_reason_label': 'Motivo da Parada:',
        'finish_stop_btn': 'Finalizar Parada',
        'stop_time_label': 'Tempo de Parada:',
        'menu_settings': 'Configurações',
        'menu_db_config': 'Configurar Banco de Dados',
        'menu_manage': 'Gerenciar',
        'menu_manage_lookup': 'Gerenciar Tabelas de Apoio',
        'menu_view_appointments': 'Visualizar Apontamentos',
        'menu_manage_pcp': 'Gerenciar Ordens (PCP)',
        'config_win_title': 'Configurações do Banco de Dados',
        'host_label': 'Host',
        'port_label': 'Porta',
        'user_label': 'Usuário',
        'password_label': 'Senha',
        'db_label': 'Banco',
        'table_label': 'Tabela de Apontamentos',
        'language_label': 'Idioma',
        'test_connection_btn': 'Testar Conexão',
        'save_btn': 'Salvar',
        'cancel_btn': 'Cancelar',
        'form_data_section': 'Dados',
        'save_changes_btn': 'Salvar Alterações',
        'edit_order_btn': 'Alterar Ordem Selecionada',
        'cancel_order_btn': 'Cancelar Ordem Selecionada',
        'edit_order_title': 'Editar Ordem de Produção - WO: {wo}',
        'confirm_cancel_order_title': 'Confirmar Cancelamento',
        'confirm_cancel_order_msg': 'Tem certeza que deseja cancelar permanentemente a ordem com WO "{wo}"? Esta ação não pode ser desfeita.',
        'cancel_order_success': 'Ordem de Produção cancelada com sucesso!',
        'cancel_order_failed': 'Falha ao cancelar a Ordem de Produção: {error}',
        'update_order_success': 'Ordem de Produção atualizada com sucesso!',
        'update_order_failed': 'Falha ao atualizar a Ordem de Produção: {error}',
        'selection_required_title': 'Seleção Necessária',
        'select_order_to_edit_msg': 'Por favor, selecione uma ordem para alterar.',
        'select_order_to_cancel_msg': 'Por favor, selecione uma ordem para cancelar.',
        'invalid_status_for_action_msg': 'Ação não permitida! Apenas ordens com status "Em Aberto" podem ser alteradas ou canceladas.',
        'col_id': 'ID', 'col_descricao': 'Descrição', 'col_nome': 'Nome', 'col_codigo': 'Código',
        'col_valor': 'Valor', 'col_data': 'Data', 'col_horainicio': 'Hora Início', 'col_horafim': 'Hora Fim',
        'equipment_label': 'Equipamento', 'col_wo': 'WO', 'col_cliente': 'Cliente', 'col_qtde_cores': 'QTDE CORES',
        'col_tipo_papel': 'TIPO PAPEL', 'col_numeroinspecao': 'Número Inspeção', 'col_gramatura': 'Gramatura',
        'col_formato': 'Formato', 'col_fsc': 'FSC', 'col_tiragem_em_folhas': 'Tiragem em Folhas',
        'col_giros_rodados': 'Giros Rodados', 'col_perdas_malas': 'Perdas/ Malas', 'col_total_lavagens': 'Total Lavagens',
        'col_total_acertos': 'Total Acertos', 'printer_label': 'Impressor', 'col_ocorrencias': 'Ocorrências',
        'col_motivos_parada': 'Motivo da Parada', 'shift_label': 'Turno', 'col_quantidadeproduzida': 'Quantidade Produzida',
        'filter_section': 'Filtros de Apontamentos', 'date_start_label': 'Data Início', 'date_end_label': 'Data Fim',
        'apply_filters_btn': 'Aplicar Filtros', 'clear_filters_btn': 'Limpar Filtros', 'export_csv_btn': 'Exportar para CSV',
        'no_data_to_export': 'Não há dados para exportar.', 'csv_files_type': 'Arquivos CSV', 'all_files_type': 'Todos os Arquivos',
        'save_csv_dialog_title': 'Salvar como CSV', 'export_success_message': 'Dados exportados com sucesso para:\n{path}',
        'export_error': 'Erro ao exportar dados para CSV: {error}', 'view_appointments_title': 'Visualizar Apontamentos',
        'loaded_appointments_success': 'Dados da tabela "{table_name}" carregados com sucesso!', 'db_load_appointments_failed': 'Falha ao carregar apontamentos da tabela "{table_name}": {error}',
        'has_stops_question': 'Possui Paradas?', 'open_stop_times_btn': 'Configurar Paradas', 'stop_times_window_title': 'Apontamento de Paradas',
        'num_stops_label': 'Número de Paradas', 'generate_fields_btn': 'Gerar Campos', 'stop_label': 'Parada',
        'stop_times_control_section': 'Controle de Paradas', 'stop_times_saved_success': 'Dados de paradas salvos com sucesso!',
        'invalid_num_stops_error': 'Por favor, insira um número válido para a quantidade de paradas.', 'validation_error_invalid_selection': 'Por favor, selecione um item válido.',
        'validation_error_time_order': 'Hora Fim deve ser posterior à Hora Início.', 'validation_error_fix_fields_stops': 'Por favor, corrija os campos de parada destacados em vermelho.',
        'other_motives_label': 'Especifique o Motivo', 'has_stops_question_short': 'Paradas?', 'yes_short': 'Sim', 'no_short': 'Não',
        'view_stop_details_btn': 'Ver Detalhes das Paradas', 'select_appointment_to_view_stops': 'Por favor, selecione um apontamento para ver os detalhes das paradas.',
        'no_stops_for_appointment': 'Este apontamento não possui paradas registradas.', 'no_stops_for_appointment_full': 'Nenhuma parada registrada para este apontamento.',
        'stop_details_for_appointment': 'Detalhes das Paradas para Apontamento ID: {id}', 'db_load_stops_failed': 'Falha ao carregar detalhes das paradas: {error}',
        'db_conn_incomplete': 'Configuração do banco de dados incompleta ou ausente.', 'invalid_input': 'Entrada Inválida',
        'filter_date_format_warning': 'Formato de data inválido para o campo "{field}". Use DD/MM/AAAA.', 'edit_appointment_btn': 'Editar Apontamento',
        'delete_appointment_btn': 'Excluir Apontamento', 'confirm_delete_appointment_title': 'Confirmar Exclusão de Apontamento',
        'confirm_delete_appointment_msg': 'Tem certeza que deseja excluir permanentemente o apontamento com ID {id}? Todas as paradas associadas também serão excluídas. Esta ação não pode ser desfeita.',
        'delete_appointment_success': 'Apontamento ID {id} excluído com sucesso!', 'delete_appointment_failed': 'Falha ao excluir apontamento: {error}',
        'select_appointment_to_edit': 'Selecione um apontamento para editar.', 'select_appointment_to_delete': 'Selecione um apontamento para excluir.',
        'edit_appointment_title': 'Editar Apontamento - ID: {id}', 'update_success': 'Apontamento ID {id} atualizado com sucesso!',
        'update_failed': 'Falha ao atualizar o apontamento: {error}',
    },
}

# ==============================================================================
# 2. FUNÇÕES E CLASSES DE DEPENDÊNCIA (DEFINIDAS PRIMEIRO)
# ==============================================================================

def get_connection_params(config_dict):
    return {
        'host': config_dict.get('host'),
        'port': config_dict.get('porta'),
        'dbname': config_dict.get('banco'),
        'user': config_dict.get('usuário'),
        'password': config_dict.get('senha')
    }

class LookupTableManagerWindow(Toplevel):
    lookup_table_schemas = {
        "equipamentos_tipos": {"display_name_key": "equipment_label", "table": "equipamentos_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "qtde_cores_tipos": {"display_name_key": "col_qtde_cores", "table": "qtde_cores_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "tipos_papel": {"display_name_key": "col_tipo_papel", "table": "tipos_papel", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "impressores": {"display_name_key": "printer_label", "table": "impressores", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "nome": {"type": "str", "db_column": "nome", "display_key": "col_nome", "editable": True}}},
        "motivos_parada_tipos": {"display_name_key": "col_motivos_parada", "table": "motivos_parada_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "codigo": {"type": "int", "db_column": "codigo", "display_key": "col_codigo", "editable": True}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "formatos_tipos": {"display_name_key": "col_formato", "table": "formatos_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "gramaturas_tipos": {"display_name_key": "col_gramatura", "table": "gramaturas_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "valor": {"type": "int", "db_column": "valor", "display_key": "col_valor", "editable": True}}},
        "fsc_tipos": {"display_name_key": "col_fsc", "table": "fsc_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "turnos_tipos": {"display_name_key": "shift_label", "table": "turnos_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
    }
    def __init__(self, master, db_config, refresh_main_comboboxes_callback=None):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.refresh_main_comboboxes_callback = refresh_main_comboboxes_callback
        self.current_table = None
        self.current_table_display_name = None
        self.create_manager_ui()
        self.update_idletasks()
        window_width = 800
        window_height = 600
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (window_width // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.set_localized_title()
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
        table_display_names_translated = [self.get_string(schema["display_name_key"]) for schema in self.lookup_table_schemas.values()]
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
            for i, col_name in enumerate(schema["columns"].keys()): current_values[col_name] = raw_values[i]
        add_edit_win = Toplevel(self)
        add_edit_win.title(f"{self.get_string('edit_selected_btn') if edit_mode else self.get_string('add_new_btn')} {self.get_string(schema['display_name_key'])}")
        add_edit_win.transient(self)
        add_edit_win.grab_set()
        form_entries = {}
        for i, (col_name, col_data) in enumerate(schema["columns"].items()):
            if (not col_data["editable"] and edit_mode) or (col_name == schema["pk_column"] and not edit_mode): continue
            tb.Label(add_edit_win, text=f"{self.get_string(col_data['display_key'])}:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = tb.Entry(add_edit_win)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            form_entries[col_name] = entry
            if edit_mode and col_name in current_values: entry.insert(0, current_values[col_name])
            if col_name == schema["pk_column"]: entry.config(state="readonly")
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
            for col, widget in entries.items():
                val = widget.get().strip()
                data[col] = int(val) if schema["columns"][col]["type"] == "int" and val else (val or None)
        except ValueError:
            messagebox.showerror(self.get_string('save_btn'), self.get_string('save_entry_validation_error', field_name=self.get_string(schema['columns'][next(iter(entries))]['display_key'])), parent=window)
            return
        try:
            with conn.cursor() as cur:
                if edit_mode:
                    clauses = [f'"{c["db_column"]}" = %s' for n, c in schema['columns'].items() if c['editable']]
                    values = [data[n] for n, c in schema['columns'].items() if c['editable']] + [pk_value]
                    query = f"UPDATE {schema['table']} SET {', '.join(clauses)} WHERE \"{schema['pk_column']}\" = %s"
                else:
                    cols = [f'"{c["db_column"]}"' for n, c in schema['columns'].items() if c['editable']]
                    values = [data[n] for n, c in schema['columns'].items() if c['editable']]
                    query = f"INSERT INTO {schema['table']} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(values))})"
                cur.execute(query, values)
            conn.commit()
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('entry_edited_success' if edit_mode else 'new_entry_added_success'), parent=window)
            window.destroy()
            self.load_table_data(self.current_table)
            if self.refresh_main_comboboxes_callback: self.refresh_main_comboboxes_callback()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror(self.get_string('db_save_failed'), self.get_string('db_save_failed', error=e, details=e.pgerror), parent=window)
        finally:
            if conn: conn.close()

    def delete_selected_entry(self):
        item = self.treeview.focus()
        if not item:
            messagebox.showwarning(self.get_string('delete_selected_btn'), self.get_string('select_entry_to_delete'), parent=self)
            return
        schema = self.lookup_table_schemas[self.current_table]
        pk_val = self.treeview.item(item, 'values')[list(schema["columns"].keys()).index(schema["pk_column"])]
        if not messagebox.askyesno(self.get_string('confirm_delete_title'), self.get_string('confirm_delete_message', pk_value=pk_val, display_name=self.get_string(schema['display_name_key'])), parent=self):
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
            messagebox.showerror(self.get_string('delete_selected_btn'), self.get_string('db_delete_failed', error=e, details=e.pgerror), parent=self)
        finally:
            if conn: conn.close()


class RealTimeStopWindow(Toplevel):
    def __init__(self, master, db_config, stop_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.stop_callback = stop_callback

        self.title(self.master.get_string('stop_tracking_window_title'))
        self.geometry("500x250")
        self.transient(master)
        self.grab_set()

        self.start_time = datetime.now()
        self.motivos_parada_options = []
        self.timer_job = None

        self.create_widgets()
        self.load_motivos_parada()
        self.update_timer()
    
    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(main_frame, text=self.get_string('stop_reason_label'), font=("Helvetica", 10)).pack(pady=(0, 5))
        self.motivo_combobox = tb.Combobox(main_frame, state="readonly")
        self.motivo_combobox.pack(fill=X, pady=(0, 20))
        self.motivo_combobox.bind("<<ComboboxSelected>>", self.on_reason_selected)

        tb.Label(main_frame, text=self.get_string('stop_time_label'), font=("Helvetica", 10)).pack(pady=(10, 5))
        self.timer_label = tb.Label(main_frame, text="00:00:00", font=("Helvetica", 20, "bold"), bootstyle=DANGER)
        self.timer_label.pack()

        self.finish_button = tb.Button(main_frame, text=self.get_string('finish_stop_btn'), bootstyle="danger", state=DISABLED, command=self.finish_stop)
        self.finish_button.pack(pady=20, ipadx=10, ipady=5)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def load_motivos_parada(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                schema = LookupTableManagerWindow.lookup_table_schemas["motivos_parada_tipos"]
                query = f'SELECT "{schema["columns"]["descricao"]["db_column"]}", "{schema["pk_column"]}" FROM {schema["table"]} ORDER BY "{schema["columns"]["descricao"]["db_column"]}"'
                cur.execute(query)
                self.motivos_parada_options = cur.fetchall()
                self.motivo_combobox['values'] = [opt[0] for opt in self.motivos_parada_options]
        except psycopg2.Error as e:
            messagebox.showwarning("Erro", f"Falha ao carregar motivos de parada: {e}", parent=self)
        finally:
            if conn: conn.close()

    def on_reason_selected(self, event=None):
        if self.motivo_combobox.get():
            self.finish_button.config(state=NORMAL)

    def update_timer(self):
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
        self.timer_job = self.after(1000, self.update_timer)

    def finish_stop(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
        
        end_time = datetime.now()
        selected_motivo_text = self.motivo_combobox.get()
        motivo_id = next((opt[1] for opt in self.motivos_parada_options if opt[0] == selected_motivo_text), None)

        stop_data = {
            "motivo_text": selected_motivo_text,
            "motivo_id": motivo_id,
            "hora_inicio_parada": self.start_time.time(),
            "hora_fim_parada": end_time.time(),
            "motivo_extra_detail": None
        }
        
        self.stop_callback(stop_data)
        self.destroy()    


# ==============================================================================
# 3. CLASSES DE GERENCIAMENTO PCP (EDITAR E PRINCIPAL) - ORDEM CORRIGIDA
# ==============================================================================

class EditOrdemWindow(Toplevel):
    def __init__(self, master, db_config, ordem_id, refresh_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.ordem_id = ordem_id
        self.refresh_callback = refresh_callback
        
        self.fields_config = self.master.fields_config
        self.widgets = {}

        self.create_widgets()
        self.load_ordem_data()
        
        self.transient(master)
        self.grab_set()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        
        form_frame = tb.LabelFrame(main_frame, text=self.get_string('form_data_section'), bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor=N)

        row = 0
        for key, config in self.fields_config.items():
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=row, column=0, padx=5, pady=5, sticky=W)
            if config["widget"] == "Combobox":
                widget = tb.Combobox(form_frame, state="readonly", values=self.master.widgets[key]['values'])
            else:
                widget = tb.Entry(form_frame)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget
            row += 1
        
        form_frame.grid_columnconfigure(1, weight=1)

        btn_frame = tb.Frame(form_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        tb.Button(btn_frame, text=self.get_string('save_changes_btn'), command=self.save_changes, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text=self.get_string('cancel_btn'), command=self.destroy, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

    def load_ordem_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cols = ", ".join([f'"{key}"' for key in self.fields_config.keys()])
                cur.execute(f"SELECT {cols} FROM ordem_producao WHERE id = %s", (self.ordem_id,))
                data = cur.fetchone()
                if data:
                    data_dict = dict(zip(self.fields_config.keys(), data))
                    self.title(self.get_string('edit_order_title', wo=data_dict.get('numero_wo', '')))
                    for key, widget in self.widgets.items():
                        value = data_dict.get(key)
                        if value is not None:
                            if isinstance(widget, tb.Combobox):
                                widget.set(str(value))
                            else:
                                widget.delete(0, END)
                                widget.insert(0, str(value))
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar dados da ordem: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def save_changes(self):
        data = {key: widget.get().strip() for key, widget in self.widgets.items()}
        if not data["numero_wo"]:
            messagebox.showwarning("Campo Obrigatório", "O número da WO é obrigatório.", parent=self)
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                set_clauses = [f'"{col}" = %s' for col in data.keys()]
                values = list(data.values()) + [self.ordem_id]
                query = f"UPDATE ordem_producao SET {', '.join(set_clauses)} WHERE id = %s"
                cur.execute(query, values)
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('update_order_success'), parent=self)
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Salvar", self.get_string('update_order_failed', error=e), parent=self)
        finally:
            if conn: conn.close()

class PCPWindow(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.title("Gerenciamento de Ordens de Produção (PCP)")
        self.geometry("800x600")
        self.grab_set()
        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"},
            "equipamento": {"label_key": "equipment_label", "widget": "Combobox", "lookup": "equipamentos_tipos"},
            "qtde_cores": {"label_key": "col_qtde_cores", "widget": "Combobox", "lookup": "qtde_cores_tipos"},
            "tipo_papel": {"label_key": "col_tipo_papel", "widget": "Combobox", "lookup": "tipos_papel"},
            "gramatura": {"label_key": "col_gramatura", "widget": "Combobox", "lookup": "gramaturas_tipos"},
            "formato": {"label_key": "col_formato", "widget": "Combobox", "lookup": "formatos_tipos"},
            "fsc": {"label_key": "col_fsc", "widget": "Combobox", "lookup": "fsc_tipos"},
            "numero_inspecao": {"label_key": "col_numeroinspecao", "widget": "Entry"},
        }
        self.widgets = {}
        self.create_widgets()
        self.load_combobox_data()
        self.load_ordens()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        form_frame = tb.LabelFrame(main_frame, text="Nova Ordem de Produção", bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor=N)

        row = 0
        for key, config in self.fields_config.items():
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=row, column=0, padx=5, pady=5, sticky=W)
            if config["widget"] == "Combobox":
                widget = tb.Combobox(form_frame, state="readonly")
            else:
                widget = tb.Entry(form_frame)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget
            row += 1

        form_frame.grid_columnconfigure(1, weight=1)

        btn_frame = tb.Frame(form_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        tb.Button(btn_frame, text="Salvar Nova Ordem", command=self.save_new_ordem, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Limpar Campos", command=self.clear_fields, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

        tree_container = tb.Frame(main_frame)
        tree_container.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        action_frame = tb.Frame(tree_container)
        action_frame.pack(fill=X, pady=5)
        
        self.edit_button = tb.Button(action_frame, text=self.get_string('edit_order_btn'), command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
        self.edit_button.pack(side=LEFT, padx=5)
        
        self.cancel_button = tb.Button(action_frame, text=self.get_string('cancel_order_btn'), command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
        self.cancel_button.pack(side=LEFT, padx=5)

        tree_frame = tb.LabelFrame(tree_container, text="Ordens de Produção Criadas", bootstyle=INFO, padding=10)
        tree_frame.pack(fill=BOTH, expand=True)
        
        cols = ("id", "wo", "cliente", "equipamento", "status")
        headers = ("ID", "Nº WO", "Cliente", "Equipamento", "Status")
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=100, anchor=W if col != "id" else CENTER)
        self.tree.column("id", width=50, anchor=CENTER)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = tb.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def on_tree_select(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)
            return
        
        item_values = self.tree.item(selected_item, 'values')
        status = item_values[-1] if item_values else ""

        if status == 'Em Aberto':
            self.edit_button.config(state=NORMAL)
            self.cancel_button.config(state=NORMAL)
        else:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)

    def open_edit_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[0]
        status = item_values[-1]
        if status != 'Em Aberto':
            messagebox.showwarning("Ação Inválida", self.get_string('invalid_status_for_action_msg'), parent=self)
            return
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_ordens)

    def cancel_ordem(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_cancel_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_num, status = item_values[0], item_values[1], item_values[-1]
        if status != 'Em Aberto':
            messagebox.showwarning("Ação Inválida", self.get_string('invalid_status_for_action_msg'), parent=self)
            return
        if not messagebox.askyesno(self.get_string('confirm_cancel_order_title'), self.get_string('confirm_cancel_order_msg', wo=wo_num), parent=self):
            return
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ordem_producao WHERE id = %s", (ordem_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('cancel_order_success'), parent=self)
            self.load_ordens()
        except psycopg2.Error as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", self.get_string('cancel_order_failed', error=e), parent=self)
        finally:
            if conn: conn.close()
            
    def load_ordens(self):
        self.edit_button.config(state=DISABLED)
        self.cancel_button.config(state=DISABLED)
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, numero_wo, cliente, equipamento, status FROM ordem_producao ORDER BY data_criacao DESC")
                for row in cur.fetchall():
                    self.tree.insert("", END, values=row)
        except psycopg2.Error as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar ordens de produção: {e}", parent=self)
        finally:
            if conn: conn.close()

    def load_combobox_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                schemas = LookupTableManagerWindow.lookup_table_schemas
                for key, widget in self.widgets.items():
                    if isinstance(widget, tb.Combobox):
                        field_config = self.fields_config.get(key, {})
                        lookup_ref = field_config.get("lookup")
                        if lookup_ref and lookup_ref in schemas:
                            schema_info = schemas[lookup_ref]
                            display_col_info = next((v for v in schema_info['columns'].values() if v['editable']), None)
                            if display_col_info:
                                db_col = display_col_info['db_column']
                                cur.execute(f'SELECT DISTINCT "{db_col}" FROM {schema_info["table"]} ORDER BY "{db_col}"')
                                values = [str(row[0]) for row in cur.fetchall()]
                                widget['values'] = values
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados para os comboboxes: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def save_new_ordem(self):
        data = {key: widget.get().strip() for key, widget in self.widgets.items()}
        if not data["numero_wo"]:
            messagebox.showwarning("Campo Obrigatório", "O número da WO é obrigatório.", parent=self)
            return
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cols_to_save = ['numero_wo', 'cliente', 'equipamento', 'qtde_cores', 'tipo_papel', 'gramatura', 'formato', 'fsc', 'numero_inspecao']
                non_empty_data = {col: data[col] for col in cols_to_save if data[col]}
                if not non_empty_data:
                    messagebox.showwarning("Dados Vazios", "Nenhum dado para salvar.", parent=self)
                    return
                if 'gramatura' in non_empty_data:
                    non_empty_data['gramatura'] = int(non_empty_data['gramatura'])
                cols = non_empty_data.keys()
                query = f"""
                    INSERT INTO ordem_producao ({', '.join(cols)}, status)
                    VALUES ({', '.join([f"%({c})s" for c in cols])}, 'Em Aberto')
                """
                cur.execute(query, non_empty_data)
            conn.commit()
            messagebox.showinfo("Sucesso", "Ordem de produção salva com sucesso!", parent=self)
            self.clear_fields()
            self.load_ordens()
            if 'production' in self.master.open_windows and self.master.open_windows['production'].winfo_exists():
                self.master.open_windows['production'].load_open_wos()
        except psycopg2.IntegrityError:
            conn.rollback()
            messagebox.showerror("Erro de Integridade", f"A WO '{data['numero_wo']}' já existe.", parent=self)
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar a ordem.\nVerifique se os dados estão corretos.\nDetalhes: {e}", parent=self)
        finally:
            if conn: conn.close()

    def clear_fields(self):
        for widget in self.widgets.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            else:
                widget.delete(0, END)

# ==============================================================================
# 5. CLASSE PRINCIPAL DE APONTAMENTO (App)
# ==============================================================================
class App(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')
        self.grab_set()
        self.set_localized_title()
        self.geometry("1100x750")
        self.start_time = None
        self.end_time = None
        self.timer_job = None
        self.is_running = False
        self.stop_times_data = []
        self.selected_ordem_id = None
        self.open_wos_data = {}
        self.final_entry_fields_config = {
            "Tiragem em folhas": {"db_column": "tiragem_em_folhas", "widget_type": "Entry", "validation_type": "int", "display_key": "col_tiragem_em_folhas"},
            "Giros Rodados": {"db_column": "giros_rodados", "widget_type": "Entry", "validation_type": "int", "display_key": "col_giros_rodados"},
            "Perdas/ Malas": {"db_column": "perdas_malas", "widget_type": "Entry", "validation_type": "int", "display_key": "col_perdas_malas"},
            "Total Lavagens": {"db_column": "total_lavagens", "widget_type": "Entry", "validation_type": "int", "display_key": "col_total_lavagens"},
            "Total Acertos": {"db_column": "total_acertos", "widget_type": "Entry", "validation_type": "int", "display_key": "col_total_acertos"},
            "Quantidade Produzida": {"db_column": "quantidadeproduzida", "widget_type": "Entry", "validation_type": "int", "display_key": "col_quantidadeproduzida"},
            "Ocorrências": {"db_column": "ocorrencias", "widget_type": "Text", "height": 4, "width": 50, "display_key": "col_ocorrencias"},
        }
        self.initial_selection_fields_config = {
             "Impressor": {"db_column": "impressor", "widget_type": "Combobox", "values": [], "display_key": "printer_label", "lookup_table_ref": "impressores"},
             "Turno": {"db_column": "turno", "widget_type": "Combobox", "values": [], "display_key": "shift_label", "lookup_table_ref": "turnos_tipos"},
        }
        self.fields = {}
        self.validation_labels = {}
        self.create_menu()
        self.create_form()
        self.load_initial_data()
        self.update_ui_state()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def set_localized_title(self):
        self.title(self.get_string('btn_production_entry'))
    
    def create_menu(self):
        self.menubar = tb.Menu(self)
        manage_menu = tb.Menu(self.menubar, tearoff=0)
        manage_menu.add_command(label=self.get_string('menu_manage_pcp'), command=lambda: self.master.open_pcp_window())
        manage_menu.add_separator()
        manage_menu.add_command(label=self.get_string('menu_manage_lookup'), command=lambda: LookupTableManagerWindow(self.master, self.db_config, self.load_initial_data))
        manage_menu.add_command(label=self.get_string('menu_view_appointments'), command=lambda: self.master.open_view_window())
        self.menubar.add_cascade(label=self.get_string('menu_manage'), menu=manage_menu)
        self.config(menu=self.menubar)

    def create_form(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        top_frame = tb.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        selection_frame = tb.LabelFrame(top_frame, text="1. Seleção Inicial", bootstyle=PRIMARY, padding=15)
        selection_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        selection_frame.grid_columnconfigure(1, weight=1)
        
        tb.Label(selection_frame, text="Selecionar WO:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.wo_combobox = tb.Combobox(selection_frame, state="readonly")
        self.wo_combobox.grid(row=0, column=1, sticky=EW, padx=5, pady=5)
        
        row = 1
        for key, cfg in self.initial_selection_fields_config.items():
            tb.Label(selection_frame, text=self.get_string(cfg["display_key"]) + ":").grid(row=row, column=0, sticky=W, padx=5, pady=5)
            widget = tb.Combobox(selection_frame, state="readonly")
            widget.grid(row=row, column=1, sticky=EW, padx=5, pady=5)
            self.fields[cfg["db_column"]] = widget
            row += 1

        control_frame = tb.LabelFrame(top_frame, text="2. Controle da Produção", bootstyle=PRIMARY, padding=15)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        control_frame.grid_columnconfigure(1, weight=1)

        self.start_finish_button = tb.Button(control_frame, text=self.get_string('start_production_btn'), bootstyle="success", command=self.toggle_production)
        self.start_finish_button.grid(row=0, column=0, padx=10, pady=10)
        
        self.status_label = tb.Label(control_frame, text=self.get_string('production_status_idle'), font=("Helvetica", 14, "bold"), bootstyle="secondary")
        self.status_label.grid(row=0, column=1, padx=10)

        self.timer_label = tb.Label(control_frame, text="00:00:00", font=("Helvetica", 20, "bold"), bootstyle=INFO)
        self.timer_label.grid(row=0, column=2, sticky=E, padx=10)

        live_entry_frame = tb.LabelFrame(main_frame, text="3. Apontamentos em Processo", bootstyle=PRIMARY, padding=15)
        live_entry_frame.grid(row=1, column=0, sticky="ew", pady=10)
        
        self.stops_button = tb.Button(live_entry_frame, text="Apontar Nova Parada", command=self.open_realtime_stop_window, state=DISABLED)
        self.stops_button.pack(pady=(0, 10))
        
        cols = ('motivo', 'inicio', 'fim', 'duracao')
        headers = ('Motivo da Parada', 'Hora Início', 'Hora Fim', 'Duração')
        self.stops_tree = tb.Treeview(live_entry_frame, columns=cols, show='headings', height=4)
        for col, header in zip(cols, headers):
            self.stops_tree.heading(col, text=header)
            self.stops_tree.column(col, anchor=CENTER, width=150)
        self.stops_tree.pack(fill=X, expand=YES)

        self.final_data_frame = tb.LabelFrame(main_frame, text="4. Dados Finais (Preencher ao Finalizar)", bootstyle=PRIMARY, padding=15)
        self.final_data_frame.grid(row=2, column=0, sticky="ew", pady=10)
        
        per_col = (len(self.final_entry_fields_config) + 1) // 2
        i = 0
        for key, cfg in self.final_entry_fields_config.items():
            row, col_offset = (i % per_col, 0) if i < per_col else (i % per_col, 3)
            tb.Label(self.final_data_frame, text=self.get_string(cfg["display_key"]) + ":").grid(row=row, column=col_offset, sticky=W, padx=5, pady=2)
            if cfg["widget_type"] == "Text":
                widget = tb.Text(self.final_data_frame, height=cfg.get("height", 3), width=cfg.get("width", 40))
                text_scroll = tb.Scrollbar(self.final_data_frame, orient=VERTICAL, command=widget.yview)
                text_scroll.grid(row=row, column=col_offset+2, sticky='ns')
                widget['yscrollcommand'] = text_scroll.set
            else:
                widget = tb.Entry(self.final_data_frame)
            
            widget.grid(row=row, column=col_offset + 1, padx=5, pady=2, sticky=EW)
            self.fields[cfg["db_column"]] = widget
            
            v_label = tb.Label(self.final_data_frame, text="", bootstyle="danger", font="Helvetica 9 italic")
            v_label.grid(row=row, column=col_offset + 3, sticky=W, padx=5)
            self.validation_labels[cfg["db_column"]] = v_label
            i += 1
        
        self.final_data_frame.grid_columnconfigure(1, weight=1)
        self.final_data_frame.grid_columnconfigure(4, weight=1)
        
        self.register_button = tb.Button(main_frame, text=self.get_string('register_entry_btn'), bootstyle="primary-outline", command=self.submit)
        self.register_button.grid(row=3, column=0, pady=10, ipadx=20, ipady=10)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def submit(self):
        if not self.selected_ordem_id or not self.end_time:
            messagebox.showerror("Erro", "A produção não foi iniciada ou finalizada corretamente.", parent=self)
            return

        final_db_cols = [cfg['db_column'] for cfg in self.final_entry_fields_config.values()]
        data = {db_col: w.get("1.0", "end-1c").strip() if isinstance(w, tb.Text) else w.get().strip()
                for db_col, w in self.fields.items() if db_col in final_db_cols}
        
        is_valid = True
        for db_col, val in data.items():
            cfg_key = next((k for k, v in self.final_entry_fields_config.items() if v['db_column'] == db_col), None)
            if not cfg_key: continue
            cfg = self.final_entry_fields_config[cfg_key]
            v_type = cfg.get("validation_type")
            if v_type == 'int' and val and not val.isdigit():
                self.validation_labels[db_col].config(text="Deve ser um número")
                is_valid = False
            else:
                 self.validation_labels[db_col].config(text="")
        
        if not is_valid:
            messagebox.showerror("Dados Inválidos", "Corrija os campos marcados.", parent=self)
            return
            
        p_data = {cfg['db_column']: self.fields[cfg['db_column']].get() for cfg in self.initial_selection_fields_config.values()}
        
        for db_col, val in data.items():
            cfg_key = next(k for k, v in self.final_entry_fields_config.items() if v['db_column'] == db_col)
            cfg = self.final_entry_fields_config[cfg_key]
            if cfg.get("validation_type") == 'int' and val:
                p_data[db_col] = int(val)
            else:
                p_data[db_col] = val if val else None

        p_data['data'] = self.start_time.date()
        p_data['horainicio'] = self.start_time.time()
        p_data['horafim'] = self.end_time.time()
        p_data['ordem_id'] = self.selected_ordem_id
        
        wo_data = self.open_wos_data.get(self.wo_combobox.get(), {})
        p_data['wo'] = self.wo_combobox.get().split(' - ')[0]
        p_data['cliente'] = wo_data.get('cliente')
        p_data['equipamento'] = wo_data.get('equipamento')
        p_data['qtde_cores'] = wo_data.get('qtde_cores')
        p_data['tipo_papel'] = wo_data.get('tipo_papel')
        p_data['formato'] = wo_data.get('formato')
        p_data['gramatura'] = wo_data.get('gramatura')
        p_data['fsc'] = wo_data.get('fsc')

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                all_db_cols = list(p_data.keys())
                q_cols = ', '.join([f'"{c}"' for c in all_db_cols])
                placeholders = ', '.join(['%s'] * len(all_db_cols))
                values = [p_data.get(c) for c in all_db_cols]
                
                query = f"INSERT INTO {self.db_config['tabela']} ({q_cols}) VALUES ({placeholders}) RETURNING id;"
                cur.execute(query, values)
                app_id = cur.fetchone()[0]

                if self.stop_times_data:
                    for stop in self.stop_times_data:
                        stop_q = "INSERT INTO paradas (apontamento_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s);"
                        cur.execute(stop_q, (app_id, stop['motivo_id'], stop['hora_inicio_parada'], stop['hora_fim_parada'], stop['motivo_extra_detail']))
            
            conn.commit()
            messagebox.showinfo("Sucesso", "Apontamento registrado com sucesso!", parent=self)
            self.update_wo_status("Concluido")
            self.destroy()

        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o apontamento: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def toggle_production(self):
        if not self.is_running:
            wo_val = self.wo_combobox.get()
            impressor_val = self.fields['impressor'].get()
            if not wo_val or not impressor_val:
                messagebox.showwarning("Campos Obrigatórios", "Por favor, selecione a WO e o Impressor antes de iniciar.", parent=self)
                return
            
            self.is_running = True
            self.start_time = datetime.now()
            self.end_time = None
            self.update_timer()
            self.update_ui_state()
            self.update_wo_status('Em Producao')
        else:
            self.is_running = False
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None
            self.end_time = datetime.now()
            self.update_ui_state()
            
    def update_timer(self):
        if self.is_running:
            elapsed = datetime.now() - self.start_time
            total_seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
            self.timer_job = self.after(1000, self.update_timer)

    def update_ui_state(self):
        if self.is_running:
            self.start_finish_button.config(text=self.get_string('finish_production_btn'), bootstyle="danger")
            self.status_label.config(text=self.get_string('production_status_running'), bootstyle="success")
            self.stops_button.config(state=NORMAL)
            self.wo_combobox.config(state=DISABLED)
            for cfg in self.initial_selection_fields_config.values():
                self.fields[cfg['db_column']].config(state=DISABLED)
            for cfg in self.final_entry_fields_config.values():
                self.fields[cfg['db_column']].config(state=DISABLED)
            self.register_button.config(state=DISABLED)
        elif self.start_time and not self.is_running:
            self.start_finish_button.config(state=DISABLED)
            self.status_label.config(text=self.get_string('production_status_stopped'), bootstyle="warning")
            self.stops_button.config(state=DISABLED)
            for cfg in self.final_entry_fields_config.values():
                self.fields[cfg['db_column']].config(state=NORMAL)
            self.register_button.config(state=NORMAL)
        else:
            self.start_finish_button.config(text=self.get_string('start_production_btn'), bootstyle="success")
            self.status_label.config(text=self.get_string('production_status_idle'), bootstyle="secondary")
            self.stops_button.config(state=DISABLED)
            self.wo_combobox.config(state="readonly")
            for cfg in self.initial_selection_fields_config.values():
                self.fields[cfg['db_column']].config(state="readonly")
            for cfg in self.final_entry_fields_config.values():
                self.fields[cfg['db_column']].config(state=DISABLED)
            self.register_button.config(state=DISABLED)

    def load_initial_data(self):
        self.load_open_wos()
        self.load_combobox_data()

    def load_open_wos(self):
        self.open_wos_data = {}
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT id, numero_wo, cliente, tipo_papel, formato, gramatura, fsc, equipamento, qtde_cores
                    FROM ordem_producao
                    WHERE status IN ('Em Aberto', 'Em Producao') ORDER BY numero_wo
                """
                cur.execute(query)
                wos_list = []
                for row in cur.fetchall():
                    (ordem_id, numero_wo, cliente, tipo_papel, formato, gramatura, fsc, equipamento, qtde_cores) = row
                    display_text = f"{numero_wo} - {cliente or 'Sem Cliente'}"
                    wos_list.append(display_text)
                    self.open_wos_data[display_text] = {
                        "id": ordem_id, "cliente": cliente, "tipo_papel": tipo_papel, "formato": formato, 
                        "gramatura": gramatura, "fsc": fsc, "equipamento": equipamento, "qtde_cores": qtde_cores
                    }
                self.wo_combobox['values'] = wos_list
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as Ordens de Serviço: {e}", parent=self)
        finally:
            if conn: conn.close()

    def load_combobox_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                for cfg in self.initial_selection_fields_config.values():
                    lookup_ref = cfg.get("lookup_table_ref")
                    if lookup_ref:
                        schema = LookupTableManagerWindow.lookup_table_schemas.get(lookup_ref)
                        if schema:
                            col = next((c['db_column'] for c in schema['columns'].values() if c['editable']), None)
                            if col:
                                cur.execute(f'SELECT DISTINCT "{col}" FROM {schema["table"]} ORDER BY "{col}"')
                                values = [row[0] for row in cur.fetchall()]
                                self.fields[cfg['db_column']]['values'] = values
        except Exception as e:
            messagebox.showwarning("Erro", f"Falha ao carregar dados de lookup: {e}", parent=self)
        finally:
            if conn: conn.close()
    
    def open_realtime_stop_window(self):
        RealTimeStopWindow(self, self.db_config, self.add_stop_to_list)
        
    def add_stop_to_list(self, stop_data):
        self.stop_times_data.append(stop_data)
        self.refresh_stops_tree()
        
    def refresh_stops_tree(self):
        for item in self.stops_tree.get_children():
            self.stops_tree.delete(item)
            
        for stop in self.stop_times_data:
            start_dt = datetime.combine(date.today(), stop['hora_inicio_parada'])
            end_dt = datetime.combine(date.today(), stop['hora_fim_parada'])
            duration = end_dt - start_dt
            
            self.stops_tree.insert('', END, values=(
                stop['motivo_text'],
                start_dt.strftime('%H:%M:%S'),
                end_dt.strftime('%H:%M:%S'),
                str(duration).split('.')[0]
            ))
            
    def update_wo_status(self, status):
        selected_wo_display = self.wo_combobox.get()
        wo_data = self.open_wos_data.get(selected_wo_display)
        if not wo_data: return
        self.selected_ordem_id = wo_data.get("id")
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE ordem_producao SET status = %s WHERE id = %s", (status, self.selected_ordem_id))
            conn.commit()
        except psycopg2.Error as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro de BD", f"Falha ao atualizar o status da WO: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def clear_placeholder(self, widget, placeholder):
        if widget.get() == placeholder: widget.delete(0, END)

    def restore_placeholder(self, widget, placeholder):
        if not widget.get(): widget.insert(0, placeholder)

    def clear_form(self):
        self.is_running = False
        self.start_time = None
        self.end_time = None
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        
        self.timer_label.config(text="00:00:00")
        self.wo_combobox.set('')
        for widget in self.fields.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            else:
                widget.delete(0, END)
        
        self.stop_times_data = []
        self.refresh_stops_tree()
        self.update_ui_state()

# ==============================================================================
# 6. CLASSE DE MENU PRINCIPAL
# ==============================================================================
class MainMenu(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.db_config = {}
        self.load_db_config()
        self.current_language = self.db_config.get('language', 'portugues')
        self.set_localized_title()
        self.geometry("600x400")
        w, h = 600, 400
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.open_windows = {}
        self.create_menu()
        self.create_widgets()

    def get_string(self, key, **kwargs):
        return LANGUAGES.get(self.current_language, LANGUAGES['portugues']).get(key, key).format(**kwargs)

    def set_localized_title(self):
        self.title(self.get_string('main_menu_title'))

    def load_db_config(self):
        if os.path.exists('db_config.json'):
            try:
                with open('db_config.json', 'r') as f: self.db_config = json.load(f)
            except Exception: self.db_config = {}

    def get_db_connection(self):
        if not all(self.db_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            messagebox.showerror("Configuração Incompleta", "A configuração da base de dados está incompleta. Por favor, verifique em Configurações.", parent=self)
            return None
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Falha ao conectar na base de dados: {e}", parent=self)
            return None
    
    def create_widgets(self):
        main_frame = tb.Frame(self, padding=(20, 20))
        main_frame.pack(fill=BOTH, expand=YES)
        tb.Label(main_frame, text=self.get_string('main_menu_title'), bootstyle=PRIMARY, font=("Helvetica", 16, "bold")).pack(pady=(10, 30))
        btn_style = "primary-outline"
        btn_padding = {'pady': 10, 'padx': 20, 'ipadx': 10, 'ipady': 10}
        tb.Button(main_frame, text=self.get_string('btn_production_entry'), bootstyle=btn_style, command=self.open_production_window).pack(fill=X, **btn_padding)
        tb.Button(main_frame, text=self.get_string('btn_pcp_management'), bootstyle=btn_style, command=self.open_pcp_window).pack(fill=X, **btn_padding)
        tb.Button(main_frame, text=self.get_string('btn_view_entries'), bootstyle=btn_style, command=self.open_view_window).pack(fill=X, **btn_padding)

    def create_menu(self):
        self.menubar = tb.Menu(self)
        config_menu = tb.Menu(self.menubar, tearoff=0)
        config_menu.add_command(label=self.get_string('menu_db_config'), command=self.open_configure_db_window)
        config_menu.add_command(label=self.get_string('menu_manage_lookup'), command=lambda: LookupTableManagerWindow(self, self.db_config))
        self.menubar.add_cascade(label=self.get_string('menu_settings'), menu=config_menu)
        self.config(menu=self.menubar)
    
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
            
    def on_window_close(self, window_key):
        if window_key in self.open_windows:
            self.open_windows[window_key].destroy()
            del self.open_windows[window_key]

    def open_configure_db_window(self):
        win = Toplevel(self)
        win.title(self.get_string('config_win_title'))
        win.transient(self)
        win.grab_set()
        labels = [("host", 'host_label'), ("porta", 'port_label'), ("usuário", 'user_label'), ("senha", 'password_label'), ("banco", 'db_label'), ("tabela", 'table_label')]
        entries = {}
        for i, (key, label_key) in enumerate(labels):
            tb.Label(win, text=self.get_string(label_key) + ":").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = tb.Entry(win, show='*' if key == "senha" else '')
            e.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            e.insert(0, self.db_config.get(key, ''))
            entries[key] = e
        tb.Label(win, text=self.get_string('language_label') + ":").grid(row=len(labels), column=0, padx=10, pady=5, sticky="w")
        lang_opts = [lang.capitalize() for lang in LANGUAGES.keys()]
        lang_selector = tb.Combobox(win, values=lang_opts, state="readonly")
        lang_selector.grid(row=len(labels), column=1, padx=10, pady=5, sticky="ew")
        lang_selector.set(self.current_language.capitalize())
        btn_frame = tb.Frame(win)
        btn_frame.grid(row=len(labels) + 1, columnspan=2, pady=15)
        tb.Button(btn_frame, text=self.get_string('test_connection_btn'), bootstyle="info-outline", command=lambda: self.test_db_connection(entries, win)).pack(side="left", padx=5)
        tb.Button(btn_frame, text=self.get_string('save_btn'), bootstyle="success", command=lambda: self.save_and_close_config(entries, lang_selector, win)).pack(side="left", padx=5)

    def save_and_close_config(self, entries, lang_selector, win):
        new_config = {k: v.get() for k, v in entries.items()}
        new_lang = lang_selector.get().lower()
        new_config['language'] = new_lang
        self.db_config = new_config
        try:
            with open('db_config.json', 'w') as f: json.dump(self.db_config, f, indent=4)
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('config_save_success'), parent=win)
        except Exception as e:
            messagebox.showerror(self.get_string('save_btn'), self.get_string('config_save_error', error=e), parent=win)
        
        if self.current_language != new_lang:
            self.current_language = new_lang
            for widget in self.winfo_children():
                widget.destroy()
            self.create_menu()
            self.create_widgets()
            self.set_localized_title()

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

# ==============================================================================
# 7. PONTO DE ENTRADA DA APLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    main_app = MainMenu()
    main_app.mainloop()
