# Versão Final Unificada com Edição e Exclusão

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import messagebox, Toplevel, END, W, E, S, N, CENTER, filedialog
import psycopg2
from datetime import datetime, time, date
import json
import os
import csv

# ==============================================================================
# 1. I18N STRINGS (Traduções)
# Adicionadas novas chaves para edição e exclusão
# ==============================================================================
LANGUAGES = {
    'portugues': {
        'app_title': 'Sistema de Apontamento de Produção',
        'menu_settings': 'Configurações',
        'menu_db_config': 'Configurar Banco de Dados',
        'menu_manage': 'Gerenciar',
        'menu_manage_lookup': 'Gerenciar Tabelas de Apoio',
        'menu_view_appointments': 'Visualizar Apontamentos',
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
        'config_loaded_success': 'Configuração do banco de dados carregada com sucesso!',
        'config_load_error_json': 'Erro ao carregar o arquivo de configuração do banco de dados. Formato JSON inválido.',
        'config_load_error_generic': 'Erro ao carregar a configuração do banco de dados: {error}',
        'config_not_found': 'Arquivo de configuração do banco de dados não encontrado. Por favor, configure a conexão.',
        'config_save_success': 'Configuração do banco de dados salva com sucesso!',
        'config_save_error': 'Erro ao salvar a configuração do banco de dados: {error}',
        'test_connection_warning_fill_fields': 'Por favor, preencha todos os campos antes de testar a conexão.',
        'test_connection_success': 'Conexão com o banco de dados estabelecida com sucesso!',
        'test_connection_failed_db': 'Falha na conexão com o banco de dados: {error}',
        'test_connection_failed_unexpected': 'Falha inesperada ao testar conexão: {error}',
        'verify_credentials_msg': 'Verifique as credenciais e o status do servidor.',
        'loading_data_failed_db_perm': 'Falha ao carregar dados do banco de dados. Verifique as permissões ou a conexão: {error}',
        'loading_data_failed_generic': 'Erro geral ao carregar dados: {error}',
        'loading_data_success': 'Dados carregados com sucesso!',
        'form_data_section': 'Dados do Apontamento',
        'submit_btn': 'Registrar Apontamento',
        'clear_form_btn': 'Limpar Formulário',
        'validation_error_required': 'Campo obrigatório.',
        'validation_error_date_format': 'Formato de data inválido (DD/MM/AAAA).',
        'validation_error_time_format': 'Formato de hora inválido (HH:MM).',
        'validation_error_int_format': 'Deve ser um número inteiro válido.',
        'validation_error_fix_fields': 'Por favor, corrija os campos destacados em vermelho.',
        'db_config_missing': 'Configurações do banco de dados não encontradas. Por favor, configure-as.',
        'table_name_missing': 'Nome da tabela não configurado no banco de dados.',
        'db_send_success': 'Apontamento registrado com sucesso!',
        'db_send_failed': 'Falha ao registrar apontamento: {error}',
        'generic_error': 'Ocorreu um erro: {error}',
        'manager_title': 'Gerenciar Tabelas de Apoio',
        'manager_select_table': 'Selecionar Tabela',
        'select_table_warning': 'Por favor, selecione uma tabela para gerenciar.',
        'add_new_btn': 'Adicionar Novo',
        'edit_selected_btn': 'Editar Selecionado',
        'delete_selected_btn': 'Excluir Selecionado',
        'db_load_table_failed': 'Falha ao carregar dados da tabela "{display_name}": {error}',
        'schema_not_found': 'Esquema para tabela "{table_name}" não encontrado.',
        'select_entry_to_edit': 'Por favor, selecione uma entrada para editar.',
        'save_entry_validation_error': 'Erro de validação para "{field_name}". Por favor, verifique o tipo de dado.',
        'entry_edited_success': 'Entrada editada com sucesso!',
        'new_entry_added_success': 'Nova entrada adicionada com sucesso!',
        'db_save_failed': 'Falha ao salvar a entrada no banco de dados: {error}\nDetalhes: {details}',
        'db_integrity_error': 'Erro de integridade do banco de dados. Pode ser um valor duplicado ou inválido: {error}\nDetalhes: {details}',
        'select_entry_to_delete': 'Por favor, selecione uma entrada para excluir.',
        'confirm_delete_title': 'Confirmar Exclusão',
        'confirm_delete_message': 'Tem certeza que deseja excluir a entrada com ID {pk_value} da tabela "{display_name}"? Esta ação é irreversível.',
        'delete_success': 'Entrada excluída com sucesso!',
        'db_delete_failed': 'Falha ao excluir a entrada do banco de dados: {error}\nDetalhes: {details}',
        'col_id': 'ID',
        'col_descricao': 'Descrição',
        'col_nome': 'Nome',
        'col_codigo': 'Código',
        'col_valor': 'Valor',
        'col_data': 'Data',
        'col_horainicio': 'Hora Início',
        'col_horafim': 'Hora Fim',
        'equipment_label': 'Equipamento',
        'col_wo': 'WO',
        'col_cliente': 'Cliente',
        'col_qtde_cores': 'QTDE CORES',
        'col_tipo_papel': 'TIPO PAPEL',
        'col_numeroinspecao': 'Número Inspeção',
        'col_gramatura': 'Gramatura',
        'col_formato': 'Formato',
        'col_fsc': 'FSC',
        'col_tiragem_em_folhas': 'Tiragem em Folhas',
        'col_giros_rodados': 'Giros Rodados',
        'col_perdas_malas': 'Perdas/ Malas',
        'col_total_lavagens': 'Total Lavagens',
        'col_total_acertos': 'Total Acertos',
        'printer_label': 'Impressor',
        'col_ocorrencias': 'Ocorrências',
        'col_motivos_parada': 'Motivo da Parada',
        'shift_label': 'Turno',
        'col_quantidadeproduzida': 'Quantidade Produzida',
        'filter_section': 'Filtros de Apontamentos',
        'date_start_label': 'Data Início',
        'date_end_label': 'Data Fim',
        'apply_filters_btn': 'Aplicar Filtros',
        'clear_filters_btn': 'Limpar Filtros',
        'export_csv_btn': 'Exportar para CSV',
        'no_data_to_export': 'Não há dados para exportar.',
        'csv_files_type': 'Arquivos CSV',
        'all_files_type': 'Todos os Arquivos',
        'save_csv_dialog_title': 'Salvar como CSV',
        'export_success_message': 'Dados exportados com sucesso para:\n{path}',
        'export_error': 'Erro ao exportar dados para CSV: {error}',
        'view_appointments_title': 'Visualizar Apontamentos',
        'loaded_appointments_success': 'Dados da tabela "{table_name}" carregados com sucesso!',
        'db_load_appointments_failed': 'Falha ao carregar apontamentos da tabela "{table_name}": {error}',
        'has_stops_question': 'Possui Paradas?',
        'open_stop_times_btn': 'Configurar Paradas',
        'stop_times_window_title': 'Apontamento de Paradas',
        'num_stops_label': 'Número de Paradas',
        'generate_fields_btn': 'Gerar Campos',
        'stop_label': 'Parada',
        'stop_times_control_section': 'Controle de Paradas',
        'stop_times_saved_success': 'Dados de paradas salvos com sucesso!',
        'invalid_num_stops_error': 'Por favor, insira um número válido para a quantidade de paradas.',
        'validation_error_invalid_selection': 'Por favor, selecione um item válido.',
        'validation_error_time_order': 'Hora Fim deve ser posterior à Hora Início.',
        'validation_error_fix_fields_stops': 'Por favor, corrija os campos de parada destacados em vermelho.',
        'other_motives_label': 'Especifique o Motivo',
        'has_stops_question_short': 'Paradas?',
        'yes_short': 'Sim',
        'no_short': 'Não',
        'view_stop_details_btn': 'Ver Detalhes das Paradas',
        'select_appointment_to_view_stops': 'Por favor, selecione um apontamento para ver os detalhes das paradas.',
        'no_stops_for_appointment': 'Este apontamento não possui paradas registradas.',
        'no_stops_for_appointment_full': 'Nenhuma parada registrada para este apontamento.',
        'stop_details_for_appointment': 'Detalhes das Paradas para Apontamento ID: {id}',
        'db_load_stops_failed': 'Falha ao carregar detalhes das paradas: {error}',
        'db_conn_incomplete': 'Configuração do banco de dados incompleta ou ausente.',
        'invalid_input': 'Entrada Inválida',
        'filter_date_format_warning': 'Formato de data inválido para o campo "{field}". Use DD/MM/AAAA.',
        # Novas chaves de tradução
        'edit_appointment_btn': 'Editar Apontamento',
        'delete_appointment_btn': 'Excluir Apontamento',
        'confirm_delete_appointment_title': 'Confirmar Exclusão de Apontamento',
        'confirm_delete_appointment_msg': 'Tem certeza que deseja excluir permanentemente o apontamento com ID {id}? Todas as paradas associadas também serão excluídas. Esta ação não pode ser desfeita.',
        'delete_appointment_success': 'Apontamento ID {id} excluído com sucesso!',
        'delete_appointment_failed': 'Falha ao excluir apontamento: {error}',
        'select_appointment_to_edit': 'Selecione um apontamento para editar.',
        'select_appointment_to_delete': 'Selecione um apontamento para excluir.',
        'edit_appointment_title': 'Editar Apontamento - ID: {id}',
        'save_changes_btn': 'Salvar Alterações',
        'update_success': 'Apontamento ID {id} atualizado com sucesso!',
        'update_failed': 'Falha ao atualizar o apontamento: {error}',
    },
    'english': {
        'app_title': 'Production Tracking System',
        'menu_settings': 'Settings',
        'menu_db_config': 'Configure Database',
        'menu_manage': 'Manage',
        'menu_manage_lookup': 'Manage Lookup Tables',
        'menu_view_appointments': 'View Appointments',
        'config_win_title': 'Database Configuration',
        'host_label': 'Host',
        'port_label': 'Port',
        'user_label': 'User',
        'password_label': 'Password',
        'db_label': 'Database',
        'table_label': 'Appointment Table',
        'language_label': 'Language',
        'test_connection_btn': 'Test Connection',
        'save_btn': 'Save',
        'cancel_btn': 'Cancel',
        'config_loaded_success': 'Database configuration loaded successfully!',
        'config_load_error_json': 'Error loading database configuration file. Invalid JSON format.',
        'config_load_error_generic': 'Error loading database configuration: {error}',
        'config_not_found': 'Database configuration file not found. Please configure the connection.',
        'config_save_success': 'Database configuration saved successfully!',
        'config_save_error': 'Error saving database configuration: {error}',
        'test_connection_warning_fill_fields': 'Please fill in all fields before testing the connection.',
        'test_connection_success': 'Database connection established successfully!',
        'test_connection_failed_db': 'Database connection failed: {error}',
        'test_connection_failed_unexpected': 'Unexpected connection test failure: {error}',
        'verify_credentials_msg': 'Check credentials and server status.',
        'loading_data_failed_db_perm': 'Failed to load data from database. Check permissions or connection: {error}',
        'loading_data_failed_generic': 'General error loading data: {error}',
        'loading_data_success': 'Data loaded successfully!',
        'form_data_section': 'Appointment Data',
        'submit_btn': 'Register Appointment',
        'clear_form_btn': 'Clear Form',
        'validation_error_required': 'Required field.',
        'validation_error_date_format': 'Invalid date format (DD/MM/YYYY).',
        'validation_error_time_format': 'Invalid time format (HH:MM).',
        'validation_error_int_format': 'Must be a valid integer.',
        'validation_error_fix_fields': 'Please correct the highlighted fields.',
        'db_config_missing': 'Database configuration not found. Please configure it.',
        'table_name_missing': 'Table name not configured in the database.',
        'db_send_success': 'Appointment registered successfully!',
        'db_send_failed': 'Failed to register appointment: {error}',
        'generic_error': 'An error occurred: {error}',
        'manager_title': 'Manage Lookup Tables',
        'manager_select_table': 'Select Table',
        'select_table_warning': 'Please select a table to manage.',
        'add_new_btn': 'Add New',
        'edit_selected_btn': 'Edit Selected',
        'delete_selected_btn': 'Delete Selected',
        'db_load_table_failed': 'Failed to load data from table "{display_name}": {error}',
        'schema_not_found': 'Schema for table "{table_name}" not found.',
        'select_entry_to_edit': 'Please select an entry to edit.',
        'save_entry_validation_error': 'Validation error for "{field_name}". Please check the data type.',
        'entry_edited_success': 'Entry edited successfully!',
        'new_entry_added_success': 'New entry added successfully!',
        'db_save_failed': 'Failed to save entry to database: {error}\nDetails: {details}',
        'db_integrity_error': 'Database integrity error. May be a duplicate or invalid value: {error}\nDetails: {details}',
        'select_entry_to_delete': 'Please select an entry to delete.',
        'confirm_delete_title': 'Confirm Deletion',
        'confirm_delete_message': 'Are you sure you want to delete the entry with ID {pk_value} from table "{display_name}"? This action is irreversible.',
        'delete_success': 'Entry deleted successfully!',
        'db_delete_failed': 'Failed to delete entry from database: {error}\nDetails: {details}',
        'col_id': 'ID',
        'col_descricao': 'Description',
        'col_nome': 'Name',
        'col_codigo': 'Code',
        'col_valor': 'Value',
        'col_data': 'Date',
        'col_horainicio': 'Start Time',
        'col_horafim': 'End Time',
        'equipment_label': 'Equipment',
        'col_wo': 'WO',
        'col_cliente': 'Client',
        'col_qtde_cores': 'QTY COLORS',
        'col_tipo_papel': 'PAPER TYPE',
        'col_numeroinspecao': 'Inspection Number',
        'col_gramatura': 'Grammage',
        'col_formato': 'Format',
        'col_fsc': 'FSC',
        'col_tiragem_em_folhas': 'Sheets Run',
        'col_giros_rodados': 'Revolutions',
        'col_perdas_malas': 'Losses/Waste',
        'col_total_lavagens': 'Total Washes',
        'col_total_acertos': 'Total Adjustments',
        'printer_label': 'Printer',
        'col_ocorrencias': 'Occurrences',
        'col_motivos_parada': 'Stop Reason',
        'shift_label': 'Shift',
        'col_quantidadeproduzida': 'Quantity Produced',
        'filter_section': 'Appointment Filters',
        'date_start_label': 'Start Date',
        'date_end_label': 'End Date',
        'apply_filters_btn': 'Apply Filters',
        'clear_filters_btn': 'Clear Filters',
        'export_csv_btn': 'Export to CSV',
        'no_data_to_export': 'No data to export.',
        'csv_files_type': 'CSV Files',
        'all_files_type': 'All Files',
        'save_csv_dialog_title': 'Save as CSV',
        'export_success_message': 'Data exported successfully to:\n{path}',
        'export_error': 'Error exporting data to CSV: {error}',
        'view_appointments_title': 'View Appointments',
        'loaded_appointments_success': 'Data from table "{table_name}" loaded successfully!',
        'db_load_appointments_failed': 'Failed to load appointments from table "{table_name}": {error}',
        'has_stops_question': 'Has Stops?',
        'open_stop_times_btn': 'Configure Stops',
        'stop_times_window_title': 'Stop Times Entry',
        'num_stops_label': 'Number of Stops',
        'generate_fields_btn': 'Generate Fields',
        'stop_label': 'Stop',
        'stop_times_control_section': 'Stop Control',
        'stop_times_saved_success': 'Stop times data saved successfully!',
        'invalid_num_stops_error': 'Please enter a valid number for the quantity of stops.',
        'validation_error_invalid_selection': 'Please select a valid item.',
        'validation_error_time_order': 'End Time must be after Start Time.',
        'validation_error_fix_fields_stops': 'Please correct the stop fields highlighted in red.',
        'other_motives_label': 'Specify Reason',
        'has_stops_question_short': 'Stops?',
        'yes_short': 'Yes',
        'no_short': 'No',
        'view_stop_details_btn': 'View Stop Details',
        'select_appointment_to_view_stops': 'Please select an appointment to view stop details.',
        'no_stops_for_appointment': 'This appointment has no stops registered.',
        'no_stops_for_appointment_full': 'No stops registered for this appointment.',
        'stop_details_for_appointment': 'Stop Details for Appointment ID: {id}',
        'db_load_stops_failed': 'Failed to load stop details: {error}',
        'db_conn_incomplete': 'Database configuration is incomplete or missing.',
        'invalid_input': 'Invalid Input',
        'filter_date_format_warning': 'Invalid date format for field "{field}". Use DD/MM/YYYY.',
        # New translation keys
        'edit_appointment_btn': 'Edit Appointment',
        'delete_appointment_btn': 'Delete Appointment',
        'confirm_delete_appointment_title': 'Confirm Appointment Deletion',
        'confirm_delete_appointment_msg': 'Are you sure you want to permanently delete appointment ID {id}? All associated stops will also be deleted. This action cannot be undone.',
        'delete_appointment_success': 'Appointment ID {id} deleted successfully!',
        'delete_appointment_failed': 'Failed to delete appointment: {error}',
        'select_appointment_to_edit': 'Please select an appointment to edit.',
        'select_appointment_to_delete': 'Please select an appointment to delete.',
        'edit_appointment_title': 'Edit Appointment - ID: {id}',
        'save_changes_btn': 'Save Changes',
        'update_success': 'Appointment ID {id} updated successfully!',
        'update_failed': 'Failed to update appointment: {error}',
    }
}

