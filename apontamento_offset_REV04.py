import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import messagebox, Toplevel, END, W, E, S, N, CENTER, filedialog, simpledialog
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
        # Títulos de Janelas e Abas
        'app_title': 'Sistema de Apontamento de Produção',
        'main_menu_title': 'Menu Principal - Sistema de Produção',
        'stop_tracking_window_title': 'Apontamento de Parada em Tempo Real',
        'config_win_title': 'Configurações do Banco de Dados',
        'manager_title': 'Gerenciador de Tabelas de Apoio',
        'edit_order_title': 'Editar Ordem de Produção - WO: {wo}',
        'confirm_cancel_order_title': 'Confirmar Cancelamento',
        'view_appointments_title': 'Visualizar Apontamentos',
        'stop_times_window_title': 'Apontamento de Paradas',
        'confirm_delete_appointment_title': 'Confirmar Exclusão de Apontamento',
        'edit_appointment_title': 'Editar Apontamento - ID: {id}',
        'stop_details_for_appointment': 'Detalhes das Paradas para Apontamento ID: {id}',
        'service_manager_title': 'Gerenciador de Etapas - WO: {wo}',
        'add_service_title': 'Adicionar Nova Etapa',
        'edit_service_title': 'Editar Etapa',

        # Botões
        'btn_production_entry': 'Apontamento de Produção',
        'btn_pcp_management': 'Gerenciamento PCP',
        'btn_view_entries': 'Visualizar Apontamentos',
        'btn_manage_tables': 'Gerenciar Tabelas de Apoio',
        'start_production_btn': 'Iniciar Produção',
        'finish_production_btn': 'Finalizar Produção',
        'register_entry_btn': 'Registar Apontamento Final',
        'finish_stop_btn': 'Finalizar Parada',
        'test_connection_btn': 'Testar Conexão',
        'save_btn': 'Salvar',
        'cancel_btn': 'Cancelar',
        'save_changes_btn': 'Salvar Alterações',
        'edit_order_btn': 'Alterar Ordem Selecionada',
        'cancel_order_btn': 'Cancelar Ordem Selecionada',
        'add_new_btn': 'Adicionar Novo',
        'edit_selected_btn': 'Editar Selecionado',
        'delete_selected_btn': 'Excluir Selecionado',
        'apply_filters_btn': 'Aplicar Filtros',
        'clear_filters_btn': 'Limpar Filtros',
        'export_csv_btn': 'Exportar para CSV',
        'open_stop_times_btn': 'Configurar Paradas',
        'generate_fields_btn': 'Gerar Campos',
        'view_stop_details_btn': 'Ver Detalhes das Paradas',
        'edit_appointment_btn': 'Editar Apontamento',
        'delete_appointment_btn': 'Excluir Apontamento',
        'btn_manage_services': 'Gerenciar Etapas',
        'add_service_btn': 'Adicionar Etapa',
        'edit_service_btn': 'Editar Etapa',
        'delete_service_btn': 'Excluir Etapa',

        # Labels e Textos de Interface
        'production_status_running': 'EM PRODUÇÃO',
        'production_status_stopped': 'PARADO',
        'production_status_idle': 'AGUARDANDO INÍCIO',
        'elapsed_time_label': 'Tempo Decorrido:',
        'stop_reason_label': 'Motivo da Parada:',
        'stop_time_label': 'Tempo de Parada:',
        'host_label': 'Host',
        'port_label': 'Porta',
        'user_label': 'Usuário',
        'password_label': 'Senha',
        'db_label': 'Banco',
        'table_label': 'Tabela de Apontamentos',
        'language_label': 'Idioma',
        'equipment_label': 'Equipamento',
        'printer_label': 'Impressor',
        'shift_label': 'Turno',
        'date_start_label': 'Data Início',
        'date_end_label': 'Data Fim',
        'has_stops_question': 'Possui Paradas?',
        'num_stops_label': 'Número de Paradas',
        'stop_label': 'Parada',
        'other_motives_label': 'Especifique o Motivo',
        'has_stops_question_short': 'Paradas?',
        'yes_short': 'Sim',
        'no_short': 'Não',
        'service_select_label': 'Selecionar Etapa/Serviço:',

        # Seções de Tela (LabelFrame)
        'form_data_section': 'Dados',
        'filter_section': 'Filtros de Apontamentos',
        'manager_select_table': 'Seleção de Tabela',
        'stop_times_control_section': 'Controle de Paradas',
        'new_order_section': "Nova Ordem de Produção",
        'created_orders_section': "Ordens de Produção Criadas",
        'services_section_title': 'Etapas da Ordem',

        # Colunas de Tabelas
        'col_id': 'ID', 'col_descricao': 'Descrição', 'col_nome': 'Nome', 'col_codigo': 'Código',
        'col_valor': 'Valor', 'col_data': 'Data', 'col_horainicio': 'Hora Início', 'col_horafim': 'Hora Fim',
        'col_wo': 'WO', 'col_cliente': 'Cliente', 'col_qtde_cores': 'QTDE CORES',
        'col_tipo_papel': 'TIPO PAPEL', 'col_numeroinspecao': 'Número Inspeção', 'col_gramatura': 'Gramatura',
        'col_formato': 'Formato', 'col_fsc': 'FSC', 'col_tiragem_em_folhas': 'Tiragem em Folhas',
        'col_giros_rodados': 'Giros Rodados', 'col_perdas_malas': 'Perdas/ Malas', 'col_total_lavagens': 'Total Lavagens',
        'col_total_acertos': 'Total Acertos', 'col_ocorrencias': 'Ocorrências',
        'col_motivos_parada': 'Motivo da Parada', 'col_quantidadeproduzida': 'Quantidade Produzida',
        'col_status': 'Status', 'col_data_criacao': 'Data Criação', 'col_duracao': 'Duração',
        'col_impressor': 'Impressor', 'col_turno': 'Turno', 'col_data_previsao': 'Data Previsão',
        'col_data_cadastro': 'Data Cadastro', 'col_servico_descricao': 'Descrição da Etapa',
        'col_servico_status': 'Status da Etapa', 'col_sequencia': 'Sequência',
        'col_perdas_producao': 'Perdas (Produção)',
        'col_motivo_perda': 'Motivo da Perda',


        # Menus
        'menu_settings': 'Configurações',
        'menu_db_config': 'Configurar Banco de Dados',
        'menu_manage': 'Gerenciar',
        'menu_manage_lookup': 'Gerenciar Tabelas de Apoio',
        'menu_view_appointments': 'Visualizar Apontamentos',
        'menu_manage_pcp': 'Gerenciar Ordens (PCP)',

        # Mensagens de Sucesso
        'cancel_order_success': 'Ordem de Produção cancelada com sucesso!',
        'update_order_success': 'Ordem de Produção atualizada com sucesso!',
        'loaded_appointments_success': 'Dados da tabela "{table_name}" carregados com sucesso!',
        'export_success_message': 'Dados exportados com sucesso para:\n{path}',
        'stop_times_saved_success': 'Dados de paradas salvos com sucesso!',
        'delete_appointment_success': 'Apontamento ID {id} excluído com sucesso!',
        'update_success': 'Apontamento ID {id} atualizado com sucesso!',
        'entry_edited_success': 'Entrada atualizada com sucesso!',
        'new_entry_added_success': 'Nova entrada adicionada com sucesso!',
        'delete_success': 'Entrada excluída com sucesso!',
        'config_save_success': 'Configuração salva com sucesso. Pode ser necessário reiniciar a aplicação.',
        'test_connection_success': 'Conexão com o banco de dados bem-sucedida!',
        'order_save_success': 'Ordem de produção salva com sucesso!',
        'service_saved_success': 'Etapa salva com sucesso!',
        'service_deleted_success': 'Etapa excluída com sucesso!',
        'production_saved_success': 'Apontamento de produção registrado com sucesso!',

        # Mensagens de Erro e Alerta
        'cancel_order_failed': 'Falha ao cancelar a Ordem de Produção: {error}',
        'update_order_failed': 'Falha ao atualizar a Ordem de Produção: {error}',
        'selection_required_title': 'Seleção Necessária',
        'select_order_to_edit_msg': 'Por favor, selecione uma ordem para alterar.',
        'select_order_to_cancel_msg': 'Por favor, selecione uma ordem para cancelar.',
        'invalid_status_for_action_msg': 'Ação não permitida! Apenas ordens com status "Em Aberto" podem ser alteradas ou canceladas.',
        'no_data_to_export': 'Não há dados para exportar.',
        'export_error': 'Erro ao exportar dados para CSV: {error}',
        'db_load_appointments_failed': 'Falha ao carregar apontamentos da tabela "{table_name}": {error}',
        'invalid_num_stops_error': 'Por favor, insira um número válido para a quantidade de paradas.',
        'validation_error_invalid_selection': 'Por favor, selecione um item válido.',
        'validation_error_time_order': 'Hora Fim deve ser posterior à Hora Início.',
        'validation_error_fix_fields_stops': 'Por favor, corrija os campos de parada destacados em vermelho.',
        'select_appointment_to_view_stops': 'Por favor, selecione um apontamento para ver os detalhes das paradas.',
        'no_stops_for_appointment': 'Este apontamento não possui paradas registradas.',
        'no_stops_for_appointment_full': 'Nenhuma parada registrada para este apontamento.',
        'db_load_stops_failed': 'Falha ao carregar detalhes das paradas: {error}',
        'db_conn_incomplete': 'Configuração do banco de dados incompleta ou ausente.',
        'invalid_input': 'Entrada Inválida',
        'filter_date_format_warning': 'Formato de data inválido para o campo "{field}". Use DD/MM/AAAA.',
        'delete_appointment_failed': 'Falha ao excluir apontamento: {error}',
        'select_appointment_to_edit': 'Selecione um apontamento para editar.',
        'select_appointment_to_delete': 'Selecione um apontamento para excluir.',
        'update_failed': 'Falha ao atualizar o apontamento: {error}',
        'select_table_warning': 'Por favor, selecione uma tabela para continuar.',
        'schema_not_found': 'Esquema para a tabela "{table_name}" não encontrado.',
        'db_load_table_failed': 'Falha ao carregar dados da tabela "{display_name}": {error}',
        'select_entry_to_edit': 'Por favor, selecione uma entrada para editar.',
        'save_entry_validation_error': 'Erro de validação para o campo "{field_name}". Insira um número inteiro válido.',
        'db_save_failed': 'Falha ao salvar no banco de dados. Erro: {error}',
        'db_delete_failed': 'Falha ao excluir do banco de dados. Erro: {error}',
        'config_save_error': 'Falha ao salvar o arquivo de configuração: {error}',
        'test_connection_warning_fill_fields': 'Por favor, preencha todos os campos de conexão para testar.',
        'test_connection_failed_db': 'Falha na conexão com o banco de dados: {error}',
        'required_field_warning': 'O campo "{field_name}" é obrigatório.',
        'integrity_error_wo': "A WO '{wo}' já existe.",
        'save_order_error': 'Não foi possível salvar a ordem. Verifique se os dados estão corretos.\nDetalhes: {error}',
        'empty_data_warning': "Nenhum dado para salvar.",
        'generic_load_error': 'Falha ao carregar dados: {error}',
        'service_save_failed': 'Falha ao salvar a etapa: {error}',
        'service_delete_failed': 'Falha ao excluir a etapa: {error}',
        'no_pending_services': 'Nenhuma etapa pendente para esta WO.',
        'select_wo_first': 'Selecione uma WO para ver as etapas.',
        'select_service_to_edit': 'Selecione uma etapa para editar.',
        'select_service_to_delete': 'Selecione uma etapa para excluir.',
        'production_save_failed': 'Falha ao salvar o apontamento de produção: {error}',
        'final_appointment_validation_error': 'Os campos "Giros Rodados" e "Quantidade Produzida" são obrigatórios.',

        
        # Mensagens de Confirmação
        'confirm_cancel_order_msg': 'Tem certeza que deseja cancelar permanentemente a ordem com WO "{wo}"? Esta ação não pode ser desfeita.',
        'confirm_delete_appointment_msg': 'Tem certeza que deseja excluir permanentemente o apontamento com ID {id}? Todas as paradas associadas também serão excluídas. Esta ação não pode ser desfeita.',
        'confirm_delete_title': 'Confirmar Exclusão',
        'confirm_delete_message': 'Tem certeza que deseja excluir permanentemente a entrada com ID "{pk_value}" da tabela "{display_name}"?',
        'confirm_delete_service_msg': 'Tem certeza que deseja excluir a etapa "{desc}"?',

        # Outros
        'csv_files_type': 'Arquivos CSV',
        'all_files_type': 'Todos os Arquivos',
        'save_csv_dialog_title': 'Salvar como CSV',

        'initial_selection_section': '1. Seleção Inicial',
        'setup_section': '2. Apontamento de Setup',
        'production_section': '3. Apontamento de Produção',
        'start_setup_btn': 'Iniciar Setup',
        'finish_setup_btn': 'Finalizar Setup',
        'point_setup_stop_btn': 'Apontar Parada de Setup',
        'point_prod_stop_btn': 'Apontar Parada de Produção',
        'col_perdas': 'Perdas (Setup)',
        'col_malas': 'Malas (Setup)',
        'status_idle': 'AGUARDANDO',
        'status_setup_running': 'SETUP EM ANDAMENTO',
        'status_setup_done': 'SETUP FINALIZADO',
        'status_prod_running': 'PRODUÇÃO EM ANDAMENTO',
        'setup_fields_required': 'Todos os campos de Setup (Perdas, Malas, Lavagens, Nº Inspeção) devem ser preenchidos para finalizar.',
        'setup_saved_success': 'Dados de Setup salvos com sucesso! Prossiga para a produção.',
        'setup_save_failed': 'Falha ao salvar os dados de Setup: {error}',
        'status_prod_done': 'PRODUÇÃO FINALIZADA',
        'finished': 'CONCLUÍDO',
    },
}

