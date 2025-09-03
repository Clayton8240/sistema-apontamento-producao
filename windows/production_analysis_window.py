# -*- coding: utf-8 -*- 

# production_analysis_window.py

import tkinter as tk
from tkinter import messagebox, Toplevel, W, CENTER, BOTH, YES, X, Y, RIGHT, VERTICAL, HORIZONTAL, BOTTOM, NSEW, N, filedialog
from datetime import datetime
import psycopg2
import pandas as pd
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
import threading
import queue
import logging

# Configuração do logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Import para integrar Matplotlib com Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import get_db_connection, release_db_connection


class ProductionAnalysisWindow(Toplevel):
    """
    Uma janela de dashboard estilo Power BI para a visão do gerente, com KPIs,
    gráficos interativos e dados detalhados da produção.
    """
    def __init__(self, master, db_config):
        logging.debug("ProductionAnalysisWindow: __init__")
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        
        self.title("Análise de Produção")
        self.geometry("1800x950") 
        self.state('zoomed') 
        self.grab_set()

        self.graph_canvas = {}
        self.data_queue = queue.Queue()
        self.df = pd.DataFrame() # Dataframe para armazenar os dados carregados
        self.generic_filter_entries = {}

        self.create_widgets()
        self.load_filter_data()

    def get_db_connection(self):
        logging.debug("ProductionAnalysisWindow: get_db_connection")
        """
        Usa a função centralizada para obter a conexão com o banco de dados.
        """
        try:
            return get_db_connection()
        except psycopg2.Error as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados:\n{e}", parent=self)
            return None

    def create_widgets(self):
        logging.debug("ProductionAnalysisWindow: create_widgets")
        """Cria a estrutura principal da interface com painéis para filtros, KPIs e gráficos."""
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        main_frame.grid_rowconfigure(2, weight=1) 
        main_frame.grid_columnconfigure(0, weight=1)

        filters_frame = tb.LabelFrame(main_frame, text="Filtros do Relatório", bootstyle=PRIMARY, padding=10)
        filters_frame.grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=5)
        self.create_filter_controls(filters_frame)

        self.kpi_frame = tb.LabelFrame(main_frame, text="Indicadores Chave de Desempenho (KPIs)", bootstyle=INFO, padding=15)
        self.kpi_frame.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=5, pady=10)
        self.create_kpi_cards(self.kpi_frame)
        
        self.notebook = tb.Notebook(main_frame, bootstyle="primary")
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=NSEW, padx=5, pady=5)

        charts_frame = tb.Frame(self.notebook, padding=10)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure((0, 1), weight=1)
        self.notebook.add(charts_frame, text=" Análise Gráfica ")
        
        self.create_chart_placeholders(charts_frame)

        self.table_tab_frame = tb.Frame(self.notebook, padding=10)
        self.notebook.add(self.table_tab_frame, text=" Dados Detalhados ")

    def create_filter_controls(self, parent_frame):
        logging.debug("ProductionAnalysisWindow: create_filter_controls")
        """Cria os controles de filtro, agora com um seletor de fonte de dados."""
        source_frame = tb.Frame(parent_frame)
        source_frame.pack(fill=X, expand=YES, pady=(0, 10))
        tb.Label(source_frame, text="Fonte de Dados:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        self.data_source_combobox = tb.Combobox(source_frame, state="readonly", bootstyle=PRIMARY)
        self.data_source_combobox.pack(side=LEFT, fill=X, expand=YES)
        self.data_source_combobox.bind("<<ComboboxSelected>>", self.on_data_source_changed)

        self.dynamic_filters_frame = tb.Frame(parent_frame)
        self.dynamic_filters_frame.pack(fill=X, expand=YES, pady=5)

        buttons_frame = tb.Frame(parent_frame)
        buttons_frame.pack(fill=X, expand=YES, pady=(10, 0))

        self.filter_button = tb.Button(buttons_frame, text="Carregar Dados", bootstyle=SUCCESS, command=self.start_load_report_data)
        self.filter_button.pack(side=LEFT, padx=10)
        
        self.export_button = tb.Button(buttons_frame, text="Exportar para Excel", bootstyle=INFO, command=self.export_to_excel)
        self.export_button.pack(side=LEFT, padx=10)
        self.export_button.config(state=DISABLED)

    def on_data_source_changed(self, event=None):
        self.rebuild_dynamic_filters()
        source = self.data_source_combobox.get()
        if source == 'Relatório de Produção':
            self.notebook.tab(0, state="normal")
            self.kpi_frame.grid()
        else:
            self.notebook.tab(0, state="disabled")
            self.kpi_frame.grid_remove()
        self.create_detailed_table(self.table_tab_frame, table_name=source)

    def rebuild_dynamic_filters(self):
        for widget in self.dynamic_filters_frame.winfo_children():
            widget.destroy()

        self.generic_filter_entries = {}

        source = self.data_source_combobox.get()
        if source == 'Relatório de Produção':
            self.create_report_filters(self.dynamic_filters_frame)
            self.load_report_filter_data()
        elif source:
            self.create_generic_filters(self.dynamic_filters_frame, source)

    def create_generic_filters(self, parent_frame, table_name):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s 
                    ORDER BY ordinal_position;
                """, (table_name,))
                columns = [row[0] for row in cur.fetchall()]
                
                frame = tb.Frame(parent_frame)
                frame.pack(fill=X, expand=YES)
                
                num_filter_cols = 4
                for i, col_name in enumerate(columns):
                    row = i // num_filter_cols
                    col = (i % num_filter_cols) * 2
                    
                    tb.Label(frame, text=f"{col_name}:").grid(row=row, column=col, padx=(0, 5), pady=2, sticky='w')
                    entry = tb.Entry(frame, width=20)
                    entry.grid(row=row, column=col + 1, padx=(0, 15), pady=2, sticky='we')
                    self.generic_filter_entries[col_name] = entry
                
                for i in range(num_filter_cols * 2):
                    frame.grid_columnconfigure(i, weight=1 if i % 2 != 0 else 0)

        except Exception as e:
            messagebox.showerror("Erro ao Criar Filtros", f"Não foi possível buscar as colunas da tabela: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def create_report_filters(self, parent_frame):
        filter_row1 = tb.Frame(parent_frame)
        filter_row1.pack(fill=X, expand=YES, pady=5)

        tb.Label(filter_row1, text="Período: De").pack(side=LEFT, padx=(0, 5))
        self.start_date_entry = DateEntry(filter_row1, dateformat='%d/%m/%Y', bootstyle=PRIMARY)
        self.start_date_entry.pack(side=LEFT)
        
        tb.Label(filter_row1, text="Até").pack(side=LEFT, padx=5)
        self.end_date_entry = DateEntry(filter_row1, dateformat='%d/%m/%Y', bootstyle=PRIMARY)
        self.end_date_entry.pack(side=LEFT, padx=(0, 15))

        tb.Label(filter_row1, text="Cliente:").pack(side=LEFT, padx=(10, 5))
        self.client_combobox = tb.Combobox(filter_row1, state="readonly", width=25, bootstyle=PRIMARY)
        self.client_combobox.pack(side=LEFT, padx=(0, 15))
        
        tb.Label(filter_row1, text="Máquina:").pack(side=LEFT, padx=(10, 5))
        self.machine_combobox = tb.Combobox(filter_row1, state="readonly", width=25, bootstyle=PRIMARY)
        self.machine_combobox.pack(side=LEFT, padx=(0, 15))

        tb.Label(filter_row1, text="Operador:").pack(side=LEFT, padx=(10, 5))
        self.operator_combobox = tb.Combobox(filter_row1, state="readonly", width=25, bootstyle=PRIMARY)
        self.operator_combobox.pack(side=LEFT, padx=(0, 15))

        filter_row2 = tb.Frame(parent_frame)
        filter_row2.pack(fill=X, expand=YES, pady=5)

        tb.Label(filter_row2, text="Tipo de Papel:").pack(side=LEFT, padx=(0, 5))
        self.paper_type_combobox = tb.Combobox(filter_row2, state="readonly", width=20, bootstyle=PRIMARY)
        self.paper_type_combobox.pack(side=LEFT, padx=(0, 15))

        tb.Label(filter_row2, text="Gramatura:").pack(side=LEFT, padx=(10, 5))
        self.grammage_combobox = tb.Combobox(filter_row2, state="readonly", width=15, bootstyle=PRIMARY)
        self.grammage_combobox.pack(side=LEFT, padx=(0, 15))

        tb.Label(filter_row2, text="FSC:").pack(side=LEFT, padx=(10, 5))
        self.fsc_combobox = tb.Combobox(filter_row2, state="readonly", width=15, bootstyle=PRIMARY)
        self.fsc_combobox.pack(side=LEFT, padx=(0, 15))

    def load_filter_data(self):
        logging.debug("ProductionAnalysisWindow: load_filter_data")
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """
                )
                tables = [row[0] for row in cur.fetchall()]
                self.data_source_combobox['values'] = ['Relatório de Produção'] + tables
                self.data_source_combobox.set('Relatório de Produção')
                self.on_data_source_changed()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar fontes de dados: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def load_report_filter_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                def load_combo(query, combobox):
                    cur.execute(query)
                    combobox['values'] = [" "] + [row[0] for row in cur.fetchall()]
                
                load_combo("SELECT DISTINCT cliente FROM ordem_producao WHERE cliente IS NOT NULL ORDER BY cliente", self.client_combobox)
                load_combo("SELECT DISTINCT descricao FROM equipamentos_tipos ORDER BY descricao", self.machine_combobox)
                load_combo("SELECT DISTINCT nome FROM impressores ORDER BY nome", self.operator_combobox)
                load_combo("SELECT DISTINCT descricao FROM tipos_papel ORDER BY descricao", self.paper_type_combobox)
                load_combo("SELECT DISTINCT valor FROM gramaturas_tipos ORDER BY valor", self.grammage_combobox)
                load_combo("SELECT DISTINCT descricao FROM fsc_tipos ORDER BY descricao", self.fsc_combobox)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar dados para os filtros: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def create_kpi_cards(self, parent_frame):
        logging.debug("ProductionAnalysisWindow: create_kpi_cards")
        kpi_specs = {
            "oee": {"title": "OEE (Eficiência Geral)", "value": "0.00%", "style": SUCCESS},
            "total_produzido": {"title": "Total Produzido", "value": "0", "style": PRIMARY},
            "total_perdas": {"title": "Total de Perdas", "value": "0", "style": DANGER},
            "tempo_paradas": {"title": "Tempo de Paradas", "value": "00:00:00", "style": WARNING},
        }
        
        parent_frame.grid_columnconfigure(list(range(len(kpi_specs))), weight=1)

        for i, (key, spec) in enumerate(kpi_specs.items()):
            card_frame = tb.Frame(parent_frame, bootstyle=LIGHT, padding=10)
            card_frame.grid(row=0, column=i, sticky=NSEW, padx=5, pady=5)
            
            title_label = tb.Label(card_frame, text=spec['title'], font=("Helvetica", 10, "bold"), bootstyle=SECONDARY)
            title_label.pack()
            
            value_label = tb.Label(card_frame, text=spec['value'], font=("Helvetica", 22, "bold"), bootstyle=spec['style'])
            value_label.pack(pady=5)
            
            setattr(self, f"kpi_{key}_label", value_label)

    def create_chart_placeholders(self, parent_frame):
        logging.debug("ProductionAnalysisWindow: create_chart_placeholders")
        f1 = tb.LabelFrame(parent_frame, text="Produção vs. Perdas por Máquina", bootstyle=DEFAULT, padding=5)
        f1.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        self.graph_canvas['machine_perf'] = tk.Frame(f1) 
        self.graph_canvas['machine_perf'].pack(fill=BOTH, expand=YES)
        
        f2 = tb.LabelFrame(parent_frame, text="Produção ao Longo do Tempo", bootstyle=DEFAULT, padding=5)
        f2.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5)
        self.graph_canvas['prod_time'] = tk.Frame(f2)
        self.graph_canvas['prod_time'].pack(fill=BOTH, expand=YES)

        f3 = tb.LabelFrame(parent_frame, text="Composição das Perdas", bootstyle=DEFAULT, padding=5)
        f3.grid(row=1, column=0, sticky=NSEW, padx=5, pady=5)
        self.graph_canvas['loss_pie'] = tk.Frame(f3)
        self.graph_canvas['loss_pie'].pack(fill=BOTH, expand=YES)

        f4 = tb.LabelFrame(parent_frame, text="Top 10 Operadores por Produção", bootstyle=DEFAULT, padding=5)
        f4.grid(row=1, column=1, sticky=NSEW, padx=5, pady=5)
        self.graph_canvas['op_perf'] = tk.Frame(f4)
        self.graph_canvas['op_perf'].pack(fill=BOTH, expand=YES)

    def create_detailed_table(self, parent_frame, table_name=None):
        logging.debug(f"ProductionAnalysisWindow: create_detailed_table for {table_name}")
        if hasattr(self, 'tree_container'):
            self.tree_container.destroy()
        
        self.tree_container = tb.Frame(parent_frame)
        self.tree_container.pack(fill=BOTH, expand=YES)
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)

        if not table_name:
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                if table_name and table_name != 'Relatório de Produção':
                    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position;", (table_name,))
                    cols = [row[0] for row in cur.fetchall()]
                    headers = cols
                else:
                    cols = ('data_ordem', 'wo', 'cliente', 'servico', 'maquina', 'operador',
                            'tipo_papel', 'gramatura', 'fsc',
                            'meta_qtd', 'prod_qtd', 'saldo_qtd', 'perdas_setup', 'perdas_prod',
                            'tempo_setup', 'tempo_prod', 'tempo_parada', 'eficiencia')
                    headers = ('Data', 'WO', 'Cliente', 'Serviço', 'Máquina', 'Operador',
                               'Tipo Papel', 'Gramatura', 'FSC',
                               'Meta Qtd', 'Prod. Qtd', 'Saldo Qtd', 'Perdas Setup', 'Perdas Prod.',
                               'T. Setup', 'T. Produção', 'T. Parada', 'Eficiência %')

                self.tree = tb.Treeview(self.tree_container, columns=cols, show="headings")
                for col, header in zip(cols, headers):
                    self.tree.heading(col, text=header, anchor=W)
                    self.tree.column(col, width=120, anchor=W)

                scrollbar_y = tb.Scrollbar(self.tree_container, orient=VERTICAL, command=self.tree.yview)
                scrollbar_x = tb.Scrollbar(self.tree_container, orient=HORIZONTAL, command=self.tree.xview)
                self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
                
                self.tree.grid(row=0, column=0, sticky=NSEW)
                scrollbar_y.grid(row=0, column=1, sticky='ns')
                scrollbar_x.grid(row=1, column=0, sticky='ew')
        except Exception as e:
            messagebox.showerror("Erro ao criar tabela", f"Não foi possível gerar a tabela dinâmica: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def format_seconds_to_hhmmss(self, seconds):
        logging.debug(f"ProductionAnalysisWindow: format_seconds_to_hhmmss with seconds: {seconds}")
        if pd.isna(seconds) or not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00:00"
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
        
    def start_load_report_data(self):
        logging.debug("ProductionAnalysisWindow: start_load_report_data")
        self.filter_button.config(state=DISABLED)
        self.export_button.config(state=DISABLED)
        self.config(cursor="watch")
        
        source = self.data_source_combobox.get()
        if not source:
            messagebox.showwarning("Seleção Necessária", "Por favor, selecione uma fonte de dados.", parent=self)
            self.filter_button.config(state=NORMAL)
            self.config(cursor="")
            return

        self.reset_dashboard()

        threading.Thread(target=self._background_load_report, daemon=True).start()
        self.after(100, self._check_load_report_queue)

    def _background_load_report(self):
        logging.debug("ProductionAnalysisWindow: _background_load_report")
        conn = None
        self.df = pd.DataFrame()
        try:
            conn = self.get_db_connection()
            if not conn:
                raise ConnectionError("Falha ao obter conexão com o banco de dados.")

            base_query, params = self.build_sql_query()
            
            with conn:
                self.df = pd.read_sql_query(base_query, conn, params=params)

            if self.df.empty:
                self.data_queue.put(None)
                return

            source = self.data_source_combobox.get()
            if source == 'Relatório de Produção':
                cols_to_fill = [
                    'meta_qtd', 'prod_qtd', 'perdas_setup', 'perdas_prod',
                    'tempo_setup_s', 'tempo_prod_s', 'tempo_parada_s', 'tempo_ciclo_ideal_s'
                ]
                for col in cols_to_fill:
                    if col in self.df.columns:
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
                
                kpi_results = self._calculate_kpis(self.df)
                chart_results = self._prepare_chart_data(self.df)
                table_results = self._prepare_table_data(self.df)

                self.data_queue.put({
                    "kpis": kpi_results,
                    "charts": chart_results,
                    "table": table_results
                })
            else:
                self.data_queue.put({"table_raw": self.df})

        except Exception as e:
            self.data_queue.put(e)
        finally:
            if conn:
                release_db_connection(conn)

    def _check_load_report_queue(self):
        logging.debug("ProductionAnalysisWindow: _check_load_report_queue")
        try:
            result = self.data_queue.get_nowait()

            self.config(cursor="")
            self.filter_button.config(state=NORMAL)

            if isinstance(result, Exception):
                messagebox.showerror("Erro ao Carregar Relatório", f"Ocorreu um erro inesperado: {result}", parent=self)
                self.reset_dashboard()
                return

            if result is None:
                messagebox.showinfo("Sem Dados", "Nenhum dado encontrado para os filtros selecionados.", parent=self)
                self.reset_dashboard()
                self.export_button.config(state=DISABLED)
                return

            if 'table_raw' in result:
                self.update_detailed_table(result['table_raw'])
            else:
                self.update_kpis(result["kpis"])
                self.update_charts(result["charts"])
                self.update_detailed_table(result["table"])
            
            self.export_button.config(state=NORMAL)

        except queue.Empty:
            self.after(100, self._check_load_report_queue)

    def build_sql_query(self):
        logging.debug("ProductionAnalysisWindow: build_sql_query")
        source = self.data_source_combobox.get()
        params = []
        
        if source == 'Relatório de Produção':
            query = """
                SELECT
                    op.data_cadastro_pcp AS data_ordem,
                    op.numero_wo,
                    op.cliente,
                    os.descricao AS servico,
                    et.descricao AS maquina,
                    imp.nome AS operador,
                    tp.descricao AS tipo_papel,
                    gt.valor AS gramatura,
                    ft.descricao AS fsc,
                    opm.tiragem_em_folhas AS meta_qtd,
                    ap.quantidadeproduzida AS prod_qtd,
                    COALESCE(aps.perdas, 0) AS perdas_setup,
                    COALESCE(ap.perdas_producao, 0) AS perdas_prod,
                    EXTRACT(EPOCH FROM (aps.hora_fim - aps.hora_inicio)) AS tempo_setup_s,
                    EXTRACT(EPOCH FROM (ap.horafim - ap.horainicio)) AS tempo_prod_s,
                    (SELECT COALESCE(SUM(EXTRACT(EPOCH FROM (p.hora_fim_parada - p.hora_inicio_parada))), 0) 
                     FROM paradas p WHERE p.apontamento_id = ap.id) AS tempo_parada_s,
                    (et.tempo_por_folha_ms / 1000.0) AS tempo_ciclo_ideal_s
                FROM
                    ordem_producao op
                LEFT JOIN ordem_servicos os ON op.id = os.ordem_id
                LEFT JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                LEFT JOIN equipamentos_tipos et ON opm.equipamento_id = et.id
                LEFT JOIN apontamento ap ON os.id = ap.servico_id
                LEFT JOIN apontamento_setup aps ON os.id = aps.servico_id
                LEFT JOIN impressores imp ON ap.impressor_id = imp.id
                LEFT JOIN tipos_papel tp ON op.tipo_papel_id = tp.id
                LEFT JOIN gramaturas_tipos gt ON op.gramatura_id = gt.id
                LEFT JOIN fsc_tipos ft ON op.fsc_id = ft.id
            """
            filters = []
            if hasattr(self, 'start_date_entry') and self.start_date_entry.entry.get():
                try:
                    filters.append("op.data_cadastro_pcp >= %s")
                    params.append(datetime.strptime(self.start_date_entry.entry.get(), '%d/%m/%Y').date())
                except ValueError: pass
            if hasattr(self, 'end_date_entry') and self.end_date_entry.entry.get():
                try:
                    filters.append("op.data_cadastro_pcp <= %s")
                    params.append(datetime.strptime(self.end_date_entry.entry.get(), '%d/%m/%Y').date())
                except ValueError: pass
            if hasattr(self, 'client_combobox') and self.client_combobox.get():
                filters.append("op.cliente = %s")
                params.append(self.client_combobox.get())
            if hasattr(self, 'machine_combobox') and self.machine_combobox.get():
                filters.append("et.descricao = %s")
                params.append(self.machine_combobox.get())
            if hasattr(self, 'operator_combobox') and self.operator_combobox.get():
                filters.append("imp.nome = %s")
                params.append(self.operator_combobox.get())
            if hasattr(self, 'paper_type_combobox') and self.paper_type_combobox.get():
                filters.append("tp.descricao = %s")
                params.append(self.paper_type_combobox.get())
            if hasattr(self, 'grammage_combobox') and self.grammage_combobox.get():
                filters.append("gt.valor = %s")
                params.append(self.grammage_combobox.get())
            if hasattr(self, 'fsc_combobox') and self.fsc_combobox.get():
                filters.append("ft.descricao = %s")
                params.append(self.fsc_combobox.get())
            
            if filters:
                query += " WHERE " + " AND ".join(filters)
            query += " ORDER BY op.data_cadastro_pcp DESC, op.numero_wo"
        else:
            query = f'SELECT * FROM public.\"{source}\"'
            filters = []
            for col_name, entry_widget in self.generic_filter_entries.items():
                value = entry_widget.get()
                if value:
                    filters.append(f'\"{col_name}\"::text ILIKE %s')
                    params.append(f"%{value}%")
            
            if filters:
                query += " WHERE " + " AND ".join(filters)

        return query, params

    def reset_dashboard(self):
        logging.debug("ProductionAnalysisWindow: reset_dashboard")
        if hasattr(self, 'kpi_oee_label'):
            self.kpi_oee_label.config(text="0.00%")
            self.kpi_total_produzido_label.config(text="0")
            self.kpi_total_perdas_label.config(text="0")
            self.kpi_tempo_paradas_label.config(text="00:00:00")
        
        if hasattr(self, 'tree'):
            for i in self.tree.get_children():
                self.tree.delete(i)
            
        for canvas_frame in self.graph_canvas.values():
            for widget in canvas_frame.winfo_children():
                widget.destroy()

    def _calculate_kpis(self, df):
        logging.debug("ProductionAnalysisWindow: _calculate_kpis")
        total_produzido = df['prod_qtd'].sum()
        total_perdas_setup = df['perdas_setup'].sum()
        total_perdas_prod = df['perdas_prod'].sum()
        total_perdas = total_perdas_setup + total_perdas_prod
        total_paradas_s = df['tempo_parada_s'].sum()
        tempo_producao_real_s = df['tempo_prod_s'].sum()

        tempo_producao_planejado_s = tempo_producao_real_s + total_paradas_s
        disponibilidade = (tempo_producao_real_s / tempo_producao_planejado_s) if tempo_producao_planejado_s > 0 else 0

        tempo_ideal_total_s = (df['prod_qtd'] * df['tempo_ciclo_ideal_s']).sum()
        performance = (tempo_ideal_total_s / tempo_producao_real_s) if tempo_producao_real_s > 0 else 0

        total_fabricado = total_produzido + total_perdas_prod
        qualidade = total_produzido / total_fabricado if total_fabricado > 0 else 0

        oee = disponibilidade * performance * qualidade

        return {
            "oee": f"{oee:.2%}",
            "total_produzido": f"{int(total_produzido):,}".replace(',', '.'),
            "total_perdas": f"{int(total_perdas):,}".replace(',', '.'),
            "tempo_paradas": self.format_seconds_to_hhmmss(total_paradas_s)
        }

    def _prepare_chart_data(self, df):
        logging.debug("ProductionAnalysisWindow: _prepare_chart_data")
        machine_data = df.groupby('maquina').agg(
            prod_qtd=('prod_qtd', 'sum'),
            perdas_total=('perdas_prod', lambda x: x.sum() + df.loc[x.index, 'perdas_setup'].sum())
        ).reset_index()

        df_time = df.copy()
        time_data = pd.DataFrame()
        if not df_time.empty and 'data_ordem' in df_time.columns:
            df_time['data_ordem'] = pd.to_datetime(df_time['data_ordem'])
            time_data = df_time.groupby(df_time['data_ordem'].dt.date)['prod_qtd'].sum().reset_index()

        loss_data = pd.DataFrame({
            'Tipo de Perda': ['Perdas em Setup', 'Perdas em Produção'],
            'Quantidade': [df['perdas_setup'].sum(), df['perdas_prod'].sum()]
        })

        op_data = df.groupby('operador')['prod_qtd'].sum().nlargest(10).reset_index()

        return {
            "machine_perf": machine_data,
            "prod_time": time_data,
            "loss_pie": loss_data,
            "op_perf": op_data
        }

    def _prepare_table_data(self, df):
        logging.debug("ProductionAnalysisWindow: _prepare_table_data")
        table_rows = []
        for _, row in df.iterrows():
            saldo_qtd = (row['prod_qtd'] or 0) - (row['meta_qtd'] or 0)
            tempo_prod_s = row['tempo_prod_s'] or 0
            tempo_parada_s = row['tempo_parada_s'] or 0
            tempo_total_operacao = tempo_prod_s + tempo_parada_s
            eficiencia = (tempo_prod_s / tempo_total_operacao * 100) if tempo_total_operacao > 0 else 0

            values = (
                row['data_ordem'].strftime('%d/%m/%Y') if pd.notna(row['data_ordem']) else '',
                row['numero_wo'] or '', row['cliente'] or '', row['servico'] or '', row['maquina'] or '', row['operador'] or '-',
                row['tipo_papel'] or '', row['gramatura'] or '', row['fsc'] or '',
                f"{int(row['meta_qtd'] or 0):,}".replace(',', '.'),
                f"{int(row['prod_qtd'] or 0):,}".replace(',', '.'),
                f"{int(saldo_qtd):,}".replace(',', '.'),
                f"{int(row['perdas_setup'] or 0):,}".replace(',', '.'),
                f"{int(row['perdas_prod'] or 0):,}".replace(',', '.'),
                self.format_seconds_to_hhmmss(row['tempo_setup_s']),
                self.format_seconds_to_hhmmss(row['tempo_prod_s']),
                self.format_seconds_to_hhmmss(row['tempo_parada_s']),
                f"{eficiencia:.2f}%"
            )
            table_rows.append(values)
        return table_rows

    def update_kpis(self, kpi_data):
        logging.debug("ProductionAnalysisWindow: update_kpis")
        self.kpi_oee_label.config(text=kpi_data["oee"])
        self.kpi_total_produzido_label.config(text=kpi_data["total_produzido"])
        self.kpi_total_perdas_label.config(text=kpi_data["total_perdas"])
        self.kpi_tempo_paradas_label.config(text=kpi_data["tempo_paradas"])

    def update_charts(self, chart_data):
        logging.debug("ProductionAnalysisWindow: update_charts")
        self.draw_bar_chart(
            self.graph_canvas['machine_perf'], data=chart_data['machine_perf'], x_col='maquina',
            y_cols=['prod_qtd', 'perdas_total'], labels=['Produção', 'Perdas'],
            title='Produção vs. Perdas por Máquina', colors=['#28a745', '#dc3545']
        )
        
        self.draw_line_chart(
            self.graph_canvas['prod_time'], data=chart_data['prod_time'], x_col='data_ordem',
            y_col='prod_qtd', title='Evolução da Produção no Período'
        )
        
        self.draw_pie_chart(
            self.graph_canvas['loss_pie'], data=chart_data['loss_pie'], labels_col='Tipo de Perda',
            values_col='Quantidade', title='Composição das Perdas'
        )
        
        self.draw_bar_chart(
            self.graph_canvas['op_perf'], data=chart_data['op_perf'], x_col='operador',
            y_cols=['prod_qtd'], labels=['Produção'], title='Top 10 Operadores por Produção',
            colors=['#17a2b8']
        )

    def update_detailed_table(self, data):
        logging.debug("ProductionAnalysisWindow: update_detailed_table")
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        if isinstance(data, pd.DataFrame):
            for i in self.tree.get_children():
                self.tree.delete(i)
            df_str = data.astype(str).replace('nan', '')
            for row in df_str.itertuples(index=False, name=None):
                self.tree.insert("", "end", values=row)
        else:
            for values in data:
                self.tree.insert("", "end", values=values)
    
    def _clear_canvas(self, canvas_frame):
        logging.debug("ProductionAnalysisWindow: _clear_canvas")
        for widget in canvas_frame.winfo_children():
            widget.destroy()

    def draw_bar_chart(self, canvas_frame, data, x_col, y_cols, labels, title, colors):
        logging.debug("ProductionAnalysisWindow: draw_bar_chart")
        self._clear_canvas(canvas_frame)
        if data.empty: return
        
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        x = range(len(data[x_col]))
        bar_width = 0.35
        
        for i, (y_col, label, color) in enumerate(zip(y_cols, labels, colors)):
            ax.bar([pos + i * bar_width for pos in x], data[y_col], width=bar_width, label=label, color=color)

        ax.set_title(title, fontsize=12)
        ax.set_xlabel('')
        ax.set_ylabel('Quantidade')
        ax.set_xticks([pos + bar_width / 2 * (len(y_cols) - 1) for pos in x])
        ax.set_xticklabels(data[x_col])
        ax.tick_params(axis='x', labelrotation=25, labelsize=8)
        ax.legend()
        fig.tight_layout(pad=1.5)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def draw_line_chart(self, canvas_frame, data, x_col, y_col, title):
        logging.debug("ProductionAnalysisWindow: draw_line_chart")
        self._clear_canvas(canvas_frame)
        if data.empty: return

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(data[x_col], data[y_col], marker='o', linestyle='-')
        ax.set_title(title, fontsize=12)
        ax.tick_params(axis='x', labelrotation=45, labelsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.6)
        fig.tight_layout(pad=1.5)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def draw_pie_chart(self, canvas_frame, data, labels_col, values_col, title):
        logging.debug("ProductionAnalysisWindow: draw_pie_chart")
        self._clear_canvas(canvas_frame)
        if data[values_col].sum() == 0: return

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        colors = ['#ffc107', '#dc3545']
        
        ax.pie(data[values_col], labels=data[labels_col], autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title(title, fontsize=12)
        ax.axis('equal')
        fig.tight_layout(pad=1.5)
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def export_to_excel(self):
        logging.debug("ProductionAnalysisWindow: export_to_excel")
        if self.df.empty:
            messagebox.showwarning("Nenhum Dado", "Não há dados para exportar.", parent=self)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
            title="Salvar Relatório como Excel"
        )
        if not file_path:
            return

        try:
            df_export = self.df.copy()
            source = self.data_source_combobox.get()

            if source == 'Relatório de Produção':
                for col in ['tempo_setup_s', 'tempo_prod_s', 'tempo_parada_s']:
                    if col in df_export.columns:
                        df_export[col] = df_export[col].apply(self.format_seconds_to_hhmmss)
                
                column_mapping = {
                    'data_ordem': 'Data Ordem', 'numero_wo': 'WO', 'cliente': 'Cliente', 'servico': 'Serviço',
                    'maquina': 'Máquina', 'operador': 'Operador', 'tipo_papel': 'Tipo Papel', 'gramatura': 'Gramatura',
                    'fsc': 'FSC', 'meta_qtd': 'Meta Qtd', 'prod_qtd': 'Produzido Qtd', 'perdas_setup': 'Perdas Setup',
                    'perdas_prod': 'Perdas Produção', 'tempo_setup_s': 'Tempo Setup', 'tempo_prod_s': 'Tempo Produção',
                    'tempo_parada_s': 'Tempo Parada', 'tempo_ciclo_ideal_s': 'Ciclo Ideal (s)'
                }
                df_export.rename(columns=column_mapping, inplace=True)
                
                export_cols = [
                    'Data Ordem', 'WO', 'Cliente', 'Serviço', 'Máquina', 'Operador', 'Tipo Papel', 'Gramatura', 'FSC',
                    'Meta Qtd', 'Produzido Qtd', 'Perdas Setup', 'Perdas Produção', 'Tempo Setup', 'Tempo Produção', 'Tempo Parada'
                ]
                export_cols_exist = [col for col in export_cols if col in df_export.columns]
                df_export = df_export[export_cols_exist]

            df_export.to_excel(file_path, index=False, engine='openpyxl')
            messagebox.showinfo("Exportação Concluída", f"Relatório salvo com sucesso em:\n{file_path}", parent=self)

        except Exception as e:
            logging.error(f"Erro ao exportar para Excel: {e}")
            messagebox.showerror("Erro de Exportação", f"Não foi possível salvar o arquivo.\nErro: {e}", parent=self)