def get_connection_params(config_dict):
    """Mapeia as chaves do dicionário de configuração para as chaves do psycopg2."""
    return {
        'host': config_dict.get('host'),
        'port': config_dict.get('porta'),
        'dbname': config_dict.get('banco'),
        'user': config_dict.get('usuário'),
        'password': config_dict.get('senha')
    }
# ==============================================================================
# 2. LOOKUP TABLE MANAGER WINDOW CLASS
# (Unchanged, provided for completeness)
# ==============================================================================
class LookupTableManagerWindow(Toplevel):
    lookup_table_schemas = {
        "equipamentos_tipos": {
            "display_name_key": "equipment_label", "table": "equipamentos_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "qtde_cores_tipos": {
            "display_name_key": "col_qtde_cores", "table": "qtde_cores_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "tipos_papel": {
            "display_name_key": "col_tipo_papel", "table": "tipos_papel", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "impressores": {
            "display_name_key": "printer_label", "table": "impressores", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "nome": {"type": "str", "db_column": "nome", "display_key": "col_nome", "editable": True}}},
        "motivos_parada_tipos": {
            "display_name_key": "col_motivos_parada", "table": "motivos_parada_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "codigo": {"type": "int", "db_column": "codigo", "display_key": "col_codigo", "editable": True},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "formatos_tipos": {
            "display_name_key": "col_formato", "table": "formatos_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "gramaturas_tipos": {
            "display_name_key": "col_gramatura", "table": "gramaturas_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "valor": {"type": "int", "db_column": "valor", "display_key": "col_valor", "editable": True}}},
        "fsc_tipos": {
            "display_name_key": "col_fsc", "table": "fsc_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
        "turnos_tipos": {
            "display_name_key": "shift_label", "table": "turnos_tipos", "pk_column": "id",
            "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False},
                        "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
    }
    # ... (O resto da classe LookupTableManagerWindow continua igual à versão anterior)
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
        if not self.db_config or not all(self.db_config.get(k) for k in ['host', 'porta', 'usuário', 'senha', 'banco']):
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('db_conn_incomplete'))
            return None
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except psycopg2.OperationalError as e:
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('test_connection_failed_db', error=e) + self.get_string('verify_credentials_msg'))
            return None
        except Exception as e:
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('test_connection_failed_unexpected', error=e))
            return None

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
            messagebox.showwarning(self.get_string('manager_select_table'), self.get_string('select_table_warning'))

    def load_table_data(self, table_name):
        conn = self.get_db_connection()
        if not conn: return
        schema = self.lookup_table_schemas.get(table_name)
        if not schema:
            messagebox.showerror(self.get_string('db_load_table_failed'), self.get_string('schema_not_found', table_name=table_name))
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
            messagebox.showerror(self.get_string('db_load_table_failed'), self.get_string('db_load_table_failed', display_name=self.get_string(schema['display_name_key']), error=e))
        finally:
            if conn: conn.close()

    def open_add_edit_window(self, edit_mode=False):
        if not self.current_table:
            messagebox.showwarning(self.get_string('manager_select_table'), self.get_string('select_table_warning'))
            return
        selected_item = self.treeview.focus()
        if edit_mode and not selected_item:
            messagebox.showwarning(self.get_string('edit_selected_btn'), self.get_string('select_entry_to_edit'))
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
            messagebox.showerror(self.get_string('save_btn'), self.get_string('save_entry_validation_error', field_name=self.get_string(schema['columns'][next(iter(entries))]['display_key'])))
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
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('entry_edited_success' if edit_mode else 'new_entry_added_success'))
            window.destroy()
            self.load_table_data(self.current_table)
            if self.refresh_main_comboboxes_callback: self.refresh_main_comboboxes_callback()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror(self.get_string('db_save_failed'), self.get_string('db_save_failed', error=e, details=e.pgerror))
        finally:
            if conn: conn.close()

    def delete_selected_entry(self):
        item = self.treeview.focus()
        if not item:
            messagebox.showwarning(self.get_string('delete_selected_btn'), self.get_string('select_entry_to_delete'))
            return
        schema = self.lookup_table_schemas[self.current_table]
        pk_val = self.treeview.item(item, 'values')[list(schema["columns"].keys()).index(schema["pk_column"])]
        if not messagebox.askyesno(self.get_string('confirm_delete_title'), self.get_string('confirm_delete_message', pk_value=pk_val, display_name=self.get_string(schema['display_name_key']))):
            return
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {schema['table']} WHERE \"{schema['pk_column']}\" = %s", (pk_val,))
            conn.commit()
            messagebox.showinfo(self.get_string('delete_selected_btn'), self.get_string('delete_success'))
            self.load_table_data(self.current_table)
            if self.refresh_main_comboboxes_callback: self.refresh_main_comboboxes_callback()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror(self.get_string('delete_selected_btn'), self.get_string('db_delete_failed', error=e, details=e.pgerror))
        finally:
            if conn: conn.close()


