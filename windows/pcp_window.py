# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Listbox, Canvas, VERTICAL, HORIZONTAL, DISABLED, NORMAL
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
import pandas as pd
from datetime import datetime
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt

# --- 1. Importações Corrigidas ---
from database import get_db_connection, release_db_connection
from schemas import LOOKUP_TABLE_SCHEMAS
from languages import LANGUAGES

# Importa as outras janelas que esta classe precisa abrir
from .edit_order_window import EditOrdemWindow
from .wo_detail_window import WODetailWindow
from .service_manager_window import ServiceManagerWindow

class PCPWindow(tb.Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')
        self.title(self.get_string('btn_pcp_management'))
        self.geometry("1200x950")

        self.transient(master)
        self.focus_set()

        # Configurações da janela (sem alterações)
        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"},
            "pn_partnumber": {"label_key": "PN (Partnumber)", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"},
            "data_previsao_entrega": {"label_key": "col_data_previsao", "widget": "DateEntry"},
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

    # A função get_db_connection() foi removida daqui.

    def create_widgets(self):
        # (Seu método create_widgets original e completo)
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

        form_frame = tb.LabelFrame(main_frame, text=self.get_string('new_order_section'), bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor='n')
        form_frame.grid_columnconfigure((0, 1), weight=1)

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
        
        machines_frame = tb.LabelFrame(main_frame, text="Detalhes de Produção por Máquina", bootstyle=INFO, padding=10)
        machines_frame.pack(fill=X, pady=10)
        machines_frame.grid_columnconfigure((1, 3), weight=1)

        for i, (key, config) in enumerate(self.machine_fields_left.items()):
            tb.Label(machines_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky='w')
            widget = self.create_widget_from_config(machines_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
            self.machine_widgets[key] = widget
        
        for i, (key, config) in enumerate(self.machine_fields_right.items()):
            tb.Label(machines_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=2, padx=5, pady=5, sticky='w')
            widget = self.create_widget_from_config(machines_frame, config)
            widget.grid(row=i, column=3, padx=5, pady=5, sticky='ew')
            self.machine_widgets[key] = widget
            
        self.machine_widgets["tiragem_em_folhas"].bind("<KeyRelease>", self._calcular_giros_para_maquina)
        self.machine_widgets["qtde_cores_id"].bind("<<ComboboxSelected>>", self._calcular_giros_para_maquina)
        self.machine_widgets["equipamento_id"].bind("<<ComboboxSelected>>", self._calcular_giros_para_maquina)

        tb.Button(machines_frame, text="Adicionar Máquina à Lista", command=self.add_machine_to_list, bootstyle=SUCCESS).grid(row=len(self.machine_fields_left), column=0, columnspan=4, pady=10)

        tree_actions_frame = tb.Frame(main_frame)
        tree_actions_frame.pack(fill=X, pady=10)

        cols = ("equipamento", "tiragem", "giros", "cores", "papel", "gramatura", "tempo_previsto")
        headers = ("Equipamento", "Tiragem", "Giros", "Cores", "Papel", "Gramatura", "Tempo Previsto")
        self.machines_tree = tb.Treeview(tree_actions_frame, columns=cols, show="headings", height=5)
        for col, header in zip(cols, headers):
            self.machines_tree.heading(col, text=header)
            self.machines_tree.column(col, width=150, anchor=CENTER)
        self.machines_tree.pack(side='left', fill=X, expand=True)
        
        tb.Button(tree_actions_frame, text="Remover Selecionada", command=self.remove_selected_machine, bootstyle=DANGER).pack(side='left', padx=10, fill='y')

        final_buttons_frame = tb.Frame(main_frame)
        final_buttons_frame.pack(fill=X, pady=10)
        tb.Button(final_buttons_frame, text=self.get_string('save_btn'), command=self.save_new_ordem, bootstyle=SUCCESS).pack(side='left', padx=5)
        tb.Button(final_buttons_frame, text=self.get_string('clear_filters_btn'), command=self.clear_fields, bootstyle=SECONDARY).pack(side='left', padx=5)

        action_frame = tb.Frame(main_frame)
        action_frame.pack(fill=X, pady=10)
        
        self.move_up_button = tb.Button(action_frame, text="Subir na Fila", command=self.move_order_up, bootstyle="primary-outline", state=DISABLED)
        self.move_up_button.pack(side='left', padx=5)
        self.move_down_button = tb.Button(action_frame, text="Descer na Fila", command=self.move_order_down, bootstyle="primary-outline", state=DISABLED)
        self.move_down_button.pack(side='left', padx=(0, 20))
        self.edit_button = tb.Button(action_frame, text="Alterar Ordem Selecionada", command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
        self.edit_button.pack(side='left', padx=5)
        self.cancel_button = tb.Button(action_frame, text="Cancelar Ordem Selecionada", command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
        self.cancel_button.pack(side='left', padx=5)
        tb.Button(action_frame, text="Ver Relatório", command=self.open_report_window, bootstyle="info-outline").pack(side='left', padx=(20, 0))
        self.export_button = tb.Button(action_frame, text="Exportar para XLSX", command=self.export_to_xlsx, bootstyle="success-outline")
        self.export_button.pack(side='right', padx=5)
        self.pdf_export_button = tb.Button(action_frame, text="Exportar para PDF", command=self.export_to_pdf, bootstyle="danger-outline")
        self.pdf_export_button.pack(side='right', padx=5)
        
        orders_tree_frame = tb.LabelFrame(main_frame, text="Ordens de Produção Criadas", bootstyle=INFO, padding=10)
        orders_tree_frame.pack(fill=BOTH, expand=True, pady=10)
        
        cols_orders = ("sequencia", "id", "wo", "cliente", "progresso", "data_previsao", "status_atraso")
        headers_orders = ("Seq.", "ID", "WO", "Cliente", "Progresso da Produção", "Data Prev.", "Status Atraso")
        
        self.tree = tb.Treeview(orders_tree_frame, columns=cols_orders, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols_orders, headers_orders):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=120, anchor='w')

        self.tree.column("progresso", width=250, anchor='w')
        self.tree.column("sequencia", width=40, anchor=CENTER)
        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("status_atraso", width=100, anchor=CENTER)
        self.tree.tag_configure('atrasado', foreground='red', font=('-weight bold'))

        self.tree.pack(side='left', fill=BOTH, expand=True)
        scrollbar = tb.Scrollbar(orders_tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def create_widget_from_config(self, parent, config):
        if config.get("widget") == "Combobox": return tb.Combobox(parent, state="readonly")
        elif config.get("widget") == "DateEntry": return DateEntry(parent, dateformat='%d/%m/%Y')
        else: return tb.Entry(parent)

    def load_all_combobox_data(self):
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}
                
                schemas = LOOKUP_TABLE_SCHEMAS
                
                for key, widget in self.machine_widgets.items():
                    if isinstance(widget, tb.Combobox):
                        config = self.machine_fields_left.get(key) or self.machine_fields_right.get(key, {})
                        lookup_ref = config.get("lookup")
                        if lookup_ref and lookup_ref in schemas:
                            schema_info = schemas[lookup_ref]
                            db_col = 'valor' if lookup_ref == 'gramaturas_tipos' else 'descricao'
                            cur.execute(f'SELECT DISTINCT "{db_col}" FROM {schema_info["table"]} ORDER BY "{db_col}"')
                            widget['values'] = [str(row[0]) for row in cur.fetchall()]

                acab_widget = self.widgets.get("acabamento")
                if acab_widget and isinstance(acab_widget, Listbox):
                    acab_widget.delete(0, 'end')
                    schema_info_acab = schemas["acabamentos_tipos"]
                    cur.execute(f'SELECT id, descricao FROM {schema_info_acab["table"]} ORDER BY descricao')
                    self.acabamentos_map = {}
                    for acab_id, desc in cur.fetchall():
                        acab_widget.insert('end', desc)
                        self.acabamentos_map[desc] = acab_id
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados dos comboboxes: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def load_ordens(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
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
                        op.sequencia_producao, op.id, op.numero_wo, op.cliente, 
                        op.data_previsao_entrega, ss.total_servicos, ss.servicos_concluidos,
                        ss.servico_em_producao, ss.proximo_servico_pendente, op.status as status_geral
                    FROM ordem_producao op
                    LEFT JOIN ServicoStatus ss ON op.id = ss.ordem_id
                    WHERE op.status IN ('Em Aberto', 'Em Produção')
                    ORDER BY op.sequencia_producao ASC;
                """
                cur.execute(sql_query)
                
                hoje = datetime.now().date()
                for row in cur.fetchall():
                    (seq, ordem_id, wo, cliente, previsao, total_servicos, concluidos, em_prod, pendente, status_geral) = row
                    
                    progresso_txt = "Sem serviços definidos"
                    if total_servicos and total_servicos > 0:
                        if em_prod:
                            progresso_txt = f"Etapa {concluidos + 1}/{total_servicos}: {em_prod} (Em Produção)"
                        elif pendente:
                            progresso_txt = f"Etapa {concluidos + 1}/{total_servicos}: {pendente} (Aguardando)"
                        elif concluidos == total_servicos:
                            progresso_txt = "Todas as etapas concluídas"

                    data_formatada = previsao.strftime('%d/%m/%Y') if previsao else ""
                    
                    status_atraso = ""
                    tags = ()
                    if previsao and previsao < hoje:
                        status_atraso = "ATRASADO"
                        tags = ('atrasado',)

                    values = (seq, ordem_id, wo, cliente, progresso_txt, data_formatada, status_atraso)
                    self.tree.insert("", "end", values=values, tags=tags)
                    
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar ordens de produção: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def remove_selected_machine(self):
        for item in self.machines_tree.selection():
            self.machines_tree.delete(item)

    def save_new_ordem(self):
        wo_number = self.widgets["numero_wo"].get()
        cliente = self.widgets["cliente"].get()
        if not wo_number or not cliente or not self.machines_tree.get_children():
            messagebox.showwarning("Validação", "WO, Cliente e ao menos uma máquina são obrigatórios.", parent=self)
            return

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                data_previsao_str = self.widgets["data_previsao_entrega"].entry.get()
                data_previsao = datetime.strptime(data_previsao_str, '%d/%m/%Y').date() if data_previsao_str else None
                pn_partnumber = self.widgets["pn_partnumber"].get()
                
                cur.execute("SELECT COALESCE(MAX(sequencia_producao), 0) + 1 FROM ordem_producao")
                next_seq = cur.fetchone()[0]
                
                query_op = """
                    INSERT INTO ordem_producao (numero_wo, pn_partnumber, cliente, data_previsao_entrega, sequencia_producao, status)
                    VALUES (%s, %s, %s, %s, %s, 'Em Aberto') RETURNING id;
                """
                cur.execute(query_op, (wo_number, pn_partnumber, cliente, data_previsao, next_seq))
                ordem_id = cur.fetchone()[0]

                sequencia_servico = 1
                for item in self.machines_tree.get_children():
                    (equip_nome, tiragem_str, giros_str, cores_nome, papel_nome, gramatura_valor, _) = self.machines_tree.item(item, 'values')
                    
                    cur.execute("SELECT id FROM equipamentos_tipos WHERE descricao = %s", (equip_nome,))
                    equipamento_id = cur.fetchone()[0]
                    
                    cur.execute("SELECT id FROM qtde_cores_tipos WHERE descricao = %s", (cores_nome,))
                    qtde_cores_id = cur.fetchone()[0] if cores_nome and cur.rowcount > 0 else None
                    
                    cur.execute("SELECT id FROM tipos_papel WHERE descricao = %s", (papel_nome,))
                    tipo_papel_id = cur.fetchone()[0] if papel_nome and cur.rowcount > 0 else None

                    cur.execute("SELECT id FROM gramaturas_tipos WHERE valor = %s", (str(gramatura_valor),))
                    gramatura_id = cur.fetchone()[0] if gramatura_valor and cur.rowcount > 0 else None
                    
                    query_maquina = """
                        INSERT INTO ordem_producao_maquinas (ordem_id, equipamento_id, tiragem_em_folhas, giros_previstos, tempo_producao_previsto_ms, qtde_cores_id, tipo_papel_id, gramatura_id, sequencia_producao)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                    """
                    cur.execute(query_maquina, (ordem_id, equipamento_id, int(tiragem_str), int(giros_str), int(tiragem_str), qtde_cores_id, tipo_papel_id, gramatura_id, sequencia_servico))
                    maquina_id = cur.fetchone()[0]

                    query_servico = """
                        INSERT INTO ordem_servicos (ordem_id, maquina_id, descricao, status, sequencia)
                        VALUES (%s, %s, %s, 'Pendente', %s);
                    """
                    cur.execute(query_servico, (ordem_id, maquina_id, equip_nome, sequencia_servico))
                    
                    sequencia_servico += 1

            conn.commit()
            messagebox.showinfo("Sucesso", "Ordem de Produção salva com sucesso!", parent=self)
            self.clear_fields()
            self.load_ordens()

        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível salvar a ordem:\n{e}", parent=self)
        finally:
            if conn: release_db_connection(conn)

    def cancel_ordem(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_cancel_msg'), parent=self)
            return
        
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_num = item_values[1], item_values[2]
        if not messagebox.askyesno(self.get_string('confirm_cancel_order_title'), self.get_string('confirm_cancel_order_msg', wo=wo_num), parent=self):
            return

        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ordem_producao WHERE id = %s", (ordem_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('cancel_order_success'), parent=self)
            self.load_ordens()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", self.get_string('cancel_order_failed', error=e), parent=self)
        finally:
            if conn: release_db_connection(conn)

    def swap_orders(self, item1, item2):
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
            self.load_ordens()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Reordenar", f"Não foi possível alterar a sequência: {e}", parent=self)
        finally:
            if conn: release_db_connection(conn)
            
    # --- Demais métodos da classe ---
    # (open_edit_window, open_report_window, export_to_xlsx, etc. permanecem os mesmos,
    # mas devem ser adaptados para usar o pool de conexões se fizerem acesso ao DB)

    def open_edit_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1]
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_all_combobox_data)

    def open_report_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma Ordem de Produção na lista para ver os detalhes.", parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1]
        WODetailWindow(self, self.db_config, ordem_id)
        
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

    def clear_fields(self):
        """Limpa todos os campos do formulário e a lista de máquinas."""
        for key, widget in self.widgets.items():
            if not widget: continue
            if isinstance(widget, tb.Combobox):
                widget.set('')
            elif isinstance(widget, DateEntry):
                widget.entry.delete(0, 'end')
            elif isinstance(widget, Listbox):
                widget.selection_clear(0, 'end')
            else:
                widget.delete(0, 'end')
        
        for widget in self.machine_widgets.values():
            if isinstance(widget, tb.Entry):
                widget.delete(0, 'end')
            elif isinstance(widget, tb.Combobox):
                widget.set('')

        for item in self.machines_tree.get_children():
            self.machines_tree.delete(item)

    def _calcular_giros_para_maquina(self, event=None):
        try:
            equipamento_selecionado = self.machine_widgets["equipamento_id"].get()
            tiragem_str = self.machine_widgets["tiragem_em_folhas"].get()
            cores_desc = self.machine_widgets["qtde_cores_id"].get()
            giros_widget = self.machine_widgets["giros_previstos"]
            
            giros_widget.delete(0, 'end')

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
                giros_widget.delete(0, 'end')
                giros_widget.insert(0, "0")
        except Exception as e:
            print(f"Erro ao calcular giros para máquina: {e}")

    def on_tree_select(self, event=None):
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
        progresso_text = item_values[4] if len(item_values) > 4 else ""
        if "concluídas" not in progresso_text.lower():
            self.edit_button.config(state=NORMAL)
            self.cancel_button.config(state=NORMAL)
        else:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)

    def format_seconds_to_hhmmss(self, seconds):
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
            tempo_por_folha_ms = self.equipment_speed_map.get(equipamento, 1)
            tempo_total_ms = tiragem * tempo_por_folha_ms
            tempo_total_s = tempo_total_ms / 1000.0
            tempo_formatado = self.format_seconds_to_hhmmss(tempo_total_s)
            
            giros = self.machine_widgets["giros_previstos"].get()
            cores = self.machine_widgets["qtde_cores_id"].get()
            papel = self.machine_widgets["tipo_papel_id"].get()
            gramatura = self.machine_widgets["gramatura_id"].get()

            values_to_insert = (equipamento, tiragem, giros, cores, papel, gramatura, tempo_formatado)
            self.machines_tree.insert("", "end", values=values_to_insert)

            for widget in self.machine_widgets.values():
                if isinstance(widget, tb.Entry): widget.delete(0, 'end')
                elif isinstance(widget, tb.Combobox): widget.set('')
            
            self._calcular_giros_para_maquina()
        except (ValueError, TypeError):
            messagebox.showerror("Erro de Formato", "O valor da Tiragem deve ser um número.", parent=self)

    def export_to_xlsx(self):
        rows = self.tree.get_children()
        if not rows:
            messagebox.showwarning("Aviso", "Não há dados para exportar.", parent=self)
            return

        data = []
        columns = [self.tree.heading(col)["text"] for col in self.tree["columns"]]
        for row in rows:
            data.append(self.tree.item(row)["values"])

        df = pd.DataFrame(data, columns=columns)
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Ficheiros Excel", "*.xlsx"), ("Todos os ficheiros", "*.*")],
                title="Salvar o relatório Excel"
            )
            if not file_path:
                return
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Sucesso", f"Os dados foram exportados com sucesso para:\n{file_path}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro na Exportação", f"Ocorreu um erro ao exportar para XLSX:\n{e}", parent=self)
            
    def export_to_pdf(self):
        # Esta função precisa ser adaptada para usar o pool de conexões
        messagebox.showinfo("Em desenvolvimento", "A exportação para PDF será implementada em breve.")