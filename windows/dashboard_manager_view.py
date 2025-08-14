# -*- coding: utf-8 -*-

# dashboard_manager_view.py

import tkinter as tk
from tkinter import messagebox, Toplevel, W, CENTER, BOTH, YES, X, Y, RIGHT, VERTICAL, HORIZONTAL, BOTTOM, NSEW, N
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


class DashboardManagerView(Toplevel):
    """
    Uma janela de dashboard estilo Power BI para a visão do gerente, com KPIs,
    gráficos interativos e dados detalhados da produção.
    """
    def __init__(self, master, db_config):
        logging.debug("DashboardManagerView: __init__")
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        
        self.title("Dashboard do Gerente - Análise de Produção Completa")
        self.geometry("1800x950") 
        self.state('zoomed') 
        self.grab_set()

        self.graph_canvas = {}
        self.data_queue = queue.Queue()

        self.create_widgets()
        self.load_filter_data()
        self.start_load_report_data()

    def get_db_connection(self):
        logging.debug("DashboardManagerView: get_db_connection")
        """
        Usa a função centralizada para obter a conexão com o banco de dados.
        """
        try:
            return get_db_connection()
        except psycopg2.Error as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados:\n{e}", parent=self)
            return None

    def create_widgets(self):
        logging.debug("DashboardManagerView: create_widgets")
        """Cria a estrutura principal da interface com painéis para filtros, KPIs e gráficos."""
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        main_frame.grid_rowconfigure(2, weight=1) 
        main_frame.grid_columnconfigure(0, weight=1)

        filters_frame = tb.LabelFrame(main_frame, text="Filtros do Relatório", bootstyle=PRIMARY, padding=10)
        filters_frame.grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=5, pady=5)
        self.create_filter_controls(filters_frame)

        kpi_frame = tb.LabelFrame(main_frame, text="Indicadores Chave de Desempenho (KPIs)", bootstyle=INFO, padding=15)
        kpi_frame.grid(row=1, column=0, columnspan=2, sticky=NSEW, padx=5, pady=10)
        self.create_kpi_cards(kpi_frame)
        
        notebook = tb.Notebook(main_frame, bootstyle="primary")
        notebook.grid(row=2, column=0, columnspan=2, sticky=NSEW, padx=5, pady=5)

        charts_frame = tb.Frame(notebook, padding=10)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure((0, 1), weight=1)
        notebook.add(charts_frame, text=" Análise Gráfica ")
        
        self.create_chart_placeholders(charts_frame)

        table_frame = tb.Frame(notebook, padding=10)
        notebook.add(table_frame, text=" Dados Detalhados ")
        self.create_detailed_table(table_frame)

    def create_filter_controls(self, parent_frame):
        logging.debug("DashboardManagerView: create_filter_controls")
        """Cria os controles de filtro (data, cliente, máquina)."""
        tb.Label(parent_frame, text="Período: De").pack(side=LEFT, padx=(0, 5))
        self.start_date_entry = DateEntry(parent_frame, dateformat='%d/%m/%Y', bootstyle=PRIMARY)
        self.start_date_entry.pack(side=LEFT)
        
        tb.Label(parent_frame, text="Até").pack(side=LEFT, padx=5)
        self.end_date_entry = DateEntry(parent_frame, dateformat='%d/%m/%Y', bootstyle=PRIMARY)
        self.end_date_entry.pack(side=LEFT, padx=(0, 20))

        tb.Label(parent_frame, text="Cliente:").pack(side=LEFT, padx=(10, 5))
        self.client_combobox = tb.Combobox(parent_frame, state="readonly", width=30, bootstyle=PRIMARY)
        self.client_combobox.pack(side=LEFT, padx=(0, 20))
        
        tb.Label(parent_frame, text="Máquina:").pack(side=LEFT, padx=(10, 5))
        self.machine_combobox = tb.Combobox(parent_frame, state="readonly", width=30, bootstyle=PRIMARY)
        self.machine_combobox.pack(side=LEFT, padx=(0, 20))
        
        self.filter_button = tb.Button(parent_frame, text="Aplicar Filtros", bootstyle=SUCCESS, command=self.start_load_report_data)
        self.filter_button.pack(side=LEFT, padx=10)

    def create_kpi_cards(self, parent_frame):
        logging.debug("DashboardManagerView: create_kpi_cards")
        """Cria os cartões para exibir os principais indicadores."""
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
        logging.debug("DashboardManagerView: create_chart_placeholders")
        """Cria os frames onde os gráficos serão desenhados."""
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

    def create_detailed_table(self, parent_frame):
        logging.debug("DashboardManagerView: create_detailed_table")
        """Cria a tabela para exibir dados brutos detalhados."""
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        
        cols = ('data_ordem', 'wo', 'cliente', 'servico', 'maquina', 'operador',
                'meta_qtd', 'prod_qtd', 'saldo_qtd', 'perdas_setup', 'perdas_prod',
                'tempo_setup', 'tempo_prod', 'tempo_parada', 'eficiencia')
        headers = ('Data', 'WO', 'Cliente', 'Serviço', 'Máquina', 'Operador',
                   'Meta Qtd', 'Prod. Qtd', 'Saldo Qtd', 'Perdas Setup', 'Perdas Prod.',
                   'T. Setup', 'T. Produção', 'T. Parada', 'Eficiência %')
        
        self.tree = tb.Treeview(parent_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header, anchor=W)
            self.tree.column(col, width=120, anchor=W)
        
        self.tree.column('cliente', width=200)
        self.tree.column('servico', width=250)

        scrollbar_y = tb.Scrollbar(parent_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar_x = tb.Scrollbar(parent_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.grid(row=0, column=0, sticky=NSEW)
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')

    def load_filter_data(self):
        logging.debug("DashboardManagerView: load_filter_data")
        """Carrega dados iniciais para os comboboxes de filtro."""
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT cliente FROM ordem_producao WHERE cliente IS NOT NULL ORDER BY cliente")
                self.client_combobox['values'] = [""] + [row[0] for row in cur.fetchall()]
                
                cur.execute("SELECT DISTINCT descricao FROM equipamentos_tipos ORDER BY descricao")
                self.machine_combobox['values'] = [""] + [row[0] for row in cur.fetchall()]
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar dados para os filtros: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)

    def format_seconds_to_hhmmss(self, seconds):
        logging.debug(f"DashboardManagerView: format_seconds_to_hhmmss with seconds: {seconds}")
        if pd.isna(seconds) or not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00:00"
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
        
    def start_load_report_data(self):
        logging.debug("DashboardManagerView: start_load_report_data")
        """Inicia o carregamento dos dados em uma thread separada para não bloquear a UI."""
        self.filter_button.config(state=DISABLED)
        self.config(cursor="watch")
        self.reset_dashboard()

        threading.Thread(target=self._background_load_report, daemon=True).start()
        self.after(100, self._check_load_report_queue)

    def _background_load_report(self):
        logging.debug("DashboardManagerView: _background_load_report")
        """Esta função roda em uma thread separada para buscar e processar os dados."""
        conn = None
        try:
            conn = self.get_db_connection()
            if not conn:
                raise ConnectionError("Falha ao obter conexão com o banco de dados.")

            base_query, params = self.build_sql_query()
            
            with conn:
                df = pd.read_sql_query(base_query, conn, params=params)

            if df.empty:
                self.data_queue.put(None)
                return

            cols_to_fill = [
                'meta_qtd', 'prod_qtd', 'perdas_setup', 'perdas_prod',
                'tempo_setup_s', 'tempo_prod_s', 'tempo_parada_s', 'tempo_ciclo_ideal_s'
            ]
            for col in cols_to_fill:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            kpi_results = self._calculate_kpis(df)
            chart_results = self._prepare_chart_data(df)
            table_results = self._prepare_table_data(df)

            self.data_queue.put({
                "kpis": kpi_results,
                "charts": chart_results,
                "table": table_results
            })

        except Exception as e:
            self.data_queue.put(e)
        finally:
            if conn:
                release_db_connection(conn)

    def _check_load_report_queue(self):
        logging.debug("DashboardManagerView: _check_load_report_queue")
        """Verifica a fila de dados e atualiza a UI quando os dados estiverem prontos."""
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
                return

            self.update_kpis(result["kpis"])
            self.update_charts(result["charts"])
            self.update_detailed_table(result["table"])

        except queue.Empty:
            self.after(100, self._check_load_report_queue)

    def build_sql_query(self):
        logging.debug("DashboardManagerView: build_sql_query")
        """Constrói a consulta SQL com base nos filtros da interface, usando a VIEW."""
        query = "SELECT * FROM mv_relatorio_producao_consolidado"
        filters = []
        params = []

        start_date = self.start_date_entry.entry.get()
        if start_date:
            try:
                filters.append("data_ordem >= %s")
                params.append(datetime.strptime(start_date, '%d/%m/%Y').date())
            except ValueError: pass

        end_date = self.end_date_entry.entry.get()
        if end_date:
            try:
                filters.append("data_ordem <= %s")
                params.append(datetime.strptime(end_date, '%d/%m/%Y').date())
            except ValueError: pass

        if self.client_combobox.get():
            filters.append("cliente = %s")
            params.append(self.client_combobox.get())

        if self.machine_combobox.get():
            filters.append("maquina = %s")
            params.append(self.machine_combobox.get())

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY data_ordem DESC, numero_wo"
        return query, params

    def reset_dashboard(self):
        logging.debug("DashboardManagerView: reset_dashboard")
        """Limpa todos os dados da tela."""
        self.kpi_oee_label.config(text="0.00%")
        self.kpi_total_produzido_label.config(text="0")
        self.kpi_total_perdas_label.config(text="0")
        self.kpi_tempo_paradas_label.config(text="00:00:00")
        
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        for canvas_frame in self.graph_canvas.values():
            for widget in canvas_frame.winfo_children():
                widget.destroy()

    def _calculate_kpis(self, df):
        logging.debug("DashboardManagerView: _calculate_kpis")
        """Calcula os KPIs a partir do DataFrame. Roda em background."""
        total_produzido = df['prod_qtd'].sum()
        total_perdas_setup = df['perdas_setup'].sum()
        total_perdas_prod = df['perdas_prod'].sum()
        total_perdas = total_perpas_setup + total_perdas_prod
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
        logging.debug("DashboardManagerView: _prepare_chart_data")
        """Prepara os DataFrames para cada gráfico. Roda em background."""
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
        logging.debug("DashboardManagerView: _prepare_table_data")
        """Prepara os dados formatados para a tabela. Roda em background."""
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
        logging.debug("DashboardManagerView: update_kpis")
        """Atualiza os valores nos cartões de KPI com dados pré-calculados."""
        self.kpi_oee_label.config(text=kpi_data["oee"])
        self.kpi_total_produzido_label.config(text=kpi_data["total_produzido"])
        self.kpi_total_perdas_label.config(text=kpi_data["total_perdas"])
        self.kpi_tempo_paradas_label.config(text=kpi_data["tempo_paradas"])

    def update_charts(self, chart_data):
        logging.debug("DashboardManagerView: update_charts")
        """Redesenha todos os gráficos com dados pré-agregados."""
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

    def update_detailed_table(self, table_data):
        logging.debug("DashboardManagerView: update_detailed_table")
        """Popula a tabela de dados detalhados com dados pré-formatados."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        for values in table_data:
            self.tree.insert("", "end", values=values)
    
    def _clear_canvas(self, canvas_frame):
        logging.debug("DashboardManagerView: _clear_canvas")
        for widget in canvas_frame.winfo_children():
            widget.destroy()

    def draw_bar_chart(self, canvas_frame, data, x_col, y_cols, labels, title, colors):
        logging.debug("DashboardManagerView: draw_bar_chart")
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
        logging.debug("DashboardManagerView: draw_line_chart")
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
        logging.debug("DashboardManagerView: draw_pie_chart")
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