# ==============================================================================
# 3. STOP TIMES WINDOW CLASS
# (Unchanged, provided for completeness)
# ==============================================================================
class StopTimesWindow(Toplevel):
    # ... (A classe StopTimesWindow continua igual à versão anterior)
    def __init__(self, master, db_config, initial_stop_data=None):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.motivos_parada_options = []
        self.stop_entries = []
        self.stop_validation_labels = []
        self.initial_stop_data = initial_stop_data if initial_stop_data is not None else []
        self.load_motivos_parada()
        self.create_stop_times_ui()
        self.set_localized_title()
        self.update_idletasks()
        window_width, window_height = 700, 500
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (window_width // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.grab_set()

    def get_string(self, key, **kwargs): return self.master.get_string(key, **kwargs)
    def set_localized_title(self): self.title(self.get_string('stop_times_window_title'))
    def get_db_connection(self):
        if not self.db_config or not all(self.db_config.get(k) for k in ['host', 'porta', 'usuário', 'senha', 'banco']):
            messagebox.showerror(self.get_string('stop_times_window_title'), self.get_string('db_conn_incomplete'))
            return None
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except psycopg2.OperationalError as e:
            messagebox.showerror(self.get_string('stop_times_window_title'), self.get_string('test_connection_failed_db', error=e) + self.get_string('verify_credentials_msg'))
            return None
        except Exception as e:
            messagebox.showerror(self.get_string('stop_times_window_title'), self.get_string('test_connection_failed_unexpected', error=e))
            return None

    def load_motivos_parada(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                schema = LookupTableManagerWindow.lookup_table_schemas["motivos_parada_tipos"]
                q_col1, q_col2 = schema['columns']['codigo']['db_column'], schema['columns']['descricao']['db_column']
                query = f'SELECT "{q_col1}", "{q_col2}", "{schema["pk_column"]}" FROM {schema["table"]} ORDER BY "{q_col1}"'
                cur.execute(query)
                self.motivos_parada_options = [(f"{row[0]} - {row[1]}", row[2]) for row in cur.fetchall()]
        except psycopg2.Error as e:
            messagebox.showwarning(self.get_string('loading_data_failed_db_perm'), self.get_string('loading_data_failed_db_perm', error=e))
        finally:
            if conn: conn.close()

    def create_stop_times_ui(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        control_frame = tb.LabelFrame(main_frame, text=self.get_string('stop_times_control_section'), bootstyle="primary", padding=10)
        control_frame.pack(fill="x", pady=(0, 10))
        tb.Label(control_frame, text=self.get_string('num_stops_label') + ":").pack(side="left", padx=5)
        self.num_stops_entry = tb.Entry(control_frame, width=5)
        self.num_stops_entry.pack(side="left", padx=5)
        self.num_stops_entry.insert(0, str(len(self.initial_stop_data)))
        self.num_stops_entry.bind("<Return>", lambda e: self.generate_stop_fields())
        tb.Button(control_frame, text=self.get_string('generate_fields_btn'), bootstyle="info", command=self.generate_stop_fields).pack(side="left", padx=10)
        
        sf_container = tb.Frame(main_frame)
        sf_container.pack(fill="both", expand=True)
        canvas = tb.Canvas(sf_container)
        scrollbar = tb.Scrollbar(sf_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tb.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        button_frame = tb.Frame(main_frame, padding=10)
        button_frame.pack(fill="x", pady=(10, 0))
        tb.Button(button_frame, text=self.get_string('save_btn'), bootstyle="success", command=self.save_stop_times).pack(side="left", padx=5, expand=True)
        tb.Button(button_frame, text=self.get_string('cancel_btn'), bootstyle="secondary", command=self.destroy).pack(side="left", padx=5, expand=True)
        if self.initial_stop_data: self.generate_stop_fields(initial_load=True)

    def generate_stop_fields(self, initial_load=False):
        for child in self.scrollable_frame.winfo_children(): child.destroy()
        self.stop_entries, self.stop_validation_labels = [], []
        try:
            num_stops = int(self.num_stops_entry.get())
            if num_stops < 0: raise ValueError
        except ValueError:
            messagebox.showerror(self.get_string('invalid_input'), self.get_string('invalid_num_stops_error'))
            return
        
        for i in range(num_stops):
            stop_data = self.initial_stop_data[i] if initial_load and i < len(self.initial_stop_data) else {}
            row_offset = i * 4
            tb.Label(self.scrollable_frame, text=f"{i+1}ª {self.get_string('stop_label')}:", font="Helvetica 10 bold").grid(row=row_offset, column=0, columnspan=4, sticky="w", pady=(10, 0))
            
            tb.Label(self.scrollable_frame, text=self.get_string('col_motivos_parada') + ":").grid(row=row_offset + 1, column=0, sticky="w", padx=5, pady=2)
            motivo_cb = tb.Combobox(self.scrollable_frame, values=[opt[0] for opt in self.motivos_parada_options], state="readonly")
            motivo_cb.grid(row=row_offset + 1, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
            
            outros_label = tb.Label(self.scrollable_frame, text=self.get_string('other_motives_label') + ":")
            outros_entry = tb.Entry(self.scrollable_frame)
            
            tb.Label(self.scrollable_frame, text=self.get_string('col_horainicio') + ":").grid(row=row_offset + 2, column=0, sticky="w", padx=5, pady=2)
            inicio_entry = tb.Entry(self.scrollable_frame)
            inicio_entry.grid(row=row_offset + 2, column=1, padx=5, pady=2, sticky="ew")
            
            tb.Label(self.scrollable_frame, text=self.get_string('col_horafim') + ":").grid(row=row_offset + 2, column=2, sticky="w", padx=5, pady=2)
            fim_entry = tb.Entry(self.scrollable_frame)
            fim_entry.grid(row=row_offset + 2, column=3, padx=5, pady=2, sticky="ew")

            for entry, placeholder in [(inicio_entry, "HH:MM"), (fim_entry, "HH:MM")]:
                entry.insert(0, placeholder)
                entry.bind("<FocusIn>", lambda e, w=entry, p=placeholder: self.master.clear_placeholder(w, p))
                entry.bind("<FocusOut>", lambda e, w=entry, p=placeholder: self.master.restore_placeholder(w, p))

            entries = {"motivo_combobox": motivo_cb, "outros_motivos_label": outros_label, "outros_motivos_entry": outros_entry, "hora_inicio_entry": inicio_entry, "hora_fim_entry": fim_entry}
            self.stop_entries.append(entries)
            motivo_cb.bind("<<ComboboxSelected>>", lambda e, entries=entries, row=row_offset: self._handle_motivo_selection(entries, row))

            if initial_load and stop_data:
                display_value = next((opt[0] for opt in self.motivos_parada_options if opt[1] == stop_data.get('motivo_id')), "")
                motivo_cb.set(display_value)
                if "outros" in display_value.lower():
                    self._handle_motivo_selection(entries, row_offset)
                    outros_entry.insert(0, stop_data.get('motivo_extra_detail', ''))
                
                inicio_entry.delete(0, END)
                inicio_entry.insert(0, stop_data.get('hora_inicio_parada').strftime("%H:%M") if isinstance(stop_data.get('hora_inicio_parada'), time) else "")
                fim_entry.delete(0, END)
                fim_entry.insert(0, stop_data.get('hora_fim_parada').strftime("%H:%M") if isinstance(stop_data.get('hora_fim_parada'), time) else "")

    def _handle_motivo_selection(self, entries, row_base):
        is_other = "outros" in entries["motivo_combobox"].get().lower()
        if is_other:
            entries["outros_motivos_label"].grid(row=row_base + 3, column=0, sticky="w", padx=5, pady=2)
            entries["outros_motivos_entry"].grid(row=row_base + 3, column=1, columnspan=3, padx=5, pady=2, sticky="ew")
        else:
            entries["outros_motivos_label"].grid_remove()
            entries["outros_motivos_entry"].grid_remove()
            entries["outros_motivos_entry"].delete(0, END)

    def save_stop_times(self):
        parsed_stops = []
        is_valid = True
        for entry_set in self.stop_entries:
            motivo_display = entry_set["motivo_combobox"].get().strip()
            hora_inicio_str = entry_set["hora_inicio_entry"].get().strip()
            hora_fim_str = entry_set["hora_fim_entry"].get().strip()
            outros_text = entry_set["outros_motivos_entry"].get().strip()
            
            if not motivo_display or not hora_inicio_str or not hora_fim_str or ("outros" in motivo_display.lower() and not outros_text):
                is_valid = False
                messagebox.showerror(self.get_string('invalid_input'), self.get_string('validation_error_required'))
                break
            
            try:
                hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
                hora_fim = datetime.strptime(hora_fim_str, "%H:%M").time()
                if hora_fim <= hora_inicio:
                    is_valid = False
                    messagebox.showerror(self.get_string('invalid_input'), self.get_string('validation_error_time_order'))
                    break
            except ValueError:
                is_valid = False
                messagebox.showerror(self.get_string('invalid_input'), self.get_string('validation_error_time_format'))
                break
            
            motivo_id = next((opt[1] for opt in self.motivos_parada_options if opt[0] == motivo_display), None)
            parsed_stops.append({"motivo_id": motivo_id, "hora_inicio_parada": hora_inicio, "hora_fim_parada": hora_fim, "motivo_extra_detail": outros_text if "outros" in motivo_display.lower() else None})

        if is_valid:
            self.master.stop_times_data = parsed_stops
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('stop_times_saved_success'))
            self.destroy()

# ==============================================================================
# 4. VIEW APPOINTMENTS WINDOW CLASS
# (MODIFICADA para incluir permissões e botões de Editar/Excluir)
# ==============================================================================
class ViewAppointmentsWindow(Toplevel):
    APPOINTMENT_COLUMNS_SCHEMA = {
        "id": {"display_key": "col_id", "db_column": "id", "type": "int"},
        "data": {"display_key": "col_data", "db_column": "data", "type": "date"},
        "horainicio": {"display_key": "col_horainicio", "db_column": "horainicio", "type": "time"},
        "horafim": {"display_key": "col_horafim", "db_column": "horafim", "type": "time"},
        "equipamento": {"display_key": "equipment_label", "db_column": "equipamento", "type": "str"},
        "wo": {"display_key": "col_wo", "db_column": "wo", "type": "str"},
        "cliente": {"display_key": "col_cliente", "db_column": "cliente", "type": "str"},
        "qtde_cores": {"display_key": "col_qtde_cores", "db_column": "qtde_cores", "type": "str"},
        "tipo_papel": {"display_key": "col_tipo_papel", "db_column": "tipo_papel", "type": "str"},
        "numeroinspecao": {"display_key": "col_numeroinspecao", "db_column": "numeroinspecao", "type": "str"},
        "gramatura": {"display_key": "col_gramatura", "db_column": "gramatura", "type": "int"},
        "formato": {"display_key": "col_formato", "db_column": "formato", "type": "str"},
        "fsc": {"display_key": "col_fsc", "db_column": "fsc", "type": "str"},
        "tiragem_em_folhas": {"display_key": "col_tiragem_em_folhas", "db_column": "tiragem_em_folhas", "type": "int"},
        "giros_rodados": {"display_key": "col_giros_rodados", "db_column": "giros_rodados", "type": "int"},
        "perdas_malas": {"display_key": "col_perdas_malas", "db_column": "perdas_malas", "type": "int"},
        "total_lavagens": {"display_key": "col_total_lavagens", "db_column": "total_lavagens", "type": "int"},
        "total_acertos": {"display_key": "col_total_acertos", "db_column": "total_acertos", "type": "int"},
        "impressor": {"display_key": "printer_label", "db_column": "impressor", "type": "str"},
        "ocorrencias": {"display_key": "col_ocorrencias", "db_column": "ocorrencias", "type": "str"},
        "turno": {"display_key": "shift_label", "db_column": "turno", "type": "str"},
        "quantidadeproduzida": {"display_key": "col_quantidadeproduzida", "db_column": "quantidadeproduzida", "type": "int"},
        "possui_paradas": {"display_key": "has_stops_question_short", "db_column": "possui_paradas", "type": "bool"}
    }
    
    FILTER_LOOKUP_TABLES = {
        "equipamento": {"table": "equipamentos_tipos", "column": "descricao"},
        "impressor": {"table": "impressores", "column": "nome"},
        "turno": {"table": "turnos_tipos", "column": "descricao"},
    }

    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.apontamento_table_name = self.db_config.get('tabela', 'apontamento')
        self.is_superuser = False
        self.check_superuser_status()
        
        self.filter_fields = {}
        self.filter_combobox_data = {}
        self.load_filter_combobox_data()
        self.create_view_ui()
        self.load_apontamentos_data()

        self.update_idletasks()
        w, h = 1300, 700
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (w // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.set_localized_title()
        self.grab_set()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def set_localized_title(self):
        self.title(self.get_string('view_appointments_title'))

    def get_db_connection(self):
        if not self.db_config or not all(self.db_config.get(k) for k in ['host', 'porta', 'usuário', 'senha', 'banco']):
            messagebox.showerror(self.get_string('view_appointments_title'), self.get_string('db_conn_incomplete'))
            return None
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except Exception as e:
            messagebox.showerror(self.get_string('view_appointments_title'), self.get_string('test_connection_failed_db', error=e))
            return None

    def check_superuser_status(self):
        """Verifica no banco de dados se o usuário logado é um superusuário."""
        conn = self.get_db_connection()
        if not conn:
            self.is_superuser = False
            return
        try:
            with conn.cursor() as cur:
                # Usa o usuário da configuração para checar seu status de superuser
                cur.execute("SELECT rolsuper FROM pg_roles WHERE rolname = %s", (self.db_config.get('usuário'),))
                result = cur.fetchone()
                if result and result[0]:
                    self.is_superuser = True
                else:
                    self.is_superuser = False
        except psycopg2.Error:
            self.is_superuser = False
        finally:
            if conn:
                conn.close()

    def load_filter_combobox_data(self):
        self.filter_combobox_data = {"equipamento": [], "impressor": [], "turno": []}
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                for field, config in self.FILTER_LOOKUP_TABLES.items():
                    schema = LookupTableManagerWindow.lookup_table_schemas.get(config['table'])
                    if schema:
                        db_col = schema['columns'][config['column']]['db_column']
                        cur.execute(f'SELECT DISTINCT "{db_col}" FROM {config["table"]} ORDER BY "{db_col}"')
                        self.filter_combobox_data[field] = [row[0] for row in cur.fetchall()]
        finally:
            if conn: conn.close()

    def create_view_ui(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)

        # ... (criação do frame de filtro é a mesma)
        filter_frame = tb.LabelFrame(main_frame, text=self.get_string('filter_section'), bootstyle="info", padding=10)
        filter_frame.pack(fill="x", pady=(0, 10))
        # (código dos widgets do filtro aqui, sem alterações)
        tb.Label(filter_frame, text=self.get_string('date_start_label') + ":").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.filter_fields['data_inicio'] = DateEntry(filter_frame, bootstyle="info", dateformat="%d/%m/%Y")
        self.filter_fields['data_inicio'].grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tb.Label(filter_frame, text=self.get_string('col_wo') + ":").grid(row=0, column=2, padx=(20, 5), pady=2, sticky="w")
        self.filter_fields['wo'] = tb.Entry(filter_frame)
        self.filter_fields['wo'].grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        tb.Label(filter_frame, text=self.get_string('date_end_label') + ":").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.filter_fields['data_fim'] = DateEntry(filter_frame, bootstyle="info", dateformat="%d/%m/%Y")
        self.filter_fields['data_fim'].grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        tb.Label(filter_frame, text=self.get_string('printer_label') + ":").grid(row=1, column=2, padx=(20, 5), pady=2, sticky="w")
        self.filter_fields['impressor'] = tb.Combobox(filter_frame, values=self.filter_combobox_data.get('impressor', []), state="readonly")
        self.filter_fields['impressor'].grid(row=1, column=3, padx=5, pady=2, sticky="ew")
        tb.Label(filter_frame, text=self.get_string('equipment_label') + ":").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.filter_fields['equipamento'] = tb.Combobox(filter_frame, values=self.filter_combobox_data.get('equipamento', []), state="readonly")
        self.filter_fields['equipamento'].grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        tb.Label(filter_frame, text=self.get_string('shift_label') + ":").grid(row=2, column=2, padx=(20, 5), pady=2, sticky="w")
        self.filter_fields['turno'] = tb.Combobox(filter_frame, values=self.filter_combobox_data.get('turno', []), state="readonly")
        self.filter_fields['turno'].grid(row=2, column=3, padx=5, pady=2, sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)

        # Botões de ação
        action_frame = tb.Frame(main_frame)
        action_frame.pack(fill="x", pady=(5, 10))
        tb.Button(action_frame, text=self.get_string('apply_filters_btn'), bootstyle="primary", command=self.apply_filters).pack(side="left", padx=5)
        tb.Button(action_frame, text=self.get_string('clear_filters_btn'), bootstyle="secondary", command=self.clear_filters).pack(side="left", padx=5)
        
        # Botões para Superusuário
        if self.is_superuser:
            self.edit_btn = tb.Button(action_frame, text=self.get_string('edit_appointment_btn'), bootstyle="info-outline", command=self.open_edit_window, state="disabled")
            self.edit_btn.pack(side="left", padx=(20, 5))
            self.delete_btn = tb.Button(action_frame, text=self.get_string('delete_appointment_btn'), bootstyle="danger-outline", command=self.delete_appointment, state="disabled")
            self.delete_btn.pack(side="left", padx=5)

        # Botões do lado direito
        tb.Button(action_frame, text=self.get_string('export_csv_btn'), bootstyle="success-outline", command=self.export_to_csv).pack(side="right", padx=5)
        self.view_stops_details_btn = tb.Button(action_frame, text=self.get_string('view_stop_details_btn'), bootstyle="warning-outline", command=self.view_selected_appointment_stops, state="disabled")
        self.view_stops_details_btn.pack(side="right", padx=5)
        
        # Treeview
        # ... (criação do treeview é a mesma)
        self.tree_frame = tb.Frame(main_frame)
        self.tree_frame.pack(fill="both", expand=True)
        self.treeview = tb.Treeview(self.tree_frame, columns=[], show="headings", bootstyle="primary", selectmode="browse")
        self.treeview.pack(side="left", fill="both", expand=True)
        ys = tb.Scrollbar(self.tree_frame, orient="vertical", command=self.treeview.yview)
        ys.pack(side="right", fill="y")
        self.treeview.configure(yscrollcommand=ys.set)
        xs = tb.Scrollbar(main_frame, orient="horizontal", command=self.treeview.xview)
        xs.pack(fill="x")
        self.treeview.configure(xscrollcommand=xs.set)

        db_cols = [c["db_column"] for c in self.APPOINTMENT_COLUMNS_SCHEMA.values()]
        headers = [self.get_string(c["display_key"]) for c in self.APPOINTMENT_COLUMNS_SCHEMA.values()]

        self.treeview.config(columns=db_cols)
        for db_col, header in zip(db_cols, headers):
            w = 120
            if db_col == "id": w = 50
            elif db_col == "ocorrencias": w = 250
            elif db_col in ["wo", "cliente", "impressor", "numeroinspecao"]: w = 150
            self.treeview.column(db_col, width=w, anchor=W if w > 120 else CENTER)
            self.treeview.heading(db_col, text=header)

        self.treeview.bind("<<TreeviewSelect>>", self.on_item_select)
    
    def on_item_select(self, event=None):
        is_selected = bool(self.treeview.selection())
        self.view_stops_details_btn.config(state="normal" if is_selected else "disabled")
        if self.is_superuser:
            self.edit_btn.config(state="normal" if is_selected else "disabled")
            self.delete_btn.config(state="normal" if is_selected else "disabled")

    # ... (o resto da classe, com as novas funções open_edit_window e delete_appointment)
    def apply_filters(self):
        filters = {}
        try:
            start_date, end_date = self.filter_fields['data_inicio'].entry.get(), self.filter_fields['data_fim'].entry.get()
            if start_date: filters['data_inicio'] = datetime.strptime(start_date, "%d/%m/%Y").date()
            if end_date: filters['data_fim'] = datetime.strptime(end_date, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showwarning(self.get_string('filter_section'), self.get_string('filter_date_format_warning', field="Data"))
            return
        for key in ['equipamento', 'wo', 'impressor', 'turno']:
            if val := self.filter_fields[key].get().strip(): filters[key] = val
        self.load_apontamentos_data(filters)

    def clear_filters(self):
        for field in self.filter_fields.values():
            if isinstance(field, DateEntry): field.entry.delete(0, END)
            else: field.set("") if isinstance(field, tb.Combobox) else field.delete(0, END)
        self.load_apontamentos_data()

    def load_apontamentos_data(self, filters=None):
        conn = self.get_db_connection()
        if not conn: return
        for item in self.treeview.get_children(): self.treeview.delete(item)
        try:
            with conn.cursor() as cur:
                cols = [f'A."{c["db_column"]}"' for c in self.APPOINTMENT_COLUMNS_SCHEMA.values() if c["db_column"] != "possui_paradas"]
                base_q = f'SELECT {", ".join(cols)}, (SELECT COUNT(P.id) > 0 FROM paradas P WHERE P.apontamento_id = A.id) AS possui_paradas FROM {self.apontamento_table_name} A'
                where, params = [], []
                if filters:
                    for key, val in filters.items():
                        op = ">=" if key == 'data_inicio' else "<=" if key == 'data_fim' else "ILIKE" if key == 'wo' else "="
                        where.append(f'A."{key}" {op} %s')
                        params.append(f"%{val}%" if op == "ILIKE" else val)
                query = base_q + (f" WHERE {' AND '.join(where)}" if where else "") + ' ORDER BY A."data" DESC, A."horainicio" DESC'
                cur.execute(query, tuple(params))
                col_map = {desc[0]: i for i, desc in enumerate(cur.description)}
                for row in cur.fetchall():
                    values = []
                    for cfg in self.APPOINTMENT_COLUMNS_SCHEMA.values():
                        val = row[col_map[cfg["db_column"]]]
                        if cfg["type"] == "date" and val: values.append(val.strftime("%d/%m/%Y"))
                        elif cfg["type"] == "time" and val: values.append(val.strftime("%H:%M"))
                        elif cfg["type"] == "bool": values.append(self.get_string('yes_short') if val else self.get_string('no_short'))
                        else: values.append(val if val is not None else "")
                    self.treeview.insert("", END, values=values)
        except psycopg2.Error as e:
            messagebox.showerror(self.get_string('view_appointments_title'), self.get_string('db_load_appointments_failed', table_name=self.apontamento_table_name, error=e))
        finally:
            self.on_item_select() # Garante que os botões fiquem desabilitados após recarregar
            if conn: conn.close()
    
    def open_edit_window(self):
        selected_item = self.treeview.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('edit_appointment_btn'), self.get_string('select_appointment_to_edit'))
            return
        
        item_values = self.treeview.item(selected_item, 'values')
        app_id = item_values[0] # ID é a primeira coluna
        EditAppointmentWindow(self, self.db_config, app_id, self.master.form_fields_config, self.load_apontamentos_data)

    def delete_appointment(self):
        selected_item = self.treeview.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('delete_appointment_btn'), self.get_string('select_appointment_to_delete'))
            return

        item_values = self.treeview.item(selected_item, 'values')
        app_id = item_values[0]

        if not messagebox.askyesno(self.get_string('confirm_delete_appointment_title'), self.get_string('confirm_delete_appointment_msg', id=app_id)):
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {self.apontamento_table_name} WHERE id = %s", (app_id,))
            conn.commit()
            messagebox.showinfo(self.get_string('delete_appointment_btn'), self.get_string('delete_appointment_success', id=app_id))
            self.load_apontamentos_data()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror(self.get_string('delete_appointment_btn'), self.get_string('delete_appointment_failed', error=e))
        finally:
            if conn: conn.close()

    def view_selected_appointment_stops(self):
        # ... (código desta função continua o mesmo da versão anterior)
        selected = self.treeview.focus()
        if not selected: return
        values = self.treeview.item(selected, 'values')
        schema_keys = [c['db_column'] for c in self.APPOINTMENT_COLUMNS_SCHEMA.values()]
        app_id = values[schema_keys.index('id')]
        has_stops = values[schema_keys.index('possui_paradas')]
        if has_stops == self.get_string('no_short'):
            messagebox.showinfo(self.get_string('view_stop_details_btn'), self.get_string('no_stops_for_appointment'))
            return
        self._open_stop_details_window(app_id)

    def _open_stop_details_window(self, app_id):
        # ... (código desta função continua o mesmo da versão anterior)
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT mpt.codigo, mpt.descricao, p.hora_inicio_parada, p.hora_fim_parada, p.motivo_extra_detail
                    FROM paradas p JOIN motivos_parada_tipos mpt ON p.motivo_id = mpt.id
                    WHERE p.apontamento_id = %s ORDER BY p.hora_inicio_parada;
                """
                cur.execute(query, (app_id,))
                stop_details = cur.fetchall()
        except psycopg2.Error as e:
            messagebox.showerror(self.get_string('view_stop_details_btn'), self.get_string('db_load_stops_failed', error=e))
            return
        finally:
            if conn: conn.close()
        win = Toplevel(self)
        win.title(self.get_string('stop_details_for_appointment', id=app_id))
        win.transient(self)
        win.grab_set()
        if not stop_details:
            tb.Label(win, text=self.get_string('no_stops_for_appointment_full')).pack(padx=20, pady=20)
            return
        tree = tb.Treeview(win, columns=("motivo", "extra", "inicio", "fim"), show="headings", bootstyle="info", padding=15)
        tree.heading("motivo", text=self.get_string('col_motivos_parada'))
        tree.heading("extra", text=self.get_string('other_motives_label'))
        tree.heading("inicio", text=self.get_string('col_horainicio'))
        tree.heading("fim", text=self.get_string('col_horafim'))
        for code, desc, start, end, extra in stop_details:
            motivo = f"{code} - {desc}" if code else desc
            start_fmt = start.strftime("%H:%M") if start else ""
            end_fmt = end.strftime("%H:%M") if end else ""
            tree.insert("", END, values=(motivo, extra or "", start_fmt, end_fmt))
        tree.pack(fill="both", expand=True)
        win.update_idletasks()
        win.geometry(f"+{self.winfo_x() + 50}+{self.winfo_y() + 50}")
    
    def export_to_csv(self):
        # ... (código desta função continua o mesmo da versão anterior)
        if not self.treeview.get_children():
            messagebox.showwarning(self.get_string('export_csv_btn'), self.get_string('no_data_to_export'))
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[(self.get_string('csv_files_type'), "*.csv"), (self.get_string('all_files_type'), "*.*")], title=self.get_string('save_csv_dialog_title'))
        if not file_path: return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow([self.treeview.heading(c)["text"] for c in self.treeview["columns"]])
                for item in self.treeview.get_children():
                    writer.writerow(self.treeview.item(item, 'values'))
            messagebox.showinfo(self.get_string('export_csv_btn'), self.get_string('export_success_message', path=file_path))
        except Exception as e:
            messagebox.showerror(self.get_string('export_csv_btn'), self.get_string('export_error', error=e))

# ==============================================================================
# 5. EDIT APPOINTMENT WINDOW CLASS
# (NOVA CLASSE para a funcionalidade de Edição)
# ==============================================================================
class EditAppointmentWindow(Toplevel):
    def __init__(self, master, db_config, appointment_id, form_fields_config, refresh_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.appointment_id = appointment_id
        self.form_fields_config = form_fields_config
        self.refresh_callback = refresh_callback
        self.fields = {}
        self.validation_labels = {}
        self.stop_times_data = []

        self.title(self.get_string('edit_appointment_title', id=self.appointment_id))
        self.create_form()
        self.load_and_populate_data()
        self.grab_set()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def get_db_connection(self):
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except Exception:
            return None

    def create_form(self):
        # Reutiliza a lógica de criação de formulário da classe App
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        # ... (código de create_form da classe App, adaptado para self)
        canvas = tb.Canvas(main_frame)
        scrollbar = tb.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tb.Frame(canvas, padding=10)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        input_frame = tb.LabelFrame(scroll_frame, text=self.get_string('form_data_section'), bootstyle="primary", padding=15)
        input_frame.grid(row=0, column=0, sticky="ew")
        fields = list(self.form_fields_config.items())
        per_col = (len(fields) + 1) // 2
        for i, (label_key, cfg) in enumerate(fields):
            row, col_offset = (i, 0) if i < per_col else (i - per_col, 3)
            db_col = cfg["db_column"]
            tb.Label(input_frame, text=self.get_string(cfg["display_key"]) + ":").grid(row=row, column=col_offset, sticky="w", padx=10, pady=5)
            if cfg["widget_type"] == "DateEntry":
                widget = DateEntry(input_frame, bootstyle="info", dateformat="%d/%m/%Y")
            elif cfg["widget_type"] == "Combobox":
                widget = tb.Combobox(input_frame, values=cfg.get("values", []), state="readonly")
            elif cfg["widget_type"] == "Text":
                widget = tb.Text(input_frame, height=cfg.get("height", 4), width=cfg.get("width", 50))
            else:
                widget = tb.Entry(input_frame)
            widget.grid(row=row, column=col_offset + 1, padx=10, pady=5, sticky="ew")
            self.fields[db_col] = widget
            v_label = tb.Label(input_frame, text="", bootstyle="danger", font="Helvetica 9 italic")
            v_label.grid(row=row, column=col_offset + 2, sticky="w", padx=5)
            self.validation_labels[db_col] = v_label
        row = per_col
        self.has_stops_var = tb.BooleanVar()
        tb.Checkbutton(input_frame, text=self.get_string('has_stops_question'), variable=self.has_stops_var, bootstyle="round-toggle", command=self.toggle_stop_times_button).grid(row=row, column=0, sticky="w", padx=10, pady=10)
        self.open_stop_times_btn = tb.Button(input_frame, text=self.get_string('open_stop_times_btn'), bootstyle="info-outline", command=self.open_stop_times_window, state="disabled")
        self.open_stop_times_btn.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(4, weight=1)
        btn_frame = tb.Frame(scroll_frame)
        btn_frame.grid(row=1, column=0, pady=20, sticky="ew")
        tb.Button(btn_frame, text=self.get_string('save_changes_btn'), bootstyle="success", command=self.save_changes).pack(expand=True, fill="x")

    def load_and_populate_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # Carregar dados do apontamento principal
                cols = [f'"{c["db_column"]}"' for c in self.form_fields_config.values()]
                cur.execute(f"SELECT {', '.join(cols)} FROM {self.db_config['tabela']} WHERE id = %s", (self.appointment_id,))
                data = cur.fetchone()
                col_names = [c['db_column'] for c in self.form_fields_config.values()]
                data_dict = dict(zip(col_names, data))

                # Popular o formulário
                for db_col, widget in self.fields.items():
                    val = data_dict.get(db_col)
                    if val is None: continue
                    if isinstance(widget, DateEntry):
                        widget.entry.delete(0, END)
                        widget.entry.insert(0, val.strftime("%d/%m/%Y"))
                    elif isinstance(widget, tb.Text):
                        widget.insert("1.0", val)
                    elif isinstance(widget, tb.Combobox):
                        widget.set(val)
                    else: # Entry
                        widget.insert(0, val.strftime("%H:%M") if isinstance(val, time) else val)

                # Carregar dados das paradas
                cur.execute("SELECT motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail FROM paradas WHERE apontamento_id = %s", (self.appointment_id,))
                self.stop_times_data = [{"motivo_id": r[0], "hora_inicio_parada": r[1], "hora_fim_parada": r[2], "motivo_extra_detail": r[3]} for r in cur.fetchall()]
                if self.stop_times_data:
                    self.has_stops_var.set(True)
                    self.toggle_stop_times_button()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados para edição: {e}")
            self.destroy()
        finally:
            if conn: conn.close()

    def save_changes(self):
        # Validação (simplificada, pode reusar a da App)
        data = {db_col: w.get("1.0", "end-1c") if isinstance(w, tb.Text) else (w.entry.get() if isinstance(w, DateEntry) else w.get()) for db_col, w in self.fields.items()}
        for k, v in data.items(): data[k] = v.strip()
        # (Lógica de validação completa aqui)

        # Processar dados
        p_data = {}
        for db_col, val in data.items():
            cfg = next(c for c in self.form_fields_config.values() if c["db_column"] == db_col)
            v_type = cfg.get("validation_type")
            if not val or (v_type == "time" and val == "HH:MM"): p_data[db_col] = None
            elif v_type == "int": p_data[db_col] = int(val)
            elif v_type == "date": p_data[db_col] = datetime.strptime(val, "%d/%m/%Y").date()
            elif v_type == "time": p_data[db_col] = datetime.strptime(val, "%H:%M").time()
            else: p_data[db_col] = val

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # Atualizar apontamento principal
                set_clauses = [f'"{col}" = %s' for col in p_data.keys()]
                values = list(p_data.values()) + [self.appointment_id]
                query = f"UPDATE {self.db_config['tabela']} SET {', '.join(set_clauses)} WHERE id = %s"
                cur.execute(query, values)
                
                # Atualizar paradas (deletar antigas e inserir novas)
                cur.execute("DELETE FROM paradas WHERE apontamento_id = %s", (self.appointment_id,))
                if self.has_stops_var.get() and self.stop_times_data:
                    for stop in self.stop_times_data:
                        stop_q = "INSERT INTO paradas (apontamento_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s);"
                        cur.execute(stop_q, (self.appointment_id, stop['motivo_id'], stop['hora_inicio_parada'], stop['hora_fim_parada'], stop['motivo_extra_detail']))
            
            conn.commit()
            messagebox.showinfo(self.get_string('save_changes_btn'), self.get_string('update_success', id=self.appointment_id))
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror(self.get_string('save_changes_btn'), self.get_string('update_failed', error=e))
        finally:
            if conn: conn.close()

    def toggle_stop_times_button(self):
        self.open_stop_times_btn.config(state="normal" if self.has_stops_var.get() else "disabled")
        if not self.has_stops_var.get(): self.stop_times_data = []
    
    def open_stop_times_window(self):
        StopTimesWindow(self, self.db_config, initial_stop_data=self.stop_times_data)

# ==============================================================================
# 6. MAIN APP CLASS
# (Unchanged, provided for completeness)
# ==============================================================================
class App(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.current_language = 'portugues'
        self.db_config = {}
        self.load_db_config()
        self.current_language = self.db_config.get('language', 'portugues')
        self.set_localized_title()
        self.stop_times_data = []
        self.form_fields_config = {
            "Data": {"db_column": "data", "widget_type": "DateEntry", "validation_type": "date", "display_key": "col_data"},
            "Hora Início": {"db_column": "horainicio", "widget_type": "Entry", "validation_type": "time", "display_key": "col_horainicio"},
            "Hora Fim": {"db_column": "horafim", "widget_type": "Entry", "validation_type": "time", "display_key": "col_horafim"},
            "Equipamento": {"db_column": "equipamento", "widget_type": "Combobox", "values": [], "display_key": "equipment_label", "lookup_table_ref": "equipamentos_tipos"},
            "WO": {"db_column": "wo", "widget_type": "Entry", "validation_type": "string", "display_key": "col_wo"},
            "Cliente": {"db_column": "cliente", "widget_type": "Entry", "validation_type": "string", "display_key": "col_cliente"},
            "QTDE CORES": {"db_column": "qtde_cores", "widget_type": "Combobox", "values": [], "display_key": "col_qtde_cores", "lookup_table_ref": "qtde_cores_tipos"},
            "TIPO PAPEL": {"db_column": "tipo_papel", "widget_type": "Combobox", "values": [], "display_key": "col_tipo_papel", "lookup_table_ref": "tipos_papel"},
            "Numero Inspeção": {"db_column": "numeroinspecao", "widget_type": "Entry", "validation_type": "string", "display_key": "col_numeroinspecao"},
            "Gramatura": {"db_column": "gramatura", "widget_type": "Combobox", "values": [], "validation_type": "int", "display_key": "col_gramatura", "lookup_table_ref": "gramaturas_tipos"},
            "Formato": {"db_column": "formato", "widget_type": "Combobox", "values": [], "validation_type": "string", "display_key": "col_formato", "lookup_table_ref": "formatos_tipos"},
            "FSC": {"db_column": "fsc", "widget_type": "Combobox", "values": [], "display_key": "col_fsc", "lookup_table_ref": "fsc_tipos"},
            "Tiragem em folhas": {"db_column": "tiragem_em_folhas", "widget_type": "Entry", "validation_type": "int", "display_key": "col_tiragem_em_folhas"},
            "Giros Rodados": {"db_column": "giros_rodados", "widget_type": "Entry", "validation_type": "int", "display_key": "col_giros_rodados"},
            "Perdas/ Malas": {"db_column": "perdas_malas", "widget_type": "Entry", "validation_type": "int", "display_key": "col_perdas_malas"},
            "Total Lavagens": {"db_column": "total_lavagens", "widget_type": "Entry", "validation_type": "int", "display_key": "col_total_lavagens"},
            "Total Acertos": {"db_column": "total_acertos", "widget_type": "Entry", "validation_type": "int", "display_key": "col_total_acertos"},
            "Impressor": {"db_column": "impressor", "widget_type": "Combobox", "values": [], "display_key": "printer_label", "lookup_table_ref": "impressores"},
            "Ocorrências": {"db_column": "ocorrencias", "widget_type": "Text", "height": 4, "width": 50, "display_key": "col_ocorrencias"},
            "Turno": {"db_column": "turno", "widget_type": "Combobox", "values": [], "display_key": "shift_label", "lookup_table_ref": "turnos_tipos"},
            "Quantidade Produzida": {"db_column": "quantidadeproduzida", "widget_type": "Entry", "validation_type": "int", "display_key": "col_quantidadeproduzida"}
        }
        self.fields, self.validation_labels, self.combobox_data = {}, {}, {}
        self.create_menu()
        self.create_form()
        self.load_combobox_data()
        self.update_idletasks()
        w, h = 950, 700
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def get_string(self, key, **kwargs): return LANGUAGES.get(self.current_language, LANGUAGES['portugues']).get(key, key).format(**kwargs)
    
    def set_localized_title(self): self.title(f"{self.get_string('app_title')} - REV07")
    
    def load_db_config(self):
        if os.path.exists('db_config.json'):
            try:
                with open('db_config.json', 'r') as f: self.db_config = json.load(f)
            except Exception: self.db_config = {}
            
    def save_db_config(self):
        try:
            with open('db_config.json', 'w') as f: json.dump(self.db_config, f, indent=4)
            messagebox.showinfo(self.get_string('save_btn'), self.get_string('config_save_success'))
        except Exception as e:
            messagebox.showerror(self.get_string('save_btn'), self.get_string('config_save_error', error=e))
            
    def create_menu(self):
        if hasattr(self, 'menubar'): self.menubar.destroy()
        self.menubar = tb.Menu(self)
        config_menu = tb.Menu(self.menubar, tearoff=0)
        config_menu.add_command(label=self.get_string('menu_db_config'), command=self.configure_db_window)
        self.menubar.add_cascade(label=self.get_string('menu_settings'), menu=config_menu)
        manage_menu = tb.Menu(self.menubar, tearoff=0)
        manage_menu.add_command(label=self.get_string('menu_manage_lookup'), command=lambda: LookupTableManagerWindow(self, self.db_config, self.load_combobox_data))
        manage_menu.add_command(label=self.get_string('menu_view_appointments'), command=lambda: ViewAppointmentsWindow(self, self.db_config))
        self.menubar.add_cascade(label=self.get_string('menu_manage'), menu=manage_menu)
        self.config(menu=self.menubar)
        
    def configure_db_window(self):
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
        tb.Button(btn_frame, text=self.get_string('test_connection_btn'), bootstyle="info-outline", command=lambda: self.test_db_connection(entries)).pack(side="left", padx=5)
        tb.Button(btn_frame, text=self.get_string('save_btn'), bootstyle="success", command=lambda: self.save_and_close_config(entries, lang_selector, win)).pack(side="left", padx=5)

    def save_and_close_config(self, entries, lang_selector, win):
        new_config = {k: v.get() for k, v in entries.items()}
        new_lang = lang_selector.get().lower()
        new_config['language'] = new_lang
        self.db_config = new_config
        self.save_db_config()
        if self.current_language != new_lang:
            self.current_language = new_lang
            self.recreate_all_ui_widgets()
        self.load_combobox_data()
        win.destroy()

    def recreate_all_ui_widgets(self):
        for widget in self.winfo_children():
            if isinstance(widget, (tb.Frame, tb.Canvas)): widget.destroy()
        self.set_localized_title()
        self.fields, self.validation_labels = {}, {}
        self.create_menu()
        self.create_form()

    # ##### FUNÇÃO CORRIGIDA #####
    def _get_connection_params(self, config_dict):
        """Mapeia as chaves do dicionário de configuração para as chaves do psycopg2."""
        return {
            'host': config_dict.get('host'),
            'port': config_dict.get('porta'),
            'dbname': config_dict.get('banco'),
            'user': config_dict.get('usuário'),
            'password': config_dict.get('senha')
        }

    # ##### FUNÇÃO CORRIGIDA #####
    def test_db_connection(self, entries):
        test_config = {k: v.get() for k, v in entries.items()}
        if not all(test_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            messagebox.showwarning(self.get_string('test_connection_btn'), self.get_string('test_connection_warning_fill_fields'))
            return
        
        conn_params = get_connection_params(test_config)
        
        try:
            with psycopg2.connect(**conn_params):
                messagebox.showinfo(self.get_string('test_connection_btn'), self.get_string('test_connection_success'))
        except Exception as e:
            messagebox.showerror(self.get_string('test_connection_btn'), self.get_string('test_connection_failed_db', error=e))

    # ##### FUNÇÃO CORRIGIDA #####
    def get_db_connection(self):
        if not all(self.db_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            return None
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except Exception:
            return None

    def load_combobox_data(self):
        defaults = {cfg['db_column']: [] for cfg in self.form_fields_config.values() if cfg['widget_type'] == 'Combobox'}
        self.update_comboboxes(defaults)
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                for cfg in self.form_fields_config.values():
                    if cfg.get("widget_type") == "Combobox" and "lookup_table_ref" in cfg:
                        schema = LookupTableManagerWindow.lookup_table_schemas.get(cfg["lookup_table_ref"])
                        if schema:
                            col = next((c['db_column'] for c in schema['columns'].values() if c['editable']), None)
                            if col:
                                cur.execute(f'SELECT DISTINCT "{col}" FROM {schema["table"]} ORDER BY "{col}"')
                                self.combobox_data[cfg['db_column']] = [row[0] for row in cur.fetchall()]
            self.update_comboboxes(self.combobox_data)
        except Exception as e:
            messagebox.showwarning("Erro", f"Falha ao carregar dados de lookup: {e}")
        finally:
            if conn: conn.close()

    def update_comboboxes(self, data):
        for cfg in self.form_fields_config.values():
            if cfg.get("widget_type") == "Combobox":
                db_col = cfg["db_column"]
                new_vals = data.get(db_col, [])
                cfg["values"] = new_vals
                if db_col in self.fields:
                    widget = self.fields[db_col]
                    current = widget.get()
                    widget['values'] = new_vals
                    widget.set(current if current in new_vals else "")
                    
    # ... (O resto da classe App e as outras classes permanecem iguais)
    def create_form(self):
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        canvas = tb.Canvas(main_frame)
        scrollbar = tb.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tb.Frame(canvas, padding=10)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        input_frame = tb.LabelFrame(scroll_frame, text=self.get_string('form_data_section'), bootstyle="primary", padding=15)
        input_frame.grid(row=0, column=0, sticky="ew")
        fields = list(self.form_fields_config.items())
        per_col = (len(fields) + 1) // 2
        for i, (label_key, cfg) in enumerate(fields):
            row, col_offset = (i, 0) if i < per_col else (i - per_col, 3)
            db_col = cfg["db_column"]
            tb.Label(input_frame, text=self.get_string(cfg["display_key"]) + ":").grid(row=row, column=col_offset, sticky="w", padx=10, pady=5)
            if cfg["widget_type"] == "DateEntry":
                widget = DateEntry(input_frame, bootstyle="info", dateformat="%d/%m/%Y")
                widget.entry.insert(0, datetime.now().strftime("%d/%m/%Y"))
            elif cfg["widget_type"] == "Combobox":
                widget = tb.Combobox(input_frame, values=cfg.get("values", []), state="readonly")
            elif cfg["widget_type"] == "Text":
                widget = tb.Text(input_frame, height=cfg.get("height", 4), width=cfg.get("width", 50))
            else:
                widget = tb.Entry(input_frame)
                if cfg["validation_type"] == "time":
                    widget.insert(0, "HH:MM")
                    widget.bind("<FocusIn>", lambda e, w=widget: self.clear_placeholder(w, "HH:MM"))
                    widget.bind("<FocusOut>", lambda e, w=widget: self.restore_placeholder(w, "HH:MM"))
            widget.grid(row=row, column=col_offset + 1, padx=10, pady=5, sticky="ew")
            self.fields[db_col] = widget
            v_label = tb.Label(input_frame, text="", bootstyle="danger", font="Helvetica 9 italic")
            v_label.grid(row=row, column=col_offset + 2, sticky="w", padx=5)
            self.validation_labels[db_col] = v_label
        row = per_col
        self.has_stops_var = tb.BooleanVar(value=False)
        tb.Checkbutton(input_frame, text=self.get_string('has_stops_question'), variable=self.has_stops_var, bootstyle="round-toggle", command=self.toggle_stop_times_button).grid(row=row, column=0, sticky="w", padx=10, pady=10)
        self.open_stop_times_btn = tb.Button(input_frame, text=self.get_string('open_stop_times_btn'), bootstyle="info-outline", command=self.open_stop_times_window, state="disabled")
        self.open_stop_times_btn.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(4, weight=1)
        btn_frame = tb.Frame(scroll_frame)
        btn_frame.grid(row=1, column=0, pady=20, sticky="ew")
        tb.Button(btn_frame, text=self.get_string('submit_btn'), bootstyle="success-outline", command=self.submit).pack(side="left", padx=10, expand=True, fill="x")
        tb.Button(btn_frame, text=self.get_string('clear_form_btn'), bootstyle="warning-outline", command=self.clear_form).pack(side="left", padx=10, expand=True, fill="x")
    def toggle_stop_times_button(self):
        self.open_stop_times_btn.config(state="normal" if self.has_stops_var.get() else "disabled")
        if not self.has_stops_var.get(): self.stop_times_data = []
    def open_stop_times_window(self): StopTimesWindow(self, self.db_config, initial_stop_data=self.stop_times_data)
    def clear_placeholder(self, w, p):
        if w.get() == p: w.delete(0, END)
    def restore_placeholder(self, w, p):
        if not w.get(): w.insert(0, p)
    def clear_form(self):
        for db_col, widget in self.fields.items():
            if isinstance(widget, (tb.Entry, DateEntry)):
                w = widget.entry if isinstance(widget, DateEntry) else widget
                w.delete(0, END)
                cfg = self.form_fields_config.get(next(k for k,v in self.form_fields_config.items() if v['db_column']==db_col))
                if cfg["validation_type"] == "time": w.insert(0, "HH:MM")
                elif cfg["widget_type"] == "DateEntry": w.insert(0, datetime.now().strftime("%d/%m/%Y"))
            elif isinstance(widget, tb.Text): widget.delete("1.0", END)
            elif isinstance(widget, tb.Combobox): widget.set("")
            self.validation_labels[db_col].config(text="")
        self.has_stops_var.set(False)
        self.toggle_stop_times_button()
    def validate_input(self, data):
        is_valid = True
        for db_col, val in data.items():
            cfg = next(c for c in self.form_fields_config.values() if c["db_column"] == db_col)
            self.validation_labels[db_col].config(text="")
            if cfg['db_column'] not in ['numeroinspecao', 'ocorrencias'] and not val:
                self.validation_labels[db_col].config(text=self.get_string('validation_error_required'))
                is_valid = False
            if val:
                v_type = cfg.get("validation_type")
                try:
                    if v_type == "date": datetime.strptime(val, "%d/%m/%Y")
                    elif v_type == "time" and val != "HH:MM": datetime.strptime(val, "%H:%M")
                    elif v_type == "int": int(val)
                except (ValueError, TypeError):
                    self.validation_labels[db_col].config(text=self.get_string(f'validation_error_{v_type}_format'))
                    is_valid = False
        return is_valid
    def submit(self):
        if not self.db_config.get('tabela'):
            messagebox.showerror(self.get_string('submit_btn'), self.get_string('db_config_missing'))
            return
        data = {db_col: w.get("1.0", "end-1c") if isinstance(w, tb.Text) else (w.entry.get() if isinstance(w, DateEntry) else w.get()) for db_col, w in self.fields.items()}
        for k, v in data.items(): data[k] = v.strip()
        if not self.validate_input(data):
            messagebox.showerror(self.get_string('validation_error_fix_fields'), self.get_string('validation_error_fix_fields'))
            return
        p_data = {}
        for db_col, val in data.items():
            cfg = next(c for c in self.form_fields_config.values() if c["db_column"] == db_col)
            v_type = cfg.get("validation_type")
            if not val or (v_type == "time" and val == "HH:MM"): p_data[db_col] = None
            elif v_type == "int": p_data[db_col] = int(val)
            elif v_type == "date": p_data[db_col] = datetime.strptime(val, "%d/%m/%Y").date()
            elif v_type == "time": p_data[db_col] = datetime.strptime(val, "%H:%M").time()
            else: p_data[db_col] = val
        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                messagebox.showerror(self.get_string('submit_btn'), self.get_string('db_conn_incomplete'))
                return
            with conn.cursor() as cur:
                cols = [cfg['db_column'] for cfg in self.form_fields_config.values()]
                q_cols = ', '.join([f'"{c}"' for c in cols])
                placeholders = ', '.join(['%s'] * len(cols))
                cur.execute(f"INSERT INTO {self.db_config['tabela']} ({q_cols}) VALUES ({placeholders}) RETURNING id;", [p_data.get(c) for c in cols])
                app_id = cur.fetchone()[0]
                if self.has_stops_var.get() and self.stop_times_data:
                    for stop in self.stop_times_data:
                        stop_q = "INSERT INTO paradas (apontamento_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s);"
                        cur.execute(stop_q, (app_id, stop['motivo_id'], stop['hora_inicio_parada'], stop['hora_fim_parada'], stop['motivo_extra_detail']))
            conn.commit()
            messagebox.showinfo(self.get_string('submit_btn'), self.get_string('db_send_success'))
            self.clear_form()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror(self.get_string('submit_btn'), self.get_string('db_send_failed', error=e))
        finally:
            if conn: conn.close()

# ==============================================================================
# 7. SCRIPT EXECUTION
# ==============================================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