# ==============================================================================
# 2. FUNÇÕES E CLASSES DE DEPENDÊNCIA
# ==============================================================================

def get_connection_params(config_dict):
    """Extrai os parâmetros de conexão do dicionário de configuração."""
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
        "motivos_perda_tipos": {"display_name_key": "col_motivo_perda", "table": "motivos_perda_tipos", "pk_column": "id", "columns": {"id": {"type": "int", "db_column": "id", "display_key": "col_id", "editable": False}, "descricao": {"type": "str", "db_column": "descricao", "display_key": "col_descricao", "editable": True}}},
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
                        data[db_col] = int(val)
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
# 3. CLASSES DE GERENCIAMENTO
# ==============================================================================

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
            elif config["widget"] == "DateEntry":
                widget = DateEntry(form_frame, dateformat='%d/%m/%Y')
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
                            elif isinstance(widget, DateEntry):
                                widget.entry.delete(0, END)
                                widget.entry.insert(0, value.strftime('%d/%m/%Y'))
                            else:
                                widget.delete(0, END)
                                widget.insert(0, str(value))
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar dados da ordem: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def save_changes(self):
        data = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, DateEntry):
                date_val = widget.entry.get()
                data[key] = datetime.strptime(date_val, '%d/%m/%Y').date() if date_val else None
            else:
                data[key] = widget.get().strip()
                
        if not data["numero_wo"]:
            messagebox.showwarning(self.get_string("required_field_warning", field_name=self.get_string('col_wo')), parent=self)
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                update_data = {k: v for k, v in data.items() if v is not None and v != ''}
                set_clauses = [f'"{col}" = %s' for col in update_data.keys()]
                values = list(update_data.values()) + [self.ordem_id]
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
        self.title(self.get_string('btn_pcp_management'))
        self.geometry("1000x700")
        self.grab_set()
        
        
        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"},
            "data_previsao_entrega": {"label_key": "col_data_previsao", "widget": "DateEntry"},
            "tiragem_em_folhas": {"label_key": "col_tiragem_em_folhas", "widget": "Entry"}, 
            "equipamento": {"label_key": "equipment_label", "widget": "Combobox", "lookup": "equipamentos_tipos"},
            "qtde_cores": {"label_key": "col_qtde_cores", "widget": "Combobox", "lookup": "qtde_cores_tipos"},
            "tipo_papel": {"label_key": "col_tipo_papel", "widget": "Combobox", "lookup": "tipos_papel"},
            "gramatura": {"label_key": "col_gramatura", "widget": "Combobox", "lookup": "gramaturas_tipos"},
            "formato": {"label_key": "col_formato", "widget": "Combobox", "lookup": "formatos_tipos"},
            "fsc": {"label_key": "col_fsc", "widget": "Combobox", "lookup": "fsc_tipos"},
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

        form_frame = tb.LabelFrame(main_frame, text=self.get_string('new_order_section'), bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor=N)

        num_fields = len(self.fields_config)
        mid_point = (num_fields + 1) // 2
        
        col_num = 0
        row_num = 0
        for i, (key, config) in enumerate(self.fields_config.items()):
            if i >= mid_point:
                col_num = 2
                row_num = i - mid_point
            else:
                col_num = 0
                row_num = i
            
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=row_num, column=col_num, padx=5, pady=5, sticky=W)
            if config["widget"] == "Combobox":
                widget = tb.Combobox(form_frame, state="readonly")
            elif config["widget"] == "DateEntry":
                widget = DateEntry(form_frame, dateformat='%d/%m/%Y')
            else:
                widget = tb.Entry(form_frame)
            widget.grid(row=row_num, column=col_num + 1, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget

        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)

        btn_frame = tb.Frame(form_frame)
        btn_frame.grid(row=mid_point, column=0, columnspan=4, pady=10)
        tb.Button(btn_frame, text=self.get_string('save_btn'), command=self.save_new_ordem, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text=self.get_string('clear_filters_btn'), command=self.clear_fields, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

        action_frame = tb.Frame(main_frame)
        action_frame.pack(fill=X, pady=5)
        self.edit_button = tb.Button(action_frame, text=self.get_string('edit_order_btn'), command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
        self.edit_button.pack(side=LEFT, padx=5)
        self.cancel_button = tb.Button(action_frame, text=self.get_string('cancel_order_btn'), command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
        self.cancel_button.pack(side=LEFT, padx=5)
        self.services_button = tb.Button(action_frame, text=self.get_string('btn_manage_services'), command=self.open_service_manager, bootstyle="primary-outline", state=DISABLED)
        self.services_button.pack(side=LEFT, padx=5)
        
        tree_frame = tb.LabelFrame(main_frame, text=self.get_string('created_orders_section'), bootstyle=INFO, padding=10)
        tree_frame.pack(fill=BOTH, expand=True)
        
        cols = ("id", "wo", "cliente", "equipamento", "data_previsao", "status")
        headers = (self.get_string('col_id'), self.get_string('col_wo'), self.get_string('col_cliente'), self.get_string('equipment_label'), self.get_string('col_data_previsao'), self.get_string('col_status'))
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=120, anchor=W)
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
            self.services_button.config(state=DISABLED)
            return
        
        self.services_button.config(state=NORMAL)
        item_values = self.tree.item(selected_item, 'values')
        status = item_values[-1] if item_values else ""

        if status == 'Em Aberto':
            self.edit_button.config(state=NORMAL)
            self.cancel_button.config(state=NORMAL)
        else:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)

    def open_service_manager(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[0]
        wo_number = item_values[1]
        
        ServiceManagerWindow(self, self.db_config, ordem_id, wo_number, refresh_callback=self.load_ordens)

    def open_edit_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[0]
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_ordens)

    def cancel_ordem(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_cancel_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_num = item_values[0], item_values[1]
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
        self.services_button.config(state=DISABLED)
        
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, numero_wo, cliente, equipamento, data_previsao_entrega, status FROM ordem_producao ORDER BY data_cadastro_pcp DESC")
                for row in cur.fetchall():
                    row_list = list(row)
                    if row_list[4]:
                        row_list[4] = row_list[4].strftime('%d/%m/%Y')
                    self.tree.insert("", END, values=tuple(row_list))
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
                            display_col_info = next((v for k, v in schema_info['columns'].items() if v['editable'] and k != schema_info['pk_column']), None)
                            if not display_col_info:
                                 display_col_info = next((v for k, v in schema_info['columns'].items() if k != schema_info['pk_column']), None)
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
        data = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, DateEntry):
                data[key] = widget.entry.get() or None
            else:
                data[key] = widget.get().strip()
                
        if not data["numero_wo"]:
            messagebox.showwarning(self.get_string("required_field_warning", field_name=self.get_string("col_wo")), parent=self)
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cols_to_save = list(self.fields_config.keys())
                non_empty_data = {col: data[col] for col in cols_to_save if data[col]}
                
                if 'data_previsao_entrega' in non_empty_data:
                    non_empty_data['data_previsao_entrega'] = datetime.strptime(non_empty_data['data_previsao_entrega'], '%d/%m/%Y').date()

                cols = non_empty_data.keys()
                query = f"""
                    INSERT INTO ordem_producao ({', '.join(f'"{c}"' for c in cols)}, status)
                    VALUES ({', '.join([f'%({c})s' for c in cols])}, 'Em Aberto')
                """
                cur.execute(query, non_empty_data)
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('order_save_success'), parent=self)
            self.clear_fields()
            self.load_ordens()
            if 'production' in self.master.open_windows and self.master.open_windows['production'].winfo_exists():
                self.master.open_windows['production'].load_open_wos()
        except psycopg2.IntegrityError:
            conn.rollback()
            messagebox.showerror("Erro de Integridade", self.get_string('integrity_error_wo', wo=data['numero_wo']), parent=self)
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro ao Salvar", self.get_string('save_order_error', error=e), parent=self)
        finally:
            if conn: conn.close()

    def clear_fields(self):
        for widget in self.widgets.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            elif isinstance(widget, DateEntry):
                widget.entry.delete(0, END)
            else:
                widget.delete(0, END)
                
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


# ==============================================================================
# 5. CLASSE PRINCIPAL DE APONTAMENTO
# ==============================================================================
class App(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')
        self.grab_set()
        self.set_localized_title()
        self.geometry("1200x850")

        # Máquina de estados para controlar o fluxo
        self.current_state = 'IDLE'  # IDLE, SETUP_RUNNING, PRODUCTION_READY, PRODUCTION_RUNNING, FINISHED
        
        # Timers e Dados
        self.setup_start_time, self.setup_end_time = None, None
        self.prod_start_time, self.prod_end_time = None, None
        
        self.setup_timer_job, self.prod_timer_job = None, None
        
        # Lista unificada para paradas
        self.all_stops_data = []

        # IDs e Dados
        self.selected_ordem_id, self.selected_servico_id, self.setup_id = None, None, None
        self.open_wos_data, self.pending_services_data = {}, {}
        self.motivos_perda_data = {}
        
        # Dicionários de Widgets
        self.initial_fields, self.setup_fields, self.production_fields, self.info_labels = {}, {}, {}, {}
        
        self.create_widgets()
        self.load_initial_data()
        self.update_ui_state()

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.master.current_language, LANGUAGES.get('portugues', {}))
        # Adiciona um valor padrão para evitar erros se a chave não existir
        default_text = key.replace('_', ' ').capitalize()
        return lang_dict.get(key, default_text).format(**kwargs)

    def set_localized_title(self):
        self.title(self.get_string('btn_production_entry'))

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Frame Superior (Seleção e Informações) ---
        top_frame = tb.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        # --- 1. SELEÇÃO INICIAL ---
        selection_frame = tb.LabelFrame(top_frame, text=self.get_string('initial_selection_section'), bootstyle=PRIMARY, padding=15)
        selection_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        selection_frame.grid_columnconfigure(1, weight=1)
        
        tb.Label(selection_frame, text="Selecionar WO:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.wo_combobox = tb.Combobox(selection_frame, state="readonly")
        self.wo_combobox.grid(row=0, column=1, sticky=EW, padx=5, pady=2)
        self.wo_combobox.bind("<<ComboboxSelected>>", self.on_wo_selected)

        tb.Label(selection_frame, text=self.get_string("service_select_label")).grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.service_combobox = tb.Combobox(selection_frame, state="disabled")
        self.service_combobox.grid(row=1, column=1, sticky=EW, padx=5, pady=2)
        self.service_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_ui_state())

        tb.Label(selection_frame, text=self.get_string("printer_label") + ":").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.impressor_combobox = tb.Combobox(selection_frame, state="readonly")
        self.impressor_combobox.grid(row=2, column=1, sticky=EW, padx=5, pady=2)
        self.initial_fields['impressor'] = self.impressor_combobox
        
        tb.Label(selection_frame, text=self.get_string("shift_label") + ":").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        self.turno_combobox = tb.Combobox(selection_frame, state="readonly")
        self.turno_combobox.grid(row=3, column=1, sticky=EW, padx=5, pady=2)
        self.initial_fields['turno'] = self.turno_combobox
        
        # --- PAINEL DE INFORMAÇÕES DA WO ---
        self.wo_info_frame = tb.LabelFrame(top_frame, text="Informações da Ordem", bootstyle=PRIMARY, padding=15)
        self.wo_info_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        info_keys = {'col_cliente': 'Cliente', 'equipment_label': 'Equipamento', 'col_tipo_papel': 'Tipo Papel', 'col_tiragem_em_folhas': 'Tiragem Meta'}
        for i, (key, text) in enumerate(info_keys.items()):
            tb.Label(self.wo_info_frame, text=f"{text}:", font="-weight bold").grid(row=i, column=0, sticky=W, padx=5, pady=2)
            label_widget = tb.Label(self.wo_info_frame, text="-")
            label_widget.grid(row=i, column=1, sticky=W, padx=5, pady=2)
            self.info_labels[key] = label_widget

        # --- 2. APONTAMENTO DE SETUP E PRODUÇÃO ---
        process_frame = tb.Frame(main_frame)
        process_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=5)
        process_frame.grid_columnconfigure(0, weight=1)
        process_frame.grid_columnconfigure(1, weight=1)

        self.setup_frame = tb.LabelFrame(process_frame, text=self.get_string('setup_section'), bootstyle=INFO, padding=15)
        self.setup_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.setup_frame.grid_columnconfigure(0, weight=1)
        
        setup_entries_frame = tb.Frame(self.setup_frame)
        setup_entries_frame.pack(fill=X, expand=YES, pady=(0,10))
        setup_fields_defs = {'perdas': 'col_perdas', 'malas': 'col_malas', 'total_lavagens': 'col_total_lavagens', 'numero_inspecao': 'col_numeroinspecao'}
        for key, label_key in setup_fields_defs.items():
            tb.Label(setup_entries_frame, text=self.get_string(label_key) + ":").pack(fill=X, pady=2)
            entry = tb.Entry(setup_entries_frame)
            entry.pack(fill=X)
            self.setup_fields[key] = entry
        
        setup_control_frame = tb.Frame(self.setup_frame)
        setup_control_frame.pack(fill=X, expand=YES)
        self.setup_timer_label = tb.Label(setup_control_frame, text="00:00:00", font=("Helvetica", 20, "bold"))
        self.setup_timer_label.pack(pady=5)
        self.setup_button = tb.Button(setup_control_frame, text=self.get_string('start_setup_btn'), bootstyle="info", command=self.toggle_setup, width=20)
        self.setup_button.pack(pady=5, ipady=5)
        self.setup_stop_button = tb.Button(setup_control_frame, text=self.get_string('point_setup_stop_btn'), command=lambda: self.open_stop_window('setup'), state=DISABLED, width=20)
        self.setup_stop_button.pack(pady=5, ipady=5)
        
        self.prod_frame = tb.LabelFrame(process_frame, text=self.get_string('production_section'), bootstyle=SUCCESS, padding=15)
        self.prod_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.prod_frame.grid_columnconfigure(0, weight=1)

        prod_entries_frame = tb.Frame(self.prod_frame)
        prod_entries_frame.pack(fill=X, expand=YES, pady=(0,10))
        prod_fields_defs = {'giros_rodados': 'col_giros_rodados', 'quantidadeproduzida': 'col_quantidadeproduzida', 'perdas_producao': 'col_perdas_producao'}
        for key, label_key in prod_fields_defs.items():
            tb.Label(prod_entries_frame, text=self.get_string(label_key) + ":").pack(fill=X, pady=2)
            entry = tb.Entry(prod_entries_frame)
            entry.pack(fill=X)
            self.production_fields[key] = entry

        # NOVO CAMPO: Motivo da Perda
        tb.Label(prod_entries_frame, text=self.get_string("col_motivo_perda") + ":").pack(fill=X, pady=2)
        self.motivo_perda_combobox = tb.Combobox(prod_entries_frame, state="readonly")
        self.motivo_perda_combobox.pack(fill=X)
        self.production_fields['motivo_perda'] = self.motivo_perda_combobox
        
        prod_control_frame = tb.Frame(self.prod_frame)
        prod_control_frame.pack(fill=X, expand=YES)
        self.prod_timer_label = tb.Label(prod_control_frame, text="00:00:00", font=("Helvetica", 20, "bold"))
        self.prod_timer_label.pack(pady=5)
        self.prod_button = tb.Button(prod_control_frame, text=self.get_string('start_production_btn'), bootstyle="success", command=self.toggle_production, width=20)
        self.prod_button.pack(pady=5, ipady=5)
        self.prod_stop_button = tb.Button(prod_control_frame, text=self.get_string('point_prod_stop_btn'), command=lambda: self.open_stop_window('production'), state=DISABLED, width=20)
        self.prod_stop_button.pack(pady=5, ipady=5)

        # --- 4. LISTA DE PARADAS UNIFICADA ---
        stops_frame = tb.LabelFrame(main_frame, text="Histórico de Paradas", padding=10)
        stops_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=5)
        
        self.stops_tree = tb.Treeview(stops_frame, columns=('tipo', 'motivo', 'inicio', 'fim', 'duracao'), show='headings', height=5)
        self.stops_tree.heading('tipo', text="Tipo"); self.stops_tree.column('tipo', width=80, anchor=CENTER)
        self.stops_tree.heading('motivo', text="Motivo"); self.stops_tree.column('motivo', width=250)
        self.stops_tree.heading('inicio', text="Início"); self.stops_tree.column('inicio', width=100, anchor=CENTER)
        self.stops_tree.heading('fim', text="Fim"); self.stops_tree.column('fim', width=100, anchor=CENTER)
        self.stops_tree.heading('duracao', text="Duração"); self.stops_tree.column('duracao', width=100, anchor=CENTER)
        self.stops_tree.pack(fill=BOTH, expand=YES)
        
        # --- 5. Botão final e Status ---
        self.final_register_button = tb.Button(main_frame, text=self.get_string("register_entry_btn"), command=self.submit_final_production, state=DISABLED)
        self.final_register_button.grid(row=3, column=0, columnspan=2, pady=20, ipady=10)

        status_bar = tb.Frame(main_frame, padding=(10, 5))
        status_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10,0))
        tb.Label(status_bar, text="Status:", font=("Helvetica", 12, "bold")).pack(side=LEFT)
        self.status_label = tb.Label(status_bar, text=self.get_string('status_idle'), font=("Helvetica", 12, "bold"), bootstyle="secondary")
        self.status_label.pack(side=LEFT, padx=10)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def load_initial_data(self):
        self.load_open_wos()
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT nome FROM impressores ORDER BY nome')
                self.impressor_combobox['values'] = [row[0] for row in cur.fetchall()]
                cur.execute('SELECT descricao FROM turnos_tipos ORDER BY id')
                self.turno_combobox['values'] = [row[0] for row in cur.fetchall()]
                cur.execute('SELECT id, descricao FROM motivos_perda_tipos ORDER BY descricao')
                self.motivos_perda_data = {desc: mid for mid, desc in cur.fetchall()}
                self.motivo_perda_combobox['values'] = list(self.motivos_perda_data.keys())
        except Exception as e:
            messagebox.showwarning("Erro", f"Falha ao carregar dados iniciais: {e}", parent=self)
        finally:
            if conn: conn.close()

    def load_open_wos(self):
        self.open_wos_data = {}
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, numero_wo, cliente FROM ordem_producao WHERE status != 'Concluído' ORDER BY numero_wo")
                wos_list = []
                for ordem_id, numero_wo, cliente in cur.fetchall():
                    display_text = f"{numero_wo} - {cliente or 'Sem Cliente'}"
                    wos_list.append(display_text)
                    self.open_wos_data[display_text] = {"id": ordem_id}
                self.wo_combobox['values'] = wos_list
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as Ordens de Serviço: {e}", parent=self)
        finally:
            if conn: conn.close()

    def on_wo_selected(self, event=None):
        self.service_combobox.set('')
        self.service_combobox.config(state='disabled')
        self.pending_services_data = {}
        self.selected_ordem_id = None

        selected_wo_text = self.wo_combobox.get()
        if not selected_wo_text: 
            self.update_wo_info_panel()
            self.update_ui_state()
            return

        wo_data = self.open_wos_data.get(selected_wo_text)
        if not wo_data: return
        
        self.selected_ordem_id = wo_data['id']
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, descricao FROM ordem_servicos WHERE ordem_id = %s AND status = 'Pendente' ORDER BY sequencia", (self.selected_ordem_id,))
                services = cur.fetchall()
                if services:
                    service_list = [f"{service_id}: {desc}" for service_id, desc in services]
                    self.pending_services_data = {f"{service_id}: {desc}": service_id for service_id, desc in services}
                    self.service_combobox['values'] = service_list
                    self.service_combobox.config(state='readonly')
                else:
                    self.service_combobox['values'] = []
                    self.service_combobox.set(self.get_string('no_pending_services'))
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Falha ao carregar etapas da WO: {e}", parent=self)
        finally:
            if conn: conn.close()
        
        self.update_wo_info_panel()
        self.update_ui_state()
        
    def update_wo_info_panel(self):
        for label in self.info_labels.values(): label.config(text="-")
        if not self.selected_ordem_id: return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                info_cols = ['cliente', 'equipamento', 'tipo_papel', 'tiragem_em_folhas']
                cur.execute(f"SELECT {', '.join(info_cols)} FROM ordem_producao WHERE id = %s", (self.selected_ordem_id,))
                data = cur.fetchone()
                if data:
                    data_dict = dict(zip(info_cols, data))
                    self.info_labels['col_cliente'].config(text=data_dict.get('cliente', '-'))
                    self.info_labels['equipment_label'].config(text=data_dict.get('equipamento', '-'))
                    self.info_labels['col_tipo_papel'].config(text=data_dict.get('tipo_papel', '-'))
                    self.info_labels['col_tiragem_em_folhas'].config(text=data_dict.get('tiragem_em_folhas', '-'))
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Falha ao carregar informações da WO: {e}", parent=self)
        finally:
            if conn: conn.close()

    def update_ui_state(self):
        state = self.current_state
        all_widgets = list(self.initial_fields.values()) + list(self.setup_fields.values()) + list(self.production_fields.values())
        for widget in all_widgets: widget.config(state=DISABLED)
        
        self.wo_combobox.config(state=DISABLED)
        self.service_combobox.config(state=DISABLED)
        for btn in [self.setup_button, self.setup_stop_button, self.prod_button, self.prod_stop_button, self.final_register_button]:
            btn.config(state=DISABLED)

        if state == 'IDLE':
            self.wo_combobox.config(state='readonly'); 
            if self.wo_combobox.get(): self.service_combobox.config(state='readonly')
            for w in self.initial_fields.values(): w.config(state='readonly')
            if self.service_combobox.get() and self.service_combobox.get() != self.get_string('no_pending_services'):
                self.setup_button.config(state=NORMAL, text=self.get_string('start_setup_btn'))
            self.status_label.config(text=self.get_string('status_idle'), bootstyle="secondary")

        elif state == 'SETUP_RUNNING':
            for w in self.setup_fields.values(): w.config(state=NORMAL)
            self.setup_button.config(state=NORMAL, text=self.get_string('finish_setup_btn'))
            self.setup_stop_button.config(state=NORMAL)
            self.status_label.config(text=self.get_string('status_setup_running'), bootstyle="info")

        elif state == 'PRODUCTION_READY':
            for w in self.setup_fields.values(): w.config(state=DISABLED)
            self.prod_button.config(state=NORMAL, text=self.get_string('start_production_btn'))
            self.status_label.config(text=self.get_string('status_setup_done'), bootstyle="primary")

        elif state == 'PRODUCTION_RUNNING':
            for w in self.setup_fields.values(): w.config(state=DISABLED)
            for w in self.production_fields.values(): w.config(state=NORMAL)
            self.prod_button.config(state=NORMAL, text=self.get_string('finish_production_btn'))
            self.prod_stop_button.config(state=NORMAL)
            self.status_label.config(text=self.get_string('status_prod_running'), bootstyle="success")

        elif state == 'FINISHED':
            for w in self.production_fields.values(): w.config(state=NORMAL)
            self.final_register_button.config(state=NORMAL)
            self.status_label.config(text=self.get_string('status_prod_done'), bootstyle="warning")

    def toggle_setup(self):
        if self.current_state == 'IDLE':
            if not self.service_combobox.get() or not self.impressor_combobox.get() or not self.turno_combobox.get() or self.service_combobox.get() == self.get_string('no_pending_services'):
                messagebox.showwarning("Seleção Incompleta", "Selecione WO, Etapa, Impressor e Turno para iniciar.")
                return
            
            self.selected_servico_id = self.pending_services_data[self.service_combobox.get()]
            self.current_state = 'SETUP_RUNNING'
            self.setup_start_time = datetime.now()
            self.update_setup_timer()
            
        elif self.current_state == 'SETUP_RUNNING':
            if not self.validate_and_save_setup(): return
            self.current_state = 'PRODUCTION_READY'
            self.setup_end_time = datetime.now()
            if self.setup_timer_job: self.after_cancel(self.setup_timer_job)

        self.update_ui_state()

    def toggle_production(self):
        if self.current_state == 'PRODUCTION_READY':
            self.current_state = 'PRODUCTION_RUNNING'
            self.prod_start_time = datetime.now()
            self.update_prod_timer()
        elif self.current_state == 'PRODUCTION_RUNNING':
            self.current_state = 'FINISHED'
            self.prod_end_time = datetime.now()
            if self.prod_timer_job: self.after_cancel(self.prod_timer_job)
        
        self.update_ui_state()
        
    def validate_and_save_setup(self):
        data = {key: widget.get().strip() for key, widget in self.setup_fields.items()}
        for key, value in data.items():
            if not value:
                messagebox.showerror("Campos Obrigatórios", self.get_string('setup_fields_required'))
                return False
        
        conn = self.get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO apontamento_setup (servico_id, data_apontamento, hora_inicio, hora_fim, perdas, malas, total_lavagens, numero_inspecao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """
                params = (
                    self.selected_servico_id, date.today(), self.setup_start_time, datetime.now(),
                    int(data['perdas']), int(data['malas']), int(data['total_lavagens']), data['numero_inspecao']
                )
                cur.execute(query, params)
                self.setup_id = cur.fetchone()[0]

                for stop in self.all_stops_data:
                    if stop['type'] == 'Setup':
                        cur.execute(
                            "INSERT INTO paradas_setup (setup_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s)",
                            (self.setup_id, stop['motivo_id'], stop['hora_inicio_parada'], stop['hora_fim_parada'], stop.get('motivo_extra_detail'))
                        )
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('setup_saved_success'))
            return True
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro", self.get_string('setup_save_failed', error=e))
            return False
        finally:
            if conn: conn.close()

    def submit_final_production(self):
        # 1. Validação
        prod_data = {key: widget.get().strip() for key, widget in self.production_fields.items()}
        if not prod_data.get('giros_rodados') or not prod_data.get('quantidadeproduzida'):
            messagebox.showerror("Validação", self.get_string('final_appointment_validation_error'), parent=self)
            return

        # 2. Coleta de dados
        final_data = {}
        # Dados da Seleção Inicial
        final_data['servico_id'] = self.selected_servico_id
        final_data['ordem_id'] = self.selected_ordem_id
        final_data['impressor'] = self.initial_fields['impressor'].get()
        final_data['turno'] = self.initial_fields['turno'].get()
        final_data['wo'] = self.wo_combobox.get().split(' - ')[0]
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            # Coleta dados complementares da WO
            with conn.cursor() as cur:
                cur.execute("SELECT cliente, equipamento, qtde_cores, tipo_papel, formato, gramatura, fsc FROM ordem_producao WHERE id = %s", (self.selected_ordem_id,))
                wo_details = cur.fetchone()
                if wo_details:
                    keys = ['cliente', 'equipamento', 'qtde_cores', 'tipo_papel', 'formato', 'gramatura', 'fsc']
                    final_data.update(dict(zip(keys, wo_details)))

            # Coleta dados do formulário de Produção
            final_data['data'] = date.today()
            final_data['horainicio'] = self.prod_start_time.time() if self.prod_start_time else None
            final_data['horafim'] = self.prod_end_time.time() if self.prod_end_time else None
            final_data['giros_rodados'] = int(prod_data['giros_rodados']) if prod_data['giros_rodados'] else None
            final_data['quantidadeproduzida'] = int(prod_data['quantidadeproduzida']) if prod_data['quantidadeproduzida'] else None
            final_data['perdas_producao'] = int(prod_data['perdas_producao']) if prod_data.get('perdas_producao') else None
            
            selected_motivo_perda = self.motivo_perda_combobox.get()
            final_data['motivo_perda_id'] = self.motivos_perda_data.get(selected_motivo_perda)

            # 3. Transação no Banco de Dados
            with conn.cursor() as cur:
                # Insere apontamento principal de produção
                cols = [f'"{k}"' for k in final_data.keys() if final_data[k] is not None]
                filtered_data = {k: v for k, v in final_data.items() if v is not None}
                placeholders = [f"%({k})s" for k in filtered_data.keys()]
                
                query = f"INSERT INTO apontamento ({', '.join(cols)}) VALUES ({', '.join(placeholders)}) RETURNING id"
                cur.execute(query, filtered_data)
                apontamento_id = cur.fetchone()[0]

                # Insere paradas de produção
                for stop in self.all_stops_data:
                    if stop['type'] == 'Produção':
                        cur.execute(
                            "INSERT INTO paradas (apontamento_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s)",
                            (apontamento_id, stop['motivo_id'], stop['hora_inicio_parada'], stop['hora_fim_parada'], stop.get('motivo_extra_detail'))
                        )
                
                # Atualiza status do serviço
                cur.execute("UPDATE ordem_servicos SET status = 'Concluído' WHERE id = %s", (self.selected_servico_id,))
                
                # Verifica se todos os serviços da ordem foram concluídos para então fechar a WO
                cur.execute("SELECT COUNT(*) FROM ordem_servicos WHERE ordem_id = %s AND status = 'Pendente'", (self.selected_ordem_id,))
                pending_services = cur.fetchone()[0]
                if pending_services == 0:
                    cur.execute("UPDATE ordem_producao SET status = 'Concluído' WHERE id = %s", (self.selected_ordem_id,))

            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('production_saved_success'), parent=self)
            self.destroy() # Fecha a janela de apontamento

        except (psycopg2.Error, ValueError, KeyError) as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", self.get_string('production_save_failed', error=e), parent=self)
        finally:
            if conn: conn.close()

    def update_setup_timer(self):
        if self.current_state == 'SETUP_RUNNING':
            elapsed = datetime.now() - self.setup_start_time
            self.setup_timer_label.config(text=str(elapsed).split('.')[0])
            self.setup_timer_job = self.after(1000, self.update_setup_timer)

    def update_prod_timer(self):
        if self.current_state == 'PRODUCTION_RUNNING':
            elapsed = datetime.now() - self.prod_start_time
            self.prod_timer_label.config(text=str(elapsed).split('.')[0])
            self.prod_timer_job = self.after(1000, self.update_prod_timer)
    
    def open_stop_window(self, stop_type):
        callback = self.add_setup_stop if stop_type == 'setup' else self.add_prod_stop
        RealTimeStopWindow(self, self.db_config, callback)

    def add_setup_stop(self, stop_data):
        stop_data['type'] = 'Setup'
        self.all_stops_data.append(stop_data)
        self.refresh_stops_tree()
    
    def add_prod_stop(self, stop_data):
        stop_data['type'] = 'Produção'
        self.all_stops_data.append(stop_data)
        self.refresh_stops_tree()

    def refresh_stops_tree(self):
        for item in self.stops_tree.get_children():
            self.stops_tree.delete(item)
        for stop in self.all_stops_data:
            start = stop['hora_inicio_parada'].strftime('%H:%M:%S')
            end = stop['hora_fim_parada'].strftime('%H:%M:%S')
            duration = (datetime.combine(date.min, stop['hora_fim_parada']) - datetime.combine(date.min, stop['hora_inicio_parada']))
            self.stops_tree.insert('', END, values=(stop['type'], stop['motivo_text'], start, end, str(duration)))

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
        return LANGUAGES.get(self.current_language, LANGUAGES['portugues']).get(key, f"_{key}_").format(**kwargs)

    def set_localized_title(self):
        self.title(self.get_string('main_menu_title'))

    def load_db_config(self):
        if os.path.exists('db_config.json'):
            try:
                with open('db_config.json', 'r') as f: self.db_config = json.load(f)
            except Exception: self.db_config = {}

    def get_db_connection(self):
        if not all(self.db_config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
            messagebox.showerror(self.get_string("db_conn_incomplete"), self.get_string("db_conn_incomplete"), parent=self)
            return None
        try:
            conn_params = get_connection_params(self.db_config)
            return psycopg2.connect(**conn_params)
        except Exception as e:
            messagebox.showerror(self.get_string("test_connection_btn"), self.get_string('test_connection_failed_db', error=e), parent=self)
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


# =============================================================================
# DESENVOLVIDO POR CLAYTON ALMEIDA
#
#
# =============================================================================
