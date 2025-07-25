# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import pandas as pd
from tkinter import filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import os
from tkinter import filedialog, messagebox
from datetime import date, datetime
import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import (
    messagebox, Toplevel, Listbox, StringVar,
    END, W, E, S, N, CENTER, BOTH, YES, X, Y, RIGHT, LEFT, VERTICAL, DISABLED, NORMAL
)

from config import LANGUAGES, LOOKUP_TABLE_SCHEMAS
from .edit_order_window import EditOrdemWindow
from .wo_detail_window import WODetailWindow
from .service_manager_window import ServiceManagerWindow

class PCPWindow(Toplevel):
    # Em windows/pcp_window.py

    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.master.current_language
        self.title(self.get_string('btn_pcp_management'))
        self.geometry("1200x950")
        self.grab_set()
        
        # Dicionário de configuração de campos
        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"},
            "pn_partnumber": {"label_key": "PN (Partnumber)", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"},
            "data_previsao_entrega": {"label_key": "col_data_previsao", "widget": "DateEntry"},
            # >>> ADICIONE A LINHA ABAIXO DE VOLTA <<<
            "acabamento": {"label_key": "Acabamento", "widget": "Listbox"},
        }
        
        self.machine_fields_left = {
            "equipamento_id": {"label_key": "equipment_label", "widget": "Combobox", "lookup": "equipamentos_tipos"},
            "tiragem_em_folhas": {"label_key": "col_tiragem_em_folhas", "widget": "Entry"},
            "giros_previstos": {"label_key": "giros_previstos", "widget": "Entry"},
            "qtde_cores_id": {"label_key": "col_qtde_cores", "widget": "Combobox", "lookup": "qtde_cores_tipos"},
        }
        self.machine_fields_right = {
            "tipo_papel_id": {"label_key": "col_tipo_papel", "widget": "Combobox", "lookup": "tipos_papel"},
            "gramatura_id": {"label_key": "col_gramatura", "widget": "Combobox", "lookup": "gramaturas_tipos"},
            "formato_id": {"label_key": "col_formato", "widget": "Combobox", "lookup": "formatos_tipos"},
            "fsc_id": {"label_key": "col_fsc", "widget": "Combobox", "lookup": "fsc_tipos"},
        }
        
        self.widgets = {}
        self.machine_widgets = {}
        self.giros_map = {}
        self.acabamentos_map = {}
        self.equipment_speed_map = {}
        
        self.create_widgets()
        self.load_all_combobox_data()
        self.load_ordens()

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
            """Cria e posiciona todos os widgets na janela do PCP com um layout otimizado."""
            main_frame = tb.Frame(self, padding=15)
            main_frame.pack(fill=BOTH, expand=True)

            # --- 1. Formulário Principal (Reorganizado em 2 colunas) ---
            form_frame = tb.LabelFrame(main_frame, text=self.get_string('new_order_section'), bootstyle=PRIMARY, padding=10)
            form_frame.pack(fill=X, pady=(0, 10), anchor=N)
            form_frame.grid_columnconfigure((0, 1), weight=1)

            # --- Coluna da Esquerda: Dados da Ordem ---
            left_form_frame = tb.Frame(form_frame)
            left_form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
            left_form_frame.grid_columnconfigure(1, weight=1)

            fields = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega"]
            for i, key in enumerate(fields):
                config = self.fields_config[key]
                tb.Label(left_form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky=W)
                widget = self.create_widget_from_config(left_form_frame, config)
                widget.grid(row=i, column=1, padx=5, pady=5, sticky=EW)
                self.widgets[key] = widget

            # --- Coluna da Direita: Acabamentos ---
            acab_frame_outer = tb.LabelFrame(form_frame, text=self.get_string("Acabamento"), bootstyle=PRIMARY)
            acab_frame_outer.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
            acab_frame_outer.grid_rowconfigure(0, weight=1)
            acab_frame_outer.grid_columnconfigure(0, weight=1)
            
            acab_scrollbar = tb.Scrollbar(acab_frame_outer)
            acab_scrollbar.grid(row=0, column=1, sticky="ns")
            
            acab_widget = Listbox(acab_frame_outer, selectmode="multiple", yscrollcommand=acab_scrollbar.set, exportselection=False)
            acab_widget.grid(row=0, column=0, sticky="nsew")
            acab_scrollbar.config(command=acab_widget.yview)
            self.widgets["acabamento"] = acab_widget
            
            # --- 2. Seção de Detalhes por Máquina (Sem alterações na estrutura interna) ---
            machines_frame = tb.LabelFrame(main_frame, text="Detalhes de Produção por Máquina", bootstyle=INFO, padding=10)
            machines_frame.pack(fill=X, pady=10)
            machines_frame.grid_columnconfigure((1, 3), weight=1)

            for i, (key, config) in enumerate(self.machine_fields_left.items()):
                tb.Label(machines_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky=W)
                widget = self.create_widget_from_config(machines_frame, config)
                widget.grid(row=i, column=1, padx=5, pady=5, sticky=EW)
                self.machine_widgets[key] = widget
            
            for i, (key, config) in enumerate(self.machine_fields_right.items()):
                tb.Label(machines_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=2, padx=5, pady=5, sticky=W)
                widget = self.create_widget_from_config(machines_frame, config)
                widget.grid(row=i, column=3, padx=5, pady=5, sticky=EW)
                self.machine_widgets[key] = widget
                
            self.machine_widgets["tiragem_em_folhas"].bind("<KeyRelease>", self._calcular_giros_para_maquina)
            self.machine_widgets["qtde_cores_id"].bind("<<ComboboxSelected>>", self._calcular_giros_para_maquina)
            self.machine_widgets["equipamento_id"].bind("<<ComboboxSelected>>", self._calcular_giros_para_maquina)

            tb.Button(machines_frame, text="Adicionar Máquina à Lista", command=self.add_machine_to_list, bootstyle=SUCCESS).grid(row=len(self.machine_fields_left), column=0, columnspan=4, pady=10)

            # --- 3. Tabela de Máquinas e Ações (Sem alterações) ---
            tree_actions_frame = tb.Frame(main_frame)
            tree_actions_frame.pack(fill=X, pady=10)

            cols = ("equipamento", "tiragem", "giros", "cores", "papel", "gramatura", "tempo_previsto")
            headers = ("Equipamento", "Tiragem", "Giros", "Cores", "Papel", "Gramatura", "Tempo Previsto")
            self.machines_tree = tb.Treeview(tree_actions_frame, columns=cols, show="headings", height=5)
            for col, header in zip(cols, headers):
                self.machines_tree.heading(col, text=header)
                self.machines_tree.column(col, width=150, anchor=CENTER)
            self.machines_tree.pack(side=LEFT, fill=X, expand=True)
            
            tb.Button(tree_actions_frame, text="Remover Selecionada", command=self.remove_selected_machine, bootstyle=DANGER).pack(side=LEFT, padx=10, fill=Y)

            final_buttons_frame = tb.Frame(main_frame)
            final_buttons_frame.pack(fill=X, pady=10)
            tb.Button(final_buttons_frame, text=self.get_string('save_btn'), command=self.save_new_ordem, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
            tb.Button(final_buttons_frame, text=self.get_string('clear_filters_btn'), command=self.clear_fields, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

            # --- 4. Tabela de Ordens Criadas e Ações (COM ALTERAÇÕES) ---
            action_frame = tb.Frame(main_frame)
            action_frame.pack(fill=X, pady=10)
            
            self.move_up_button = tb.Button(action_frame, text="Subir na Fila", command=self.move_order_up, bootstyle="primary-outline", state=DISABLED)
            self.move_up_button.pack(side=LEFT, padx=5)
            self.move_down_button = tb.Button(action_frame, text="Descer na Fila", command=self.move_order_down, bootstyle="primary-outline", state=DISABLED)
            self.move_down_button.pack(side=LEFT, padx=(0, 20))
            self.edit_button = tb.Button(action_frame, text="Alterar Ordem Selecionada", command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
            self.edit_button.pack(side=LEFT, padx=5)
            self.cancel_button = tb.Button(action_frame, text="Cancelar Ordem Selecionada", command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
            self.cancel_button.pack(side=LEFT, padx=5)
            tb.Button(action_frame, text="Ver Relatório", command=self.open_report_window, bootstyle="info-outline").pack(side=LEFT, padx=(20, 0))
            self.export_button = tb.Button(action_frame, text="Exportar para XLSX", command=self.export_to_xlsx, bootstyle="success-outline")
            self.export_button.pack(side=RIGHT, padx=5)
            self.pdf_export_button = tb.Button(action_frame, text="Exportar para PDF", command=self.export_to_pdf, bootstyle="danger-outline")
            self.pdf_export_button.pack(side=RIGHT, padx=5)
            
            orders_tree_frame = tb.LabelFrame(main_frame, text="Ordens de Produção Criadas", bootstyle=INFO, padding=10)
            orders_tree_frame.pack(fill=BOTH, expand=True, pady=10)
            
            # ALTERAÇÃO: Adicionada a coluna 'status_atraso'
            cols_orders = ("sequencia", "id", "wo", "cliente", "progresso", "data_previsao", "status_atraso")
            headers_orders = ("Seq.", "ID", "WO", "Cliente", "Progresso da Produção", "Data Prev.", "Status Atraso")
            
            self.tree = tb.Treeview(orders_tree_frame, columns=cols_orders, show="headings", bootstyle=PRIMARY)
            for col, header in zip(cols_orders, headers_orders):
                self.tree.heading(col, text=header)
                self.tree.column(col, width=120, anchor=W)

            # Configurações de largura das colunas
            self.tree.column("progresso", width=250, anchor=W)
            self.tree.column("sequencia", width=40, anchor=CENTER)
            self.tree.column("id", width=50, anchor=CENTER)
            self.tree.column("status_atraso", width=100, anchor=CENTER) # Configuração da nova coluna

            # NOVO: Define a tag de estilo para as linhas atrasadas
            self.tree.tag_configure('atrasado', foreground='red', font=('-weight bold'))

            self.tree.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar = tb.Scrollbar(orders_tree_frame, orient=VERTICAL, command=self.tree.yview)
            scrollbar.pack(side=RIGHT, fill=Y)
            self.tree.configure(yscrollcommand=scrollbar.set)
            self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def create_widget_from_config(self, parent, config):
        if config.get("widget") == "Combobox": return tb.Combobox(parent, state="readonly")
        elif config.get("widget") == "DateEntry": return DateEntry(parent, dateformat='%d/%m/%Y')
        else: return tb.Entry(parent)

    def load_all_combobox_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # Carrega o mapa de giros para o cálculo automático
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}
                
                schemas = LOOKUP_TABLE_SCHEMAS
                
                # Popula os comboboxes da seção de máquinas
                for key, widget in self.machine_widgets.items():
                    if isinstance(widget, tb.Combobox):
                        config = self.machine_fields_left.get(key) or self.machine_fields_right.get(key, {})
                        lookup_ref = config.get("lookup")
                        if lookup_ref and lookup_ref in schemas:
                            schema_info = schemas[lookup_ref]
                            db_col = 'valor' if lookup_ref == 'gramaturas_tipos' else 'descricao'
                            cur.execute(f'SELECT DISTINCT "{db_col}" FROM {schema_info["table"]} ORDER BY "{db_col}"')
                            widget['values'] = [str(row[0]) for row in cur.fetchall()]

                # >>> LÓGICA RESTAURADA: Popula a lista de acabamentos <<<
                acab_widget = self.widgets.get("acabamento")
                if acab_widget and isinstance(acab_widget, Listbox):
                    acab_widget.delete(0, END)
                    schema_info_acab = schemas["acabamentos_tipos"]
                    cur.execute(f'SELECT id, descricao FROM {schema_info_acab["table"]} ORDER BY descricao')
                    self.acabamentos_map = {}
                    for acab_id, desc in cur.fetchall():
                        acab_widget.insert(END, desc)
                        self.acabamentos_map[desc] = acab_id

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados dos comboboxes: {e}", parent=self)
        finally:
            if conn: conn.close()
  
    def remove_selected_machine(self):
        for item in self.machines_tree.selection():
            self.machines_tree.delete(item)

    def save_new_ordem(self):
        """
        Salva a nova Ordem de Produção, coletando todos os detalhes de cada máquina,
        salva-os individualmente e cria os serviços correspondentes.
        """
        conn = self.get_db_connection()
        if not conn:
            return

        try:
            # --- 1. Coleta de dados gerais da WO ---
            wo_number = self.widgets["numero_wo"].get()
            pn_partnumber = self.widgets["pn_partnumber"].get()
            cliente = self.widgets["cliente"].get()
            data_previsao_str = self.widgets["data_previsao_entrega"].entry.get()
            data_previsao = datetime.strptime(data_previsao_str, '%d/%m/%Y').date() if data_previsao_str else None

            if not wo_number or not cliente or not self.machines_tree.get_children():
                messagebox.showwarning("Validação", "WO, Cliente e ao menos uma máquina são obrigatórios.", parent=self)
                return

            with conn.cursor() as cur:
                # --- 2. Busca o próximo número de sequência ---
                cur.execute("SELECT COALESCE(MAX(sequencia_producao), 0) + 1 FROM ordem_producao")
                next_seq = cur.fetchone()[0]
                
                # --- 3. Inserção da Ordem de Produção principal (com dados gerais) ---
                query_op = """
                    INSERT INTO ordem_producao (numero_wo, pn_partnumber, cliente, data_previsao_entrega, sequencia_producao, status)
                    VALUES (%s, %s, %s, %s, %s, 'Em Aberto') RETURNING id;
                """
                op_data = (wo_number, pn_partnumber, cliente, data_previsao, next_seq)
                cur.execute(query_op, op_data)
                ordem_id = cur.fetchone()[0]

                # --- 4. Iterar sobre as máquinas, salvá-las e criar os serviços ---
                sequencia_servico = 1
                for item in self.machines_tree.get_children():
                    # >>> CORREÇÃO AQUI: Desempacotando todas as 7 colunas da tabela <<<
                    (equip_nome, tiragem_str, giros_str, cores_nome, papel_nome, gramatura_valor, _) = self.machines_tree.item(item, 'values')
                    
                    # Busca os IDs correspondentes aos textos
                    cur.execute("SELECT id FROM equipamentos_tipos WHERE descricao = %s", (equip_nome,))
                    equipamento_id = cur.fetchone()[0]
                    
                    cur.execute("SELECT id FROM qtde_cores_tipos WHERE descricao = %s", (cores_nome,))
                    qtde_cores_id = cur.fetchone()[0] if cores_nome and cur.rowcount > 0 else None
                    
                    cur.execute("SELECT id FROM tipos_papel WHERE descricao = %s", (papel_nome,))
                    tipo_papel_id = cur.fetchone()[0] if papel_nome and cur.rowcount > 0 else None

                    cur.execute("SELECT id FROM gramaturas_tipos WHERE valor = %s", (gramatura_valor,))
                    gramatura_id = cur.fetchone()[0] if gramatura_valor and cur.rowcount > 0 else None
                    
                    # NOTA: formato_id e fsc_id não estão na tabela visual, então serão nulos.
                    formato_id = None
                    fsc_id = None

                    tiragem_int = int(tiragem_str)
                    giros_int = int(giros_str)
                    tempo_previsto_ms = tiragem_int

                    # Passo 4.1: Inserir na tabela de máquinas com todos os detalhes
                    query_maquina = """
                        INSERT INTO ordem_producao_maquinas (
                            ordem_id, equipamento_id, tiragem_em_folhas, giros_previstos, tempo_producao_previsto_ms,
                            qtde_cores_id, tipo_papel_id, gramatura_id, formato_id, fsc_id, sequencia_producao
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                    """
                    cur.execute(query_maquina, (
                        ordem_id, equipamento_id, tiragem_int, giros_int, tempo_previsto_ms,
                        qtde_cores_id, tipo_papel_id, gramatura_id, formato_id, fsc_id, sequencia_servico
                    ))
                    maquina_id = cur.fetchone()[0]

                    # Passo 4.2: Inserir o serviço correspondente
                    query_servico = """
                        INSERT INTO ordem_servicos (ordem_id, maquina_id, descricao, status, sequencia)
                        VALUES (%s, %s, %s, 'Pendente', %s);
                    """
                    cur.execute(query_servico, (ordem_id, maquina_id, equip_nome, sequencia_servico))
                    
                    sequencia_servico += 1

            conn.commit()
            messagebox.showinfo("Sucesso", "Ordem de Produção e seus serviços foram salvos com sucesso!", parent=self)
            self.clear_fields()
            self.load_ordens()

        except psycopg2.Error as db_err:
            if conn: conn.rollback()
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível salvar a ordem:\n{db_err}", parent=self)
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}", parent=self)
        finally:
            if conn: conn.close()

    def get_id_from_combobox(self, widget_key, cursor, column_name='descricao'):
        widget = self.widgets.get(widget_key)
        if not widget: return None
        selected_value = widget.get()
        if not selected_value: return None
        config = self.fields_config[widget_key]
        lookup_table = LOOKUP_TABLE_SCHEMAS[config['lookup']]['table']
        cursor.execute(f'SELECT id FROM {lookup_table} WHERE "{column_name}"::text = %s', (selected_value,))
        result = cursor.fetchone()
        return result[0] if result else None

    def open_service_manager(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_number = item_values[1], item_values[2]
        ServiceManagerWindow(self, self.db_config, ordem_id, wo_number, refresh_callback=self.load_ordens)

    def open_edit_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
            
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1] # Pega o ID da segunda coluna da tabela
        
        # Esta linha deve criar a janela de EDIÇÃO, e não a de Login.
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_all_combobox_data)

    def cancel_ordem(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_cancel_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_num = item_values[1], item_values[2]
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
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            conn = self.get_db_connection()
            if not conn: return

            try:
                with conn.cursor() as cur:
                    # A query SQL permanece a mesma
                    sql_query = """
                        WITH ServicoStatus AS (
                            SELECT
                                ordem_id,
                                COUNT(*) AS total_servicos,
                                COUNT(*) FILTER (WHERE status = 'Concluído') AS servicos_concluidos,
                                (SELECT descricao FROM ordem_servicos 
                                WHERE ordem_id = s.ordem_id AND status = 'Em Produção' 
                                ORDER BY sequencia LIMIT 1) as servico_em_producao,
                                (SELECT descricao FROM ordem_servicos 
                                WHERE ordem_id = s.ordem_id AND status = 'Pendente' 
                                ORDER BY sequencia LIMIT 1) as proximo_servico_pendente
                            FROM ordem_servicos s
                            GROUP BY ordem_id
                        )
                        SELECT 
                            op.sequencia_producao,
                            op.id, 
                            op.numero_wo, 
                            op.cliente, 
                            op.data_previsao_entrega,
                            ss.total_servicos,
                            ss.servicos_concluidos,
                            ss.servico_em_producao,
                            ss.proximo_servico_pendente,
                            op.status as status_geral
                        FROM ordem_producao op
                        LEFT JOIN ServicoStatus ss ON op.id = ss.ordem_id
                        WHERE op.status IN ('Em Aberto', 'Em Produção')
                        ORDER BY op.sequencia_producao ASC;
                    """
                    cur.execute(sql_query)
                    
                    # NOVO: Pega a data de hoje uma única vez antes do loop
                    hoje = datetime.now().date()

                    for row in cur.fetchall():
                        seq, ordem_id, wo, cliente, previsao, total_servicos, concluidos, em_prod, pendente, status_geral = row
                        
                        progresso_txt = ""
                        if total_servicos is None or total_servicos == 0:
                            progresso_txt = "Sem serviços definidos"
                        elif em_prod:
                            progresso_txt = f"Etapa {concluidos + 1}/{total_servicos}: {em_prod} (Em Produção)"
                        elif pendente:
                            progresso_txt = f"Etapa {concluidos + 1}/{total_servicos}: {pendente} (Aguardando)"
                        elif concluidos == total_servicos:
                            progresso_txt = "Todas as etapas concluídas"

                        data_formatada = previsao.strftime('%d/%m/%Y') if previsao else ""
                        
                        # --- LÓGICA DE ATRASO ADICIONADA AQUI ---
                        status_atraso = ""
                        tags = () # Começa com uma tupla de tags vazia
                        # Verifica se a data de previsão existe e se é anterior a hoje
                        if previsao and previsao < hoje:
                            status_atraso = "ATRASADO"
                            tags = ('atrasado',) # Adiciona a tag 'atrasado' se a condição for verdadeira
                        # --- FIM DA LÓGICA DE ATRASO ---

                        # Monta a tupla de valores para inserir na tabela visual, incluindo o novo status
                        values = (seq, ordem_id, wo, cliente, progresso_txt, data_formatada, status_atraso)
                        
                        # Adiciona a linha na tabela, aplicando as tags se houver
                        self.tree.insert("", "end", values=values, tags=tags)
                        
            except psycopg2.Error as e:
                messagebox.showerror("Erro ao Carregar", f"Falha ao carregar ordens de produção: {e}", parent=self)
            finally:
                if conn: conn.close()

    def export_to_xlsx(self):
            """
            Exporta os dados da Treeview de Ordens de Produção para um ficheiro XLSX.
            """
            # 1. Obter os dados da Treeview
            rows = self.tree.get_children()
            if not rows:
                messagebox.showwarning("Aviso", "Não há dados para exportar.", parent=self)
                return

            # 2. Estruturar os dados para o pandas
            data = []
            # Obtém os nomes das colunas a partir dos cabeçalhos da Treeview
            columns = [self.tree.heading(col)["text"] for col in self.tree["columns"]]

            for row in rows:
                data.append(self.tree.item(row)["values"])

            # 3. Criar um DataFrame do pandas
            df = pd.DataFrame(data, columns=columns)

            # 4. Pedir ao utilizador o local para salvar o ficheiro
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Ficheiros Excel", "*.xlsx"), ("Todos os ficheiros", "*.*")],
                    title="Salvar o relatório Excel"
                )
                if not file_path:
                    # O utilizador cancelou a caixa de diálogo
                    return

                # 5. Salvar o DataFrame para um ficheiro XLSX
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Sucesso", f"Os dados foram exportados com sucesso para:\n{file_path}", parent=self)

            except Exception as e:
                messagebox.showerror("Erro na Exportação", f"Ocorreu um erro ao exportar para XLSX:\n{e}", parent=self)

    def move_order_up(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        prev_item = self.tree.prev(selected_item)
        if not prev_item: return
        self.swap_orders(selected_item, prev_item)

    def move_order_down(self):
        selected_item = self.tree.focus()
        if not selected_item: return
        next_item = self.tree.next(selected_item)
        if not next_item: return
        self.swap_orders(selected_item, next_item)

    def swap_orders(self, item1, item2):
        data1 = self.tree.item(item1, 'values')
        seq1, id1 = data1[0], data1[1]
        data2 = self.tree.item(item2, 'values')
        seq2, id2 = data2[0], data2[1]
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq2, id1))
                cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq1, id2))
            conn.commit()
            self.load_ordens()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Erro ao Reordenar", f"Não foi possível alterar a sequência: {e}", parent=self)
        finally:
            if conn: conn.close()

    def update_total_giros(self):

        total = 0
        for item in self.machines_tree.get_children():
            values = self.machines_tree.item(item, 'values')
            try:
                giros = int(values[2])
                total += giros
            except (ValueError, IndexError):
                continue
        self.total_giros_var.set(str(total))

    def open_report_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma Ordem de Produção na lista para ver os detalhes.", parent=self)
            return

        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1] # O ID é a segunda coluna

        WODetailWindow(self, self.db_config, ordem_id)

        # =============================================================================

    def clear_fields(self):
        """Limpa todos os campos do formulário e a lista de máquinas."""
        for key, widget in self.widgets.items():
            if not widget: continue
            if isinstance(widget, tb.Combobox):
                widget.set('')
            elif isinstance(widget, DateEntry):
                widget.entry.delete(0, END)
            elif isinstance(widget, Listbox):
                widget.selection_clear(0, END)
            else:
                widget.delete(0, END)
        
        # CORREÇÃO: Acessando os widgets através do dicionário self.machine_widgets
        for widget in self.machine_widgets.values():
            if isinstance(widget, tb.Entry):
                widget.delete(0, END)
            elif isinstance(widget, tb.Combobox):
                widget.set('')

        for item in self.machines_tree.get_children():
            self.machines_tree.delete(item)

    def _calcular_giros_para_maquina(self, event=None):
        """
        Calcula os giros para a máquina que está sendo adicionada,
        mas somente se for uma impressora.
        """
        try:
            # CORREÇÃO: Acessando os widgets através do dicionário self.machine_widgets
            equipamento_selecionado = self.machine_widgets["equipamento_id"].get()
            tiragem_str = self.machine_widgets["tiragem_em_folhas"].get()
            cores_desc = self.machine_widgets["qtde_cores_id"].get()
            giros_widget = self.machine_widgets["giros_previstos"]
            
            giros_widget.delete(0, END)

            if "impressora" in equipamento_selecionado.lower() and tiragem_str and cores_desc:
                tiragem_folhas = int(tiragem_str)
                multiplicador = self.giros_map.get(cores_desc, 1)
                giros_calculado = tiragem_folhas * multiplicador
                giros_widget.insert(0, str(giros_calculado))
            else:
                giros_widget.insert(0, "0")
                
        except (ValueError, IndexError):
            giros_widget = self.machine_widgets.get("giros_previstos")
            if giros_widget:
                giros_widget.delete(0, END)
                giros_widget.insert(0, "0")
        except Exception as e:
            print(f"Erro ao calcular giros para máquina: {e}")

    def on_tree_select(self, event=None):
        selected_item = self.tree.focus()
        
        # Se nada estiver selecionado, desativa todos os botões
        if not selected_item:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)
            self.move_up_button.config(state=DISABLED)
            self.move_down_button.config(state=DISABLED)
            # O botão "Ver Relatório" também deve ser desativado
            # (Você pode encontrar o nome da variável dele no seu código, ex: self.report_button)
            return

        # Habilita os botões que sempre podem ser usados com uma seleção
        self.move_up_button.config(state=NORMAL)
        self.move_down_button.config(state=NORMAL)
        # O botão "Ver Relatório" também deve ser ativado aqui

        # Pega os valores da linha selecionada
        item_values = self.tree.item(selected_item, 'values')
        
        # O texto do progresso está na 5ª coluna (índice 4)
        progresso_text = item_values[4] if len(item_values) > 4 else ""

        # Habilita os botões de Alterar e Cancelar APENAS se a WO não estiver totalmente concluída
        # A verificação agora é feita com base no texto da coluna de progresso.
        if "concluídas" not in progresso_text.lower():
            self.edit_button.config(state=NORMAL)
            self.cancel_button.config(state=NORMAL)
        else:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)

    def format_seconds_to_hhmmss(self, seconds):
        """Converte um total de segundos para o formato HH:MM:SS."""
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00:00"
        
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def add_machine_to_list(self):
        equipamento = self.machine_widgets["equipamento_id"].get()
        tiragem_str = self.machine_widgets["tiragem_em_folhas"].get()
        
        if not all([equipamento, tiragem_str]):
            messagebox.showwarning("Campo Obrigatório", "Equipamento e Tiragem são obrigatórios.", parent=self)
            return

        try:
            tiragem = int(tiragem_str)
            # --- NOVO CÁLCULO DE TEMPO ---
            tempo_por_folha_ms = self.equipment_speed_map.get(equipamento, 1) # Padrão de 1ms se não encontrar
            tempo_total_ms = tiragem * tempo_por_folha_ms
            tempo_total_s = tempo_total_ms / 1000.0
            tempo_formatado = self.format_seconds_to_hhmmss(tempo_total_s)
            # --- FIM DO NOVO CÁLCULO ---
            
            # Coleta os outros dados
            giros = self.machine_widgets["giros_previstos"].get()
            cores = self.machine_widgets["qtde_cores_id"].get()
            papel = self.machine_widgets["tipo_papel_id"].get()
            gramatura = self.machine_widgets["gramatura_id"].get()

            values_to_insert = (equipamento, tiragem, giros, cores, papel, gramatura, tempo_formatado)
            self.machines_tree.insert("", "end", values=values_to_insert)

            # Limpa os campos
            for widget in self.machine_widgets.values():
                if isinstance(widget, tb.Entry): widget.delete(0, END)
                elif isinstance(widget, tb.Combobox): widget.set('')
            
            self._calcular_giros_para_maquina()

        except (ValueError, TypeError):
            messagebox.showerror("Erro de Formato", "O valor da Tiragem deve ser um número.", parent=self)

    def export_to_pdf(self):
            """
            Gera um relatório completo em PDF com KPIs avançados (folhas, tempos, paradas),
            múltiplos gráficos e um layout profissional. (VERSÃO CORRIGIDA)
            """
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("Ficheiros PDF", "*.pdf"), ("Todos os ficheiros", "*.*")],
                    title="Salvar Relatório em PDF"
                )
                if not file_path:
                    return
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao obter o caminho do ficheiro: {e}", parent=self)
                return

            conn = self.get_db_connection()
            if not conn:
                messagebox.showerror("Erro de Conexão", "Não foi possível conectar à base de dados.", parent=self)
                return
            
            try:
                # --- 1. Coleta de Dados com a Nova Query Abrangente ---
                query_completa = """
                    WITH TempoProducao AS (
                        SELECT os.ordem_id, SUM(EXTRACT(EPOCH FROM (ap.horafim - ap.horainicio))) AS total_segundos
                        FROM apontamento ap JOIN ordem_servicos os ON ap.servico_id = os.id
                        GROUP BY os.ordem_id
                    ),
                    TempoSetup AS (
                        SELECT os.ordem_id, SUM(EXTRACT(EPOCH FROM (aps.hora_fim - aps.hora_inicio))) AS total_segundos
                        FROM apontamento_setup aps JOIN ordem_servicos os ON aps.servico_id = os.id
                        GROUP BY os.ordem_id
                    ),
                    TempoParadaProducao AS (
                        SELECT os.ordem_id, SUM(EXTRACT(EPOCH FROM (p.hora_fim_parada - p.hora_inicio_parada))) AS total_segundos
                        FROM paradas p
                        JOIN apontamento ap ON p.apontamento_id = ap.id
                        JOIN ordem_servicos os ON ap.servico_id = os.id
                        GROUP BY os.ordem_id
                    ),
                    TempoParadaSetup AS (
                        SELECT os.ordem_id, SUM(EXTRACT(EPOCH FROM (ps.hora_fim_parada - ps.hora_inicio_parada))) AS total_segundos
                        FROM paradas_setup ps
                        JOIN apontamento_setup aps ON ps.setup_id = aps.id
                        JOIN ordem_servicos os ON aps.servico_id = os.id
                        GROUP BY os.ordem_id
                    ),
                    FolhasReais AS (
                        SELECT os.ordem_id, SUM(ap.quantidadeproduzida) as total_folhas
                        FROM apontamento ap JOIN ordem_servicos os ON ap.servico_id = os.id
                        GROUP BY os.ordem_id
                    )
                    SELECT
                        op.numero_wo,
                        opm.tiragem_em_folhas AS folhas_previstas,
                        COALESCE(fr.total_folhas, 0) AS folhas_reais,
                        COALESCE(tp.total_segundos, 0) AS tempo_producao_segundos,
                        COALESCE(ts.total_segundos, 0) AS tempo_setup_segundos,
                        (COALESCE(tpp.total_segundos, 0) + COALESCE(tps.total_segundos, 0)) AS tempo_parada_segundos
                    FROM ordem_producao op
                    JOIN ordem_producao_maquinas opm ON op.id = opm.ordem_id
                    LEFT JOIN FolhasReais fr ON op.id = fr.ordem_id
                    LEFT JOIN TempoProducao tp ON op.id = tp.ordem_id
                    LEFT JOIN TempoSetup ts ON op.id = ts.ordem_id
                    LEFT JOIN TempoParadaProducao tpp ON op.id = tpp.ordem_id
                    LEFT JOIN TempoParadaSetup tps ON op.id = tps.ordem_id
                    GROUP BY op.id, opm.tiragem_em_folhas, fr.total_folhas, tp.total_segundos, ts.total_segundos, tpp.total_segundos, tps.total_segundos
                    ORDER BY op.numero_wo;
                """
                df = pd.read_sql_query(query_completa, conn)

                # --- 2. Geração de Gráficos Melhorados ---
                chart_paths = []
                plt.style.use('seaborn-v0_8-talk')

                if not df.empty:
                    df_folhas_chart = df[df['folhas_reais'] > 0].head(10)
                    if not df_folhas_chart.empty:
                        df_folhas_chart.plot(x='numero_wo', y=['folhas_previstas', 'folhas_reais'], kind='bar', figsize=(10, 6))
                        plt.title('Folhas Previstas vs. Reais (10 Primeiras WOs com Produção)')
                        plt.ylabel('Quantidade de Folhas')
                        plt.xlabel('')
                        plt.xticks(rotation=45, ha='right')
                        plt.tight_layout()
                        path = "chart_folhas.png"
                        plt.savefig(path)
                        plt.close()
                        chart_paths.append(path)

                if not df.empty and (df['tempo_producao_segundos'].sum() > 0 or df['tempo_setup_segundos'].sum() > 0 or df['tempo_parada_segundos'].sum() > 0):
                    tempo_total_prod = df['tempo_producao_segundos'].sum()
                    tempo_total_setup = df['tempo_setup_segundos'].sum()
                    tempo_total_parada = df['tempo_parada_segundos'].sum()
                    
                    tempos = pd.Series([tempo_total_prod, tempo_total_setup, tempo_total_parada], index=['Produção', 'Setup', 'Paradas'])
                    tempos.plot(kind='pie', autopct='%1.1f%%', figsize=(8, 8), legend=None, 
                                colors=['#4CAF50', '#FFC107', '#F44336'])
                    plt.title('Distribuição do Tempo Total Gasto')
                    plt.ylabel('')
                    plt.tight_layout()
                    path = "chart_tempos.png"
                    plt.savefig(path)
                    plt.close()
                    chart_paths.append(path)

                # --- 3. Construção do PDF com Platypus ---
                def format_seconds(seconds):
                    h = int(seconds // 3600)
                    m = int((seconds % 3600) // 60)
                    s = int(seconds % 60)
                    return f"{h:02d}:{m:02d}:{s:02d}"

                doc = SimpleDocTemplate(file_path, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
                styles = getSampleStyleSheet()
                story = []

                story.append(Paragraph("Relatório Gerencial de Produção", styles['Title']))
                story.append(Spacer(1, 0.5 * cm))
                story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
                story.append(Spacer(1, 1 * cm))

                if chart_paths:
                    story.append(Paragraph("Análise Gráfica", styles['h2']))
                    story.append(Spacer(1, 0.5 * cm))
                    for chart_path in chart_paths:
                        story.append(Image(chart_path, width=18*cm)) 
                        story.append(Spacer(1, 0.5 * cm))

                if not df.empty:
                    story.append(Paragraph("Dados Consolidados por Ordem de Produção", styles['h2']))
                    story.append(Spacer(1, 0.5 * cm))
                    
                    table_data = [['WO', 'Folhas Previstas', 'Folhas Reais', 'Tempo Produção', 'Tempo Parada']]
                    for _, row in df.iterrows():
                        table_data.append([
                            row['numero_wo'],
                            f"{row['folhas_previstas']:.0f}",
                            f"{row['folhas_reais']:.0f}",
                            format_seconds(row['tempo_producao_segundos'] + row['tempo_setup_segundos']),
                            format_seconds(row['tempo_parada_segundos'])
                        ])
                    
                    t = Table(table_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#004D40')),
                        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke), # <-- LINHA CORRIGIDA
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 10),
                        ('BOTTOMPADDING', (0,0), (-1,0), 10),
                        ('TOPPADDING', (0,0), (-1,0), 10),
                        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#E0F2F1')),
                        ('GRID', (0,0), (-1,-1), 1, colors.black)
                    ]))
                    story.append(t)
                
                doc.build(story)
                
                for path in chart_paths:
                    if os.path.exists(path):
                        os.remove(path)
                
                messagebox.showinfo("Sucesso", f"Relatório PDF gerado com sucesso em:\n{file_path}", parent=self)

            except Exception as e:
                messagebox.showerror("Erro na Geração do PDF", f"Ocorreu um erro ao gerar o relatório:\n{e}", parent=self)
            finally:
                if conn: conn.close()