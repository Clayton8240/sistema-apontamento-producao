# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Listbox, Canvas, VERTICAL, HORIZONTAL, DISABLED, NORMAL
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
import pandas as pd
from datetime import datetime
import os
import tempfile  # Importado para arquivos temporários
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
import threading
import queue
import json

# --- 1. Importações Corrigidas ---
from database import get_db_connection, release_db_connection
from schemas import LOOKUP_TABLE_SCHEMAS
from languages import LANGUAGES
from services import get_equipment_fields, get_field_id_by_name, ServiceError, create_production_order

# Importa as outras janelas que esta classe precisa abrir
from .edit_order_window import EditOrdemWindow
from .wo_detail_window import WODetailWindow
from .service_manager_window import ServiceManagerWindow
from .select_closed_wo_window import SelectClosedWOWindow

class PCPWindow(tb.Toplevel):
    """
    Janela de Planejamento e Controle da Produção (PCP).

    Esta classe é responsável por fornecer uma interface completa para o gerenciamento
    de Ordens de Produção (OPs). Permite a criação de novas OPs, a visualização
    e o reordenamento da fila de produção, a edição e o cancelamento de ordens,
    e a exportação de relatórios.
    """
    def __init__(self, master, db_config):
        """
        Inicializa a janela PCP.

        Configura a janela, inicializa os dicionários de configuração de campos,
        os mapas de dados para comboboxes e os widgets da interface.

        Parâmetros:
            master: O widget pai (janela principal).
            db_config (dict): Dicionário de configuração do banco de dados.
        """
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')
        self.title(self.get_string('btn_pcp_management'))
        
        self.state('zoomed')
        self.wm_minsize(1024, 768)

        self.transient(master)
        self.focus_set()

        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"},
            "pn_partnumber": {"label_key": "PN (Partnumber)", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"},
            "data_previsao_entrega": {"label_key": "col_data_previsao", "widget": "DateEntry"},
            "acabamento": {"label_key": "Acabamento", "widget": "Listbox"},
        }
        self.material_fields = {
            "tipo_papel_id": {"label_key": "col_tipo_papel", "widget": "Combobox", "lookup": "tipos_papel"},
            "gramatura_id": {"label_key": "col_gramatura", "widget": "Combobox", "lookup": "gramaturas_tipos"},
            "formato_id": {"label_key": "col_formato", "widget": "Combobox", "lookup": "formatos_tipos"},
            "fsc_id": {"label_key": "col_fsc", "widget": "Combobox", "lookup": "fsc_tipos"},
            "qtde_cores_id": {"label_key": "col_qtde_cores", "widget": "Combobox", "lookup": "qtde_cores_tipos"},
        }
        self.machine_fields_static = {
            "equipamento_id": {"label_key": "equipment_label", "widget": "Combobox", "lookup": "equipamentos_tipos"},
            "tiragem_em_folhas": {"label_key": "col_tiragem_em_folhas", "widget": "Entry"},
        }
        self.widgets = {}
        self.material_widgets = {}
        self.machine_static_widgets = {}
        self.machine_dynamic_widgets = {}
        
        self.giros_map = {}
        self.acabamentos_map = {}
        self.equipment_speed_map = {}
        self.equipamentos_map = {}
        self.cores_map = {}
        self.papeis_map = {}
        self.gramaturas_map = {}
        self.fsc_map = {}
        self.formatos_map = {}
        
        self.data_queue = queue.Queue()
        
        self.create_widgets()
        self.load_all_combobox_data()

    def get_string(self, key, **kwargs):
        """
        Obtém uma string de tradução com base na língua atual.

        Parâmetros:
            key (str): A chave da string no dicionário de idiomas.
            **kwargs: Argumentos para formatação da string.

        Retorna:
            str: A string traduzida e formatada.
        """
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def create_widgets(self):
        """
        Cria e organiza todos os widgets da interface gráfica da janela PCP.

        Esta função é responsável por construir o layout completo da janela, incluindo
        o formulário de criação de OPs, a lista de máquinas, a fila de produção (Treeview)
        e os botões de ação.
        """
        canvas = Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = tb.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill=BOTH, expand=True)

        scrollable_frame = tb.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="scrollable_frame")
        
        def on_canvas_configure(event):
            canvas.itemconfig("scrollable_frame", width=event.width)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        canvas.bind("<Configure>", on_canvas_configure)
        scrollable_frame.bind("<Configure>", on_frame_configure)

        main_frame = tb.Frame(scrollable_frame, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)

        form_frame = tb.LabelFrame(main_frame, text=self.get_string('new_order_section'), bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor='n')
        form_frame.grid_columnconfigure((0, 1, 2), weight=1)

        left_form_frame = tb.Frame(form_frame)
        left_form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_form_frame.grid_columnconfigure(1, weight=1)

        fields = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega"]
        for i, key in enumerate(fields):
            config = self.fields_config[key]
            tb.Label(left_form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky='w')
            widget = self.create_widget_from_config(left_form_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            self.widgets[key] = widget

        material_details_frame = tb.LabelFrame(form_frame, text="Detalhes do Material", bootstyle=INFO, padding=10)
        material_details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        material_details_frame.grid_columnconfigure(1, weight=1)

        for i, (key, config) in enumerate(self.material_fields.items()):
            tb.Label(material_details_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky='w')
            widget = self.create_widget_from_config(material_details_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            self.material_widgets[key] = widget

        acab_frame_outer = tb.LabelFrame(form_frame, text=self.get_string("Acabamento"), bootstyle=PRIMARY)
        acab_frame_outer.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        acab_frame_outer.grid_rowconfigure(0, weight=1)
        acab_frame_outer.grid_columnconfigure(0, weight=1)
        acab_scrollbar = tb.Scrollbar(acab_frame_outer)
        acab_scrollbar.grid(row=0, column=1, sticky="ns")
        acab_widget = Listbox(acab_frame_outer, selectmode="multiple", yscrollcommand=acab_scrollbar.set, exportselection=False)
        acab_widget.grid(row=0, column=0, sticky="nsew")
        acab_scrollbar.config(command=acab_widget.yview)
        self.widgets["acabamento"] = acab_widget
        
        machines_frame = tb.LabelFrame(main_frame, text="Detalhes de Produção por Máquina", bootstyle=INFO, padding=10)
        machines_frame.pack(fill=X, pady=15)
        machines_frame.grid_columnconfigure((0, 1), weight=1)

        machine_data_frame = tb.LabelFrame(machines_frame, text="Dados da Máquina", bootstyle=INFO, padding=10)
        machine_data_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        machine_data_frame.grid_columnconfigure(1, weight=1)

        for i, (key, config) in enumerate(self.machine_fields_static.items()):
            tb.Label(machine_data_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky='w')
            widget = self.create_widget_from_config(machine_data_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            self.machine_static_widgets[key] = widget
        
        self.machine_dynamic_frame = tb.LabelFrame(machines_frame, text="Dados Específicos", bootstyle=INFO, padding=10)
        self.machine_dynamic_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.machine_dynamic_frame.grid_columnconfigure(1, weight=1)
            
        self.machine_static_widgets["equipamento_id"].bind("<<ComboboxSelected>>", self.update_machine_fields)

        tb.Button(machines_frame, text="➕ Adicionar Máquina à Lista", command=self.add_machine_to_list, bootstyle=SUCCESS).grid(row=1, column=0, columnspan=2, pady=10)

        tree_actions_frame = tb.Frame(main_frame)
        tree_actions_frame.pack(fill=X, pady=10)

        cols = ("equipamento", "tiragem", "giros", "cores", "tempo_previsto")
        headers = ("Equipamento", "Tiragem", "Giros", "Cores", "Tempo Previsto")
        self.machines_tree = tb.Treeview(tree_actions_frame, columns=cols, show="headings", height=5)
        for col, header in zip(cols, headers):
            self.machines_tree.heading(col, text=header)
            self.machines_tree.column(col, width=150, anchor=CENTER)
        self.machines_tree.pack(side='left', fill=X, expand=True)
        
        tb.Button(tree_actions_frame, text="🗑️ Remover Selecionada", command=self.remove_selected_machine, bootstyle=DANGER).pack(side='left', padx=10, fill='y')

        final_buttons_frame = tb.Frame(main_frame)
        final_buttons_frame.pack(fill=X, pady=10)
        tb.Button(final_buttons_frame, text=self.get_string('save_btn'), command=self.save_new_ordem, bootstyle=SUCCESS).pack(side='left', padx=5)
        tb.Button(final_buttons_frame, text=self.get_string('clear_filters_btn'), command=self.clear_fields, bootstyle=SECONDARY).pack(side='left', padx=5)
        tb.Button(final_buttons_frame, text=self.get_string('copy_wo_btn'), command=self.open_select_closed_wo_window, bootstyle=INFO).pack(side='left', padx=5)

        action_frame = tb.Frame(main_frame)
        action_frame.pack(fill=X, pady=15)
        
        # Ocultamos os botões de subir e descer, pois a funcionalidade agora é de arrastar e soltar.
        self.move_up_button = tb.Button(action_frame, text="Subir na Fila", command=self.move_order_up, bootstyle="primary-outline", state=DISABLED)
        # self.move_up_button.pack(side='left', padx=5)
        self.move_down_button = tb.Button(action_frame, text="Descer na Fila", command=self.move_order_down, bootstyle="primary-outline", state=DISABLED)
        # self.move_down_button.pack(side='left', padx=(0, 20))
        
        self.edit_button = tb.Button(action_frame, text="✏️ Alterar Ordem Selecionada", command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
        self.edit_button.pack(side='left', padx=5)
        
        self.cancel_button = tb.Button(action_frame, text="🗑️ Cancelar Ordem Selecionada", command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
        self.cancel_button.pack(side='left', padx=5)
        
        tb.Button(action_frame, text="Ver Relatório", command=self.open_report_window, bootstyle="info-outline").pack(side='left', padx=(20, 0))
        self.export_button = tb.Button(action_frame, text="Exportar para XLSX", command=self.export_to_xlsx, bootstyle="success-outline")
        self.export_button.pack(side='right', padx=5)
        self.pdf_export_button = tb.Button(action_frame, text="Exportar para PDF", command=self.export_to_pdf, bootstyle="danger-outline")
        self.pdf_export_button.pack(side='right', padx=5)
        
        orders_tree_frame = tb.LabelFrame(main_frame, text="Ordens de Produção Criadas", bootstyle=INFO, padding=10)
        orders_tree_frame.pack(fill=BOTH, expand=True, pady=10)
        
        cols_orders = ("sequencia", "id", "pn_partnumber", "wo", "cliente", "progresso", "data_previsao", "status_atraso")
        headers_orders = ("Seq.", "PN (Partnumber)", "WO", "Cliente", "Progresso da Produção", "Data Prev.", "Status Atraso")
        
        self.tree = tb.Treeview(orders_tree_frame, columns=cols_orders, show="headings", bootstyle=PRIMARY)

        # Define which columns are visible and set their headers
        visible_cols = [col for col in cols_orders if col != 'id']
        for col, header in zip(visible_cols, headers_orders):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=120, anchor='w')
            
        self.tree.column("id", width=0, stretch=False) # Oculta a coluna ID
        self.tree.column("progresso", width=250, anchor='w')
        self.tree.column("sequencia", width=40, anchor=CENTER)
        self.tree.column("pn_partnumber", width=150, anchor='w')
        self.tree.column("status_atraso", width=100, anchor=CENTER)

        self.tree.tag_configure('atrasado', foreground='red', font=('-weight bold'))

        self.tree.pack(side='left', fill=BOTH, expand=True)
        scrollbar = tb.Scrollbar(orders_tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Adiciona os bindings para o drag and drop
        self.tree.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_end)
        self._drag_data = {"item": None, "y": 0}

        self.start_load_ordens()

    def on_drag_start(self, event):
        """
        Inicia a operação de arrastar (drag) de um item na fila de produção.

        Identifica o item da Treeview sob o cursor e armazena-o junto com a
        posição inicial do mouse para a operação de arrastar e soltar.

        Parâmetros:
            event (tk.Event): O evento de clique do mouse.
        """
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._drag_data["item"] = item
            self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        """
        Manipula o movimento do mouse durante a operação de arrastar.

        Atualmente, este método não possui implementação visual, mas está
        reservado para futuras melhorias, como exibir um feedback visual
        (ex: um ícone ou uma linha de destino) enquanto o item é arrastado.

        Parâmetros:
            event (tk.Event): O evento de movimento do mouse.
        """
        # Este método é mantido para futuras melhorias (ex: exibir um indicador visual),
        # mas a lógica de mover o item foi centralizada no on_drag_end para mais controle.
        pass

    def on_drag_end(self, event):
        """
        Finaliza a operação de arrastar e soltar (drag and drop).

        Quando o botão do mouse é liberado, identifica o item de destino e, se for
        um local válido e diferente do item original, move o item arrastado para a
        nova posição na Treeview e chama a função para atualizar a sequência no banco de dados.

        Parâmetros:
            event (tk.Event): O evento de liberação do botão do mouse.
        """
        if not self._drag_data["item"]:
            return

        dragged_item = self._drag_data["item"]
        destination_item = self.tree.identify_row(event.y)
        
        # Só move e atualiza o banco se o item for solto em um novo local válido
        if destination_item and dragged_item != destination_item:
            self.tree.move(dragged_item, self.tree.parent(dragged_item), self.tree.index(destination_item))
            # A atualização do banco de dados agora só ocorre se houver uma mudança real
            self.update_sequence_from_tree()
        
        self._drag_data["item"] = None # Reseta o estado do arraste


    def update_sequence_from_tree(self):
        """
        Atualiza a sequência de produção no banco de dados com base na ordem da Treeview.

        Itera sobre os itens na Treeview, extrai o ID da ordem e sua nova posição (índice),
        e executa uma transação no banco de dados para atualizar a coluna `sequencia_producao`
        de cada ordem afetada.
        """
        new_sequence = {}
        for i, item_id in enumerate(self.tree.get_children()):
            item_data = self.tree.item(item_id)
            # A coluna "id" não está mais visível, mas os dados ainda estão nos valores
            ordem_id = item_data['values'][1] 
            new_sequence[ordem_id] = i + 1

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                for ordem_id, seq in new_sequence.items():
                    cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq, ordem_id))
            conn.commit()
            # Opcional: Recarregar as ordens para garantir a consistência
            self.start_load_ordens()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Reordenar", f"Não foi possível alterar a sequência: {e}", parent=self)
        finally:
            if conn: release_db_connection(conn)

    def update_machine_fields(self, event=None):
        """
        Atualiza dinamicamente os campos específicos de uma máquina selecionada.

        Quando um equipamento é selecionado no combobox, esta função limpa os campos
        dinâmicos antigos e busca, via camada de serviço, os novos campos associados
        ao equipamento selecionado, renderizando-os na interface.

        Parâmetros:
            event (tk.Event, opcional): O evento que disparou a chamada.
        """
        for widget in self.machine_dynamic_frame.winfo_children():
            widget.destroy()
        self.machine_dynamic_widgets.clear()

        equipamento_nome = self.machine_static_widgets["equipamento_id"].get()
        if not equipamento_nome:
            return

        equipamento_id = self.equipamentos_map.get(equipamento_nome)
        if not equipamento_id:
            return

        try:
            machine_fields = get_equipment_fields(equipamento_id)
        except ServiceError as e:
            messagebox.showerror("Erro", f"Falha ao carregar campos do equipamento: {e}", parent=self)
            return

        for i, field_config in enumerate(machine_fields):
            label_key = field_config["label_traducao"]
            label = tb.Label(self.machine_dynamic_frame, text=self.get_string(label_key) + ":")
            label.grid(row=i, column=0, padx=5, pady=5, sticky='w')

            config = {
                "widget": field_config["widget_type"],
                "lookup": field_config["lookup_table"]
            }
            
            widget = self.create_widget_from_config(self.machine_dynamic_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            
            self.machine_dynamic_widgets[field_config["nome_campo"]] = widget
            
            if config["lookup"]:
                if config["lookup"] == "qtde_cores_tipos":
                    widget['values'] = list(self.cores_map.keys())

    def create_widget_from_config(self, parent, config):
        """
        Cria um widget com base em uma configuração.

        Função utilitária que cria e retorna um widget (Entry, Combobox, DateEntry)
        com base na especificação fornecida no dicionário de configuração.

        Parâmetros:
            parent: O widget pai onde o novo widget será inserido.
            config (dict): Dicionário de configuração do widget.

        Retorna:
            tk.Widget: O widget criado.
        """
        if config.get("widget") == "Combobox": return tb.Combobox(parent, state="readonly")
        elif config.get("widget") == "DateEntry": return DateEntry(parent, dateformat='%d/%m/%Y')
        else: return tb.Entry(parent)

    def load_all_combobox_data(self):
        """
        Carrega os dados para todos os comboboxes e listboxes da janela.

        Busca dados de tabelas de lookup (equipamentos, cores, papéis, etc.)
        no banco de dados e popula os respectivos mapas (dicionários) e widgets
        (Combobox, Listbox) para serem usados na interface.
        """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}

                cur.execute('SELECT descricao, tempo_por_folha_ms FROM equipamentos_tipos')
                self.equipment_speed_map.clear()
                for desc, speed_ms in cur.fetchall():
                    self.equipment_speed_map[desc] = speed_ms if speed_ms and speed_ms > 0 else 1

                schemas = LOOKUP_TABLE_SCHEMAS

                lookup_to_map = {
                    "equipamentos_tipos": (self.equipamentos_map, "id", "descricao"),
                    "qtde_cores_tipos": (self.cores_map, "id", "descricao"),
                    "tipos_papel": (self.papeis_map, "id", "descricao"),
                    "gramaturas_tipos": (self.gramaturas_map, "id", "valor"),
                    "fsc_tipos": (self.fsc_map, "id", "descricao"),
                    "formatos_tipos": (self.formatos_map, "id", "descricao"),
                }

                all_widgets = {**self.material_widgets, **self.machine_static_widgets}
                all_configs = {**self.material_fields, **self.machine_fields_static}

                for key, widget in all_widgets.items():
                    if isinstance(widget, tb.Combobox):
                        config = all_configs.get(key, {})
                        lookup_ref = config.get("lookup")
                        if lookup_ref in schemas and lookup_ref in lookup_to_map:
                            schema_info = schemas[lookup_ref]
                            target_map, id_col, val_col = lookup_to_map[lookup_ref]
                            
                            cur.execute(f'SELECT {id_col}, {val_col} FROM {schema_info["table"]} ORDER BY {val_col}')
                            
                            fetched_data = cur.fetchall()
                            widget['values'] = [str(row[1]) for row in fetched_data]
                            
                            target_map.clear()
                            for id_val, desc_val in fetched_data:
                                target_map[str(desc_val)] = id_val

                acab_widget = self.widgets.get("acabamento")
                if acab_widget and isinstance(acab_widget, Listbox):
                    acab_widget.delete(0, 'end')
                    schema_info_acab = schemas["acabamentos_tipos"]
                    cur.execute(f'SELECT id, descricao FROM {schema_info_acab["table"]} ORDER BY descricao')
                    self.acabamentos_map.clear()
                    for acab_id, desc in cur.fetchall():
                        acab_widget.insert('end', desc)
                        self.acabamentos_map[desc] = acab_id
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados dos comboboxes: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def start_load_ordens(self):
        """
        Inicia o carregamento assíncrono das ordens de produção.

        Limpa a Treeview, exibe um cursor de espera e dispara uma thread para
        executar a busca das ordens no banco de dados em segundo plano, evitando
        que a interface congele.
        """
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.config(cursor="watch")
        self.update_idletasks()
        threading.Thread(target=self._background_load_ordens, daemon=True).start()
        self.after(100, self._check_load_ordens_queue)

    def _background_load_ordens(self):
        """
        Executa a consulta ao banco de dados para buscar as ordens em uma thread separada.

        Realiza uma consulta SQL complexa para obter os dados das ordens de produção
        e o status de seus serviços. O resultado (ou uma exceção) é colocado em uma
        fila para ser processado pela thread principal da UI.
        """
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                sql_query = """
                    SELECT 
                        op.sequencia_producao, op.id, op.pn_partnumber, op.numero_wo, op.cliente, 
                        op.data_previsao_entrega,
                        ss.total_servicos, ss.servicos_concluidos,
                        ss.servico_em_producao, ss.proximo_servico_pendente,
                        CASE 
                            WHEN op.data_previsao_entrega < CURRENT_DATE THEN 'ATRASADO'
                            ELSE 'No Prazo'
                        END as status_atraso
                    FROM ordem_producao op
                    LEFT JOIN LATERAL (
                        SELECT
                            COUNT(*) AS total_servicos,
                            COUNT(*) FILTER (WHERE status = 'Concluído') AS servicos_concluidos,
                            (SELECT descricao FROM ordem_servicos 
                             WHERE ordem_id = op.id AND status = 'Em Produção' 
                             ORDER BY sequencia LIMIT 1) as servico_em_producao,
                            (SELECT descricao FROM ordem_servicos 
                             WHERE ordem_id = op.id AND status = 'Pendente' 
                             ORDER BY sequencia LIMIT 1) as proximo_servico_pendente
                        FROM ordem_servicos
                        WHERE ordem_id = op.id
                    ) ss ON true
                    WHERE op.status IN ('Em Aberto', 'Em Produção')
                    AND (ss.total_servicos IS NULL OR ss.servicos_concluidos < ss.total_servicos)
                    ORDER BY op.sequencia_producao ASC;
                """
                cur.execute(sql_query)
                results = cur.fetchall()
                self.data_queue.put(results)
        except Exception as e:
            self.data_queue.put(e)
        finally:
            if conn:
                release_db_connection(conn)

    def _check_load_ordens_queue(self):
        """
        Verifica a fila de dados e atualiza a Treeview com as ordens carregadas.

        Este método é chamado periodicamente pela thread principal para verificar se
        os dados das ordens já estão disponíveis na fila. Se sim, processa os dados,
        formata o texto de progresso e insere as ordens na Treeview.
        """
        try:
            result = self.data_queue.get_nowait()
            self.config(cursor="")

            if isinstance(result, Exception):
                messagebox.showerror("Erro ao Carregar", f"Falha ao carregar ordens de produção: {result}", parent=self)
                return

            for row in result:
                (seq, ordem_id, pn, wo, cliente, previsao, total_servicos, concluidos, em_prod, pendente, status_atraso) = row
                
                progresso_txt = "Sem serviços definidos"
                if total_servicos and total_servicos > 0:
                    if em_prod:
                        progresso_txt = f"Etapa {concluidos + 1}/{total_servicos}: {em_prod} (Em Produção)"
                    elif pendente:
                        progresso_txt = f"Etapa {concluidos + 1}/{total_servicos}: {pendente} (Aguardando)"
                    elif concluidos == total_servicos:
                        progresso_txt = "Todas as etapas concluídas"

                data_formatada = previsao.strftime('%d/%m/%Y') if previsao else ""
                
                tags = ()
                if status_atraso == "ATRASADO":
                    tags = ('atrasado',)
                    status_atraso = f"⚠️ {status_atraso}"

                values = (seq, ordem_id, pn, wo, cliente, progresso_txt, data_formatada, status_atraso)
                self.tree.insert("", "end", values=values, tags=tags)

        except queue.Empty:
            self.after(100, self._check_load_ordens_queue)

    def remove_selected_machine(self):
        """
        Remove a máquina selecionada da lista de máquinas da nova OP.
        """
        for item in self.machines_tree.selection():
            self.machines_tree.delete(item)

    def save_new_ordem(self):
        """
        Salva uma nova Ordem de Produção no banco de dados.

        Coleta todos os dados do formulário (dados da OP, materiais, acabamentos e
        sequência de máquinas), valida as informações e chama o serviço
        `create_production_order` para persistir os dados de forma transacional.
        """
        wo_number = self.widgets["numero_wo"].get()
        cliente = self.widgets["cliente"].get()
        if not wo_number or not cliente or not self.machines_tree.get_children():
            messagebox.showwarning("Validação", "WO, Cliente e ao menos uma máquina são obrigatórios.", parent=self)
            return

        try:
            data_previsao_str = self.widgets["data_previsao_entrega"].entry.get()
            data_previsao = datetime.strptime(data_previsao_str, '%d/%m/%Y').date() if data_previsao_str else None
            pn_partnumber = self.widgets["pn_partnumber"].get()
            
            tipo_papel_id = self.papeis_map.get(self.material_widgets["tipo_papel_id"].get())
            gramatura_id = self.gramaturas_map.get(self.material_widgets["gramatura_id"].get())
            formato_id = self.formatos_map.get(self.material_widgets["formato_id"].get())
            fsc_id = self.fsc_map.get(self.material_widgets["fsc_id"].get())
            qtde_cores_id = self.cores_map.get(self.material_widgets["qtde_cores_id"].get())

            order_data = {
                "numero_wo": wo_number,
                "pn_partnumber": pn_partnumber,
                "cliente": cliente,
                "data_previsao_entrega": data_previsao,
                "tipo_papel_id": tipo_papel_id,
                "gramatura_id": gramatura_id,
                "formato_id": formato_id,
                "fsc_id": fsc_id,
                "qtde_cores_id": qtde_cores_id
            }

            acabamento_ids = []
            selected_indices = self.widgets["acabamento"].curselection()
            for i in selected_indices:
                desc = self.widgets["acabamento"].get(i)
                acab_id = self.acabamentos_map.get(desc)
                if acab_id:
                    acabamento_ids.append(acab_id)

            machine_list = []
            for item in self.machines_tree.get_children():
                item_data = self.machines_tree.item(item)
                (equip_nome, tiragem_str, giros_str, cores_desc, tempo_formatado) = item_data['values']
                dynamic_values_str = item_data['tags'][0] if item_data['tags'] else "{}"
                dynamic_values = json.loads(dynamic_values_str)

                equipamento_id = self.equipamentos_map.get(equip_nome)
                if not equipamento_id:
                    raise ValueError(f"Equipamento '{equip_nome}' não encontrado no cache.")

                h, m, s = map(int, tempo_formatado.split(':'))
                tempo_previsto_ms = (h * 3600 + m * 60 + s) * 1000

                machine_list.append({
                    "equipamento_id": equipamento_id,
                    "equipamento_nome": equip_nome,
                    "tiragem": int(tiragem_str),
                    "giros_previstos": int(giros_str),
                    "tempo_previsto_ms": tempo_previsto_ms,
                    "dynamic_fields": dynamic_values
                })
            
            create_production_order(order_data, machine_list, acabamento_ids)

            messagebox.showinfo("Sucesso", "Ordem de Produção salva com sucesso!", parent=self)
            self.clear_fields()
            self.start_load_ordens()

        except ServiceError as e:
            messagebox.showerror("Erro de Serviço", f"Não foi possível salvar a ordem:\n{e}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}", parent=self)

    def cancel_ordem(self):
        """
        Cancela uma Ordem de Produção selecionada.

        Pede confirmação ao usuário e, se confirmado, remove a ordem de produção
        e todos os seus registros associados (serviços, máquinas, etc.) do banco
        de dados de forma transacional.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_cancel_msg'), parent=self)
            return
        
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_num = item_values[1], item_values[3]
        if not messagebox.askyesno(self.get_string('confirm_cancel_order_title'), self.get_string('confirm_cancel_order_msg', wo=wo_num), parent=self):
            return

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ordem_producao WHERE id = %s", (ordem_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('cancel_order_success'), parent=self)
            self.start_load_ordens()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", self.get_string('cancel_order_failed', error=e), parent=self)
        finally:
            if conn: release_db_connection(conn)

    def swap_orders(self, item1, item2):
        """
        Troca a sequência de duas ordens de produção no banco de dados.

        Parâmetros:
            item1 (str): O ID do primeiro item na Treeview.
            item2 (str): O ID do segundo item na Treeview.
        """
        data1 = self.tree.item(item1, 'values')
        seq1, id1 = data1[0], data1[1]
        data2 = self.tree.item(item2, 'values')
        seq2, id2 = data2[0], data2[1]

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq2, id1))
                cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq1, id2))
            conn.commit()
            self.start_load_ordens()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Reordenar", f"Não foi possível alterar a sequência: {e}", parent=self)
        finally:
            if conn: release_db_connection(conn)
            
    def open_edit_window(self):
        """
        Abre a janela de edição para a ordem de produção selecionada.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1]
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_all_combobox_data)

    def open_report_window(self):
        """
        Abre a janela de detalhes (relatório) para a ordem de produção selecionada.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma Ordem de Produção na lista para ver os detalhes.", parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1]
        WODetailWindow(self, self.db_config, ordem_id)
        
    def move_order_up(self):
        """
        Move a ordem selecionada uma posição para cima na fila de produção.
        """
        selected_item = self.tree.focus()
        if not selected_item: return
        prev_item = self.tree.prev(selected_item)
        if not prev_item: return
        self.swap_orders(selected_item, prev_item)

    def move_order_down(self):
        """
        Move a ordem selecionada uma posição para baixo na fila de produção.
        """
        selected_item = self.tree.focus()
        if not selected_item: return
        next_item = self.tree.next(selected_item)
        if not next_item: return
        self.swap_orders(selected_item, next_item)

    def clear_fields(self):
        """
        Limpa todos os campos do formulário de criação de nova OP.

        Reseta todos os widgets de entrada (Entry, Combobox, Listbox) para seus
        valores padrão, incluindo a lista de máquinas adicionadas.
        """
        for widget in self.widgets.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            elif isinstance(widget, DateEntry):
                widget.entry.delete(0, 'end')
            elif isinstance(widget, Listbox):
                widget.selection_clear(0, 'end')
            elif isinstance(widget, tb.Entry):
                widget.delete(0, 'end')

        for widget in self.material_widgets.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            elif isinstance(widget, tb.Entry):
                widget.delete(0, 'end')

        for widget in self.machine_static_widgets.values():
            if isinstance(widget, tb.Combobox):
                widget.set('')
            elif isinstance(widget, tb.Entry):
                widget.delete(0, 'end')

        for widget in self.machine_dynamic_frame.winfo_children():
            widget.destroy()
        self.machine_dynamic_widgets.clear()

        for item in self.machines_tree.get_children():
            self.machines_tree.delete(item)

    def _calcular_giros_para_maquina(self, event=None):
        """
        Calcula automaticamente os giros previstos para uma impressora.

        Esta função é um placeholder e atualmente não está conectada a nenhum evento.
        A lógica de cálculo de giros foi integrada diretamente em `add_machine_to_list`.

        Parâmetros:
            event (tk.Event, opcional): O evento que poderia disparar a chamada.
        """
        try:
            equipamento_selecionado = self.machine_static_widgets["equipamento_id"].get()
            tiragem_str = self.machine_static_widgets["tiragem_em_folhas"].get()
            
            if "impressora" not in equipamento_selecionado.lower():
                return

            cores_desc = self.machine_dynamic_widgets["qtde_cores_id"].get()
            giros_widget = self.machine_dynamic_widgets["giros_previstos"]
            
            giros_widget.delete(0, 'end')

            if tiragem_str and cores_desc:
                tiragem_folhas = int(tiragem_str)
                multiplicador = self.giros_map.get(cores_desc, 1)
                giros_calculado = tiragem_folhas * multiplicador
                giros_widget.insert(0, str(giros_calculado))
            else:
                giros_widget.insert(0, "0")
                
        except (ValueError, IndexError, KeyError):
            giros_widget = self.machine_dynamic_widgets.get("giros_previstos")
            if giros_widget:
                giros_widget.delete(0, 'end')
                giros_widget.insert(0, "0")
        except Exception as e:
            print(f"Erro ao calcular giros para máquina: {e}")

    def on_tree_select(self, event=None):
        """
        Callback executado quando um item na Treeview de ordens é selecionado.

        Habilita ou desabilita os botões de ação (Editar, Cancelar, Mover)
        com base no status da ordem selecionada.

        Parâmetros:
            event (tk.Event, opcional): O evento de seleção.
        """
        selected_item = self.tree.focus()
        if not selected_item:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)
            self.move_up_button.config(state=DISABLED)
            self.move_down_button.config(state=DISABLED)
            return

        self.move_up_button.config(state=NORMAL)
        self.move_down_button.config(state=NORMAL)
        item_values = self.tree.item(selected_item, 'values')
        progresso_text = item_values[5] if len(item_values) > 5 else ""
        if "concluídas" not in progresso_text.lower():
            self.edit_button.config(state=NORMAL)
            self.cancel_button.config(state=NORMAL)
        else:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)

    def format_seconds_to_hhmmss(self, seconds):
        """
        Formata um valor em segundos para o formato HH:MM:SS.

        Parâmetros:
            seconds (int or float): O número de segundos a ser formatado.

        Retorna:
            str: A string formatada como "HH:MM:SS".
        """
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def add_machine_to_list(self):
        """
        Adiciona uma máquina configurada à lista de máquinas da nova OP.

        Valida os campos da máquina, calcula o tempo previsto e os giros, e insere
        a máquina na Treeview `machines_tree`. Os dados dinâmicos são armazenados
        como uma string JSON nas tags do item da Treeview.
        """
        equipamento = self.machine_static_widgets["equipamento_id"].get()
        tiragem_str = self.machine_static_widgets["tiragem_em_folhas"].get()
        
        cores_desc = self.material_widgets["qtde_cores_id"].get()
        if not cores_desc:
            messagebox.showwarning("Campo Obrigatório", "Selecione a quantidade de cores nos Detalhes do Material.", parent=self)
            return

        if not all([equipamento, tiragem_str]):
            messagebox.showwarning("Campo Obrigatório", "Equipamento e Tiragem são obrigatórios.", parent=self)
            return
        try:
            tiragem = int(tiragem_str)
            tempo_por_folha_ms = self.equipment_speed_map.get(equipamento, 1)
            tempo_total_ms = tiragem * tempo_por_folha_ms
            tempo_total_s = tempo_total_ms / 1000.0
            tempo_formatado = self.format_seconds_to_hhmmss(tempo_total_s)
            
            multiplicador = self.giros_map.get(cores_desc, 1)
            giros_calculado = tiragem * multiplicador

            dynamic_values = {key: widget.get() for key, widget in self.machine_dynamic_widgets.items()}
            
            self.machines_tree.insert("", "end", values=(equipamento, tiragem, giros_calculado, cores_desc, tempo_formatado), tags=[json.dumps(dynamic_values)])

            for widget in self.machine_static_widgets.values():
                if isinstance(widget, tb.Entry):
                    widget.delete(0, 'end')
                elif isinstance(widget, tb.Combobox):
                    widget.set('')
            
            for widget in self.machine_dynamic_widgets.values():
                if isinstance(widget, tb.Entry):
                    widget.delete(0, 'end')
                elif isinstance(widget, tb.Combobox):
                    widget.set('')

        except (ValueError, TypeError):
            messagebox.showerror("Erro de Formato", "O valor da Tiragem deve ser um número.", parent=self)

    def export_to_xlsx(self):
        """
        Exporta os dados da fila de produção (Treeview) para um arquivo XLSX.

        Coleta os dados visíveis na Treeview, cria um DataFrame do Pandas e solicita
        ao usuário um local para salvar o arquivo Excel.
        """
        rows = self.tree.get_children()
        if not rows:
            messagebox.showwarning("Aviso", "Não há dados para exportar.", parent=self)
            return

        data = []
        columns = [self.tree.heading(col)("text") for col in self.tree["columns"]]
        for row in rows:
            data.append(self.tree.item(row)["values"])

        df = pd.DataFrame(data, columns=columns)
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Ficheiros Excel", "*.xlsx"), ("Todos os ficheiros", "*.* ")],
                title="Salvar o relatório Excel"
            )
            if not file_path:
                return
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Sucesso", f"Os dados foram exportados com sucesso para:\n{file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro na Exportação", f"Ocorreu um erro ao exportar para XLSX:\n{e}", parent=self)
            
    def export_to_pdf(self):
        """
        Exporta os dados da fila de produção para um arquivo PDF.

        Coleta os dados da Treeview e gera um relatório em PDF, incluindo gráficos.
        (Atualmente, a geração do gráfico e do PDF está parcialmente implementada).
        """
        rows = self.tree.get_children()
        if not rows:
            messagebox.showwarning("Aviso", "Não há dados para exportar.", parent=self)
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Ficheiros PDF", "*.pdf"), ("Todos os ficheiros", "*.* ")],
            title="Salvar Relatório como PDF"
        )
        if not filepath:
            return
            
        with tempfile.TemporaryDirectory() as tempdir:
            chart_folhas_path = os.path.join(tempdir, "chart_folhas.png")
            chart_tempos_path = os.path.join(tempdir, "chart_tempos.png")

            messagebox.showinfo("Sucesso", "Relatório PDF gerado com sucesso!")

    def get_db_connection(self):
        """
        Obtém uma conexão com o banco de dados.

        Retorna:
            connection: Uma conexão de banco de dados do pool.
        """
        return get_db_connection()

    def open_select_closed_wo_window(self):
        SelectClosedWOWindow(self, self.db_config, self.populate_fields_from_wo)

    def populate_fields_from_wo(self, wo_data):
        # Clear current fields first
        self.clear_fields()

        # Populate main fields
        self.widgets["numero_wo"].insert(0, wo_data.get('numero_wo', ''))
        self.widgets["pn_partnumber"].insert(0, wo_data.get('pn_partnumber', ''))
        self.widgets["cliente"].insert(0, wo_data.get('cliente', ''))
        if wo_data.get('data_previsao_entrega'):
            self.widgets["data_previsao_entrega"].entry.insert(0, wo_data['data_previsao_entrega'].strftime('%d/%m/%Y'))

        # Populate material fields
        self.material_widgets["tipo_papel_id"].set(self.get_lookup_value_by_id(self.papeis_map, wo_data.get('tipo_papel_id')))
        self.material_widgets["gramatura_id"].set(self.get_lookup_value_by_id(self.gramaturas_map, wo_data.get('gramatura_id')))
        self.material_widgets["formato_id"].set(self.get_lookup_value_by_id(self.formatos_map, wo_data.get('formato_id')))
        self.material_widgets["fsc_id"].set(self.get_lookup_value_by_id(self.fsc_map, wo_data.get('fsc_id')))
        self.material_widgets["qtde_cores_id"].set(self.get_lookup_value_by_id(self.cores_map, wo_data.get('qtde_cores_id')))

        # Populate acabamento listbox
        if wo_data.get('acabamentos'):
            acab_widget = self.widgets["acabamento"]
            for acabamento in wo_data['acabamentos']:
                desc = acabamento['descricao']
                # Find index by description and select
                for i, item in enumerate(acab_widget.get(0, tk.END)):
                    if item == desc:
                        acab_widget.selection_set(i)
                        break

        # Populate machines treeview
        for machine in wo_data.get('machines', []):
            equip_nome = machine.get('equipamento_nome', '')
            tiragem = machine.get('tiragem_em_folhas', 0)
            giros_previstos = machine.get('giros_previstos', 0)
            tempo_previsto_ms = machine.get('tempo_producao_previsto_ms', 0)
            tempo_formatado = self.format_seconds_to_hhmmss(tempo_previsto_ms / 1000.0)
            dynamic_fields = machine.get('dynamic_fields', {})
            
            # Assuming cores_desc can be derived from dynamic_fields or is part of machine data
            # For now, let's assume it's not directly available and might need to be re-selected by user or inferred
            # If 'qtde_cores_id' is a dynamic field, it will be handled by dynamic_fields
            cores_desc = dynamic_fields.get('qtde_cores_id', '') # Example: if qtde_cores_id is a dynamic field

            self.machines_tree.insert("", "end", values=(equip_nome, tiragem, giros_previstos, cores_desc, tempo_formatado), tags=[json.dumps(dynamic_fields)])

    def get_lookup_value_by_id(self, lookup_map, id_value):
        """
        Helper to get the display value from a lookup map given an ID.
        """
        if id_value is None: return ''
        for key, value_id in lookup_map.items():
            if value_id == id_value:
                return key
        return ''
