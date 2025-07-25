# -*- coding: utf-8 -*-

from datetime import datetime
import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import messagebox, Toplevel, END, W, CENTER, BOTH, YES, X, Y, RIGHT, VERTICAL, HORIZONTAL, BOTTOM, NSEW

from config import LANGUAGES

class ManagerViewWindow(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.master.current_language
        
        self.title("Visão do Gerente - Relatório de Produção Consolidado")
        self.geometry("1600x800") # Aumentei a largura para as novas colunas
        self.grab_set()

        self.create_widgets()
        self.load_filter_data()
        self.load_report_data() # Por enquanto, esta função está vazia

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES.get('portugues', {}))
        return lang_dict.get(key, f"_{key}_").format(**kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        # --- PAINEL DE FILTROS (Permanece o mesmo) ---
        filters_frame = tb.LabelFrame(main_frame, text="Filtros do Relatório", bootstyle=PRIMARY, padding=10)
        filters_frame.pack(fill=X, pady=(0, 10), anchor=N)
        
        tb.Label(filters_frame, text="Período: De").pack(side=LEFT, padx=(0, 5))
        self.start_date_entry = DateEntry(filters_frame, dateformat='%d/%m/%Y')
        self.start_date_entry.pack(side=LEFT)
        
        tb.Label(filters_frame, text="Até").pack(side=LEFT, padx=5)
        self.end_date_entry = DateEntry(filters_frame, dateformat='%d/%m/%Y')
        self.end_date_entry.pack(side=LEFT, padx=(0, 20))

        tb.Label(filters_frame, text="Cliente:").pack(side=LEFT, padx=(10, 5))
        self.client_combobox = tb.Combobox(filters_frame, state="readonly", width=30)
        self.client_combobox.pack(side=LEFT, padx=(0, 20))
        
        tb.Label(filters_frame, text="Máquina:").pack(side=LEFT, padx=(10, 5))
        self.machine_combobox = tb.Combobox(filters_frame, state="readonly", width=30)
        self.machine_combobox.pack(side=LEFT, padx=(0, 20))
        
        self.filter_button = tb.Button(filters_frame, text="Aplicar Filtros", bootstyle=SUCCESS, command=self.load_report_data)
        self.filter_button.pack(side=LEFT, padx=10)
        
        self.export_button = tb.Button(filters_frame, text="Exportar para Excel", bootstyle="info-outline")
        self.export_button.pack(side=RIGHT, padx=10)

        # --- PAINEL DE TOTAIS (Permanece o mesmo) ---
        kpi_frame = tb.LabelFrame(main_frame, text="Totais Consolidados do Período", bootstyle=INFO, padding=15)
        kpi_frame.pack(fill=X, pady=10)
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.create_kpi_card(kpi_frame, "Total Produzido", "0", 0)
        self.create_kpi_card(kpi_frame, "Perdas Setup", "0", 1)
        self.create_kpi_card(kpi_frame, "Perdas Producao", "0", 2) # Sem 'ç' e 'ã'
        self.create_kpi_card(kpi_frame, "Tempo de Paradas", "00:00:00", 3)


        # --- TABELA DE DADOS DETALHADOS (ATUALIZADA) ---
        report_frame = tb.LabelFrame(main_frame, text="Relatório Detalhado", bootstyle=DEFAULT, padding=10)
        report_frame.pack(fill=BOTH, expand=YES)

        # >>> NOVAS COLUNAS ADICIONADAS <<<
        cols = (
            'wo', 'cliente', 'servico', 'acabamentos',
            'giros_prev', 'giros_real', 'giros_saldo',
            'qtd_meta', 'qtd_real',
            'tempo_prev', 'tempo_real', 'tempo_saldo',
            'tempo_setup', 'tempo_parada', 'operador'
        )
        headers = (
            'WO', 'Cliente', 'Serviço/Máquina', 'Acabamentos',
            'Giros Prev.', 'Giros Real.', 'Saldo Giros',
            'Qtd. Meta', 'Qtd. Real.',
            'Tempo Prev.', 'Tempo Real.', 'Saldo Tempo',
            'Tempo Setup', 'Tempo Paradas', 'Operador'
        )
        
        self.tree = tb.Treeview(report_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=110, anchor=CENTER) # Largura padrão

        # Ajuste de largura para colunas de texto
        self.tree.column('cliente', width=180, anchor=W)
        self.tree.column('servico', width=200, anchor=W)
        self.tree.column('acabamentos', width=250, anchor=W)

        scrollbar_y = tb.Scrollbar(report_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar_x = tb.Scrollbar(report_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=RIGHT, fill=Y)
        scrollbar_x.pack(side=BOTTOM, fill=X)
        self.tree.pack(fill=BOTH, expand=YES)

    def create_kpi_card(self, parent, title, value, col):
        card_frame = tb.Frame(parent, bootstyle=LIGHT, padding=10)
        card_frame.grid(row=0, column=col, sticky=NSEW, padx=5, pady=5)
        title_label = tb.Label(card_frame, text=title, font=("Helvetica", 10, "bold"), bootstyle=SECONDARY)
        title_label.pack()
        value_label = tb.Label(card_frame, text=value, font=("Helvetica", 22, "bold"), bootstyle=PRIMARY)
        value_label.pack(pady=5)
        
        # >>> CORREÇÃO: Limpando o título para criar um nome de atributo seguro <<<
        safe_title = title.lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a')
        safe_title = safe_title.replace('(', '').replace(')', '')
        attr_name = f"kpi_{safe_title}_label"
        
        setattr(self, attr_name, value_label)

    def format_seconds_to_hhmmss(self, seconds):
        if not isinstance(seconds, (int, float)) or seconds < 0:
            return "00:00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def load_filter_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT cliente FROM ordem_producao ORDER BY cliente")
                self.client_combobox['values'] = [""] + [row[0] for row in cur.fetchall() if row[0]]
                
                cur.execute("SELECT DISTINCT descricao FROM equipamentos_tipos ORDER BY descricao")
                self.machine_combobox['values'] = [""] + [row[0] for row in cur.fetchall() if row[0]]
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar dados para os filtros: {e}", parent=self)
        finally:
            if conn: conn.close()


        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = self.get_db_connection()
        if not conn: return

        try:
            with conn.cursor() as cur:
                # A consulta SQL foi corrigida para usar op.data_cadastro_pcp
                base_query = """
                    WITH SetupAndProductionTimes AS (
                        SELECT
                            ap.servico_id,
                            s.id as setup_id,
                            EXTRACT(EPOCH FROM (s.hora_fim - s.hora_inicio)) AS tempo_total_setup_s,
                            EXTRACT(EPOCH FROM (ap.horafim - ap.horainicio)) AS tempo_total_producao_s,
                            s.perdas AS perdas_setup,
                            ap.perdas_producao,
                            ap.quantidadeproduzida,
                            i.nome AS operador_nome,
                            t.descricao AS turno_nome
                        FROM apontamento ap
                        LEFT JOIN apontamento_setup s ON ap.servico_id = s.servico_id
                        LEFT JOIN impressores i ON ap.impressor_id = i.id
                        LEFT JOIN turnos_tipos t ON ap.turno_id = t.id
                    ),
                    StopTimes AS (
                        SELECT
                            a.servico_id,
                            COALESCE(SUM(EXTRACT(EPOCH FROM (p_setup.hora_fim_parada - p_setup.hora_inicio_parada))), 0) AS tempo_paradas_setup_s,
                            COALESCE(SUM(EXTRACT(EPOCH FROM (p_prod.hora_fim_parada - p_prod.hora_inicio_parada))), 0) AS tempo_paradas_prod_s
                        FROM apontamento a
                        LEFT JOIN apontamento_setup s ON a.servico_id = s.servico_id
                        LEFT JOIN paradas_setup p_setup ON p_setup.setup_id = s.id
                        LEFT JOIN paradas p_prod ON p_prod.apontamento_id = a.id
                        GROUP BY a.servico_id
                    )
                    SELECT 
                        -- >>> CORREÇÃO AQUI: Usando a data da Ordem de Produção (op) <<<
                        op.data_cadastro_pcp::date AS data_ordem,
                        op.numero_wo,
                        op.cliente,
                        os.descricao AS servico_descricao,
                        spt.operador_nome,
                        spt.turno_nome,
                        opm.tiragem_em_folhas AS meta_quantidade,
                        spt.quantidadeproduzida AS quantidade_produzida,
                        (spt.quantidadeproduzida - opm.tiragem_em_folhas) AS saldo,
                        spt.perdas_setup,
                        spt.perdas_producao,
                        spt.tempo_total_setup_s,
                        spt.tempo_total_producao_s,
                        (COALESCE(st.tempo_paradas_setup_s, 0) + COALESCE(st.tempo_paradas_prod_s, 0)) as tempo_total_paradas_s,
                        CASE 
                            WHEN (spt.tempo_total_producao_s > 0)
                            THEN ROUND((spt.tempo_total_producao_s / (spt.tempo_total_producao_s + COALESCE(st.tempo_paradas_prod_s, 0))) * 100, 2)
                            ELSE 0 
                        END AS eficiencia_percentual
                    FROM ordem_servicos os
                    JOIN ordem_producao op ON os.ordem_id = op.id
                    JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                    LEFT JOIN equipamentos_tipos et ON opm.equipamento_id = et.id
                    LEFT JOIN SetupAndProductionTimes spt ON os.id = spt.servico_id
                    LEFT JOIN StopTimes st ON os.id = st.servico_id
                """
                
                filters = []
                params = []
                
                start_date_str = self.start_date_entry.entry.get()
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
                    # >>> CORREÇÃO AQUI: Filtrando pela data da Ordem de Produção (op) <<<
                    filters.append("op.data_cadastro_pcp::date >= %s")
                    params.append(start_date)

                end_date_str = self.end_date_entry.entry.get()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
                    # >>> CORREÇÃO AQUI: Filtrando pela data da Ordem de Produção (op) <<<
                    filters.append("op.data_cadastro_pcp::date <= %s")
                    params.append(end_date)
                    
                client = self.client_combobox.get()
                if client:
                    filters.append("op.cliente = %s")
                    params.append(client)
                    
                machine = self.machine_combobox.get()
                if machine:
                    filters.append("et.descricao = %s")
                    params.append(machine)

                if filters:
                    base_query += " WHERE " + " AND ".join(filters)
                
                base_query += " ORDER BY op.data_cadastro_pcp DESC, op.numero_wo, os.sequencia ASC;"

                cur.execute(base_query, tuple(params))
                rows = cur.fetchall()
                
                total_produzido = 0
                total_perda_setup = 0
                total_perda_prod = 0
                total_paradas_s = 0

                for row in rows:
                    (data_ordem, wo, cliente, servico, operador, turno, meta, prod, saldo, p_setup, p_prod, t_setup, t_prod, t_parada, eficiencia) = row

                    t_setup_fmt = self.format_seconds_to_hhmmss(t_setup)
                    t_prod_fmt = self.format_seconds_to_hhmmss(t_prod)
                    t_parada_fmt = self.format_seconds_to_hhmmss(t_parada)
                    
                    values = (
                        data_ordem.strftime('%d/%m/%Y') if data_ordem else '',
                        wo or '', cliente or '', servico or '', operador or '-', turno or '-',
                        meta or 0, prod or 0, saldo or 0,
                        p_setup or 0, p_prod or 0,
                        t_setup_fmt, t_prod_fmt, t_parada_fmt, f"{eficiencia or 0:.2f}%"
                    )
                    self.tree.insert("", "end", values=values)
                    
                    total_produzido += prod or 0
                    total_perda_setup += p_setup or 0
                    total_perda_prod += p_prod or 0
                    total_paradas_s += t_parada or 0

                self.kpi_total_produzido_label.config(text=f"{total_produzido:,}".replace(',', '.'))
                self.kpi_perdas_setup_label.config(text=f"{total_perda_setup:,}".replace(',', '.'))
                self.kpi_perdas_producao_label.config(text=f"{total_perda_prod:,}".replace(',', '.'))
                self.kpi_tempo_de_paradas_label.config(text=self.format_seconds_to_hhmmss(total_paradas_s))

        except psycopg2.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao carregar relatório: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}", parent=self)
        finally:
            if conn: conn.close()

    def load_report_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = self.get_db_connection()
        if not conn: return

        try:
            with conn.cursor() as cur:
                # Consulta SQL reestruturada para máxima robustez
                base_query = """
                    WITH 
                    -- Passo 1: Juntar apontamentos de setup e produção a partir dos serviços
                    ApontamentosCompletos AS (
                        SELECT
                            os.id as servico_id,
                            ap.id as apontamento_id,
                            s.id as setup_id,
                            EXTRACT(EPOCH FROM (s.hora_fim - s.hora_inicio)) AS tempo_setup_real_s,
                            EXTRACT(EPOCH FROM (ap.horafim - ap.horainicio)) AS tempo_producao_real_s,
                            s.perdas AS perdas_setup,
                            ap.perdas_producao,
                            ap.quantidadeproduzida,
                            i.nome AS operador_nome,
                            t.descricao AS turno_nome
                        FROM ordem_servicos os
                        LEFT JOIN apontamento ap ON os.id = ap.servico_id
                        LEFT JOIN apontamento_setup s ON os.id = s.servico_id
                        LEFT JOIN impressores i ON ap.impressor_id = i.id
                        LEFT JOIN turnos_tipos t ON ap.turno_id = t.id
                    ),
                    -- Passo 2: Calcular todas as paradas associadas
                    TemposDeParada AS (
                        SELECT
                            ac.servico_id,
                            COALESCE(SUM(EXTRACT(EPOCH FROM (ps.hora_fim_parada - ps.hora_inicio_parada))), 0) AS tempo_paradas_setup_s,
                            COALESCE(SUM(EXTRACT(EPOCH FROM (pp.hora_fim_parada - pp.hora_inicio_parada))), 0) AS tempo_paradas_prod_s
                        FROM ApontamentosCompletos ac
                        LEFT JOIN paradas_setup ps ON ps.setup_id = ac.setup_id
                        LEFT JOIN paradas pp ON pp.apontamento_id = ac.apontamento_id
                        GROUP BY ac.servico_id
                    )
                    -- Passo 3: Juntar tudo para o relatório final
                    SELECT 
                        op.data_cadastro_pcp::date AS data_ordem,
                        op.numero_wo,
                        op.cliente,
                        os.descricao AS servico_descricao,
                        ac.operador_nome,
                        ac.turno_nome,
                        opm.tiragem_em_folhas AS meta_quantidade,
                        ac.quantidadeproduzida AS quantidade_produzida,
                        (ac.quantidadeproduzida - opm.tiragem_em_folhas) AS saldo,
                        ac.perdas_setup,
                        ac.perdas_producao,
                        ac.tempo_setup_real_s,
                        ac.tempo_producao_real_s,
                        (COALESCE(tdp.tempo_paradas_setup_s, 0) + COALESCE(tdp.tempo_paradas_prod_s, 0)) as tempo_total_paradas_s,
                        CASE 
                            WHEN (ac.tempo_producao_real_s > 0)
                            THEN ROUND((ac.tempo_producao_real_s / (ac.tempo_producao_real_s + COALESCE(tdp.tempo_paradas_prod_s, 0))) * 100, 2)
                            ELSE 0 
                        END AS eficiencia_percentual
                    FROM ordem_servicos os
                    JOIN ordem_producao op ON os.ordem_id = op.id
                    JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                    LEFT JOIN equipamentos_tipos et ON opm.equipamento_id = et.id
                    LEFT JOIN ApontamentosCompletos ac ON os.id = ac.servico_id
                    LEFT JOIN TemposDeParada tdp ON os.id = tdp.servico_id
                """
                
                filters = []
                params = []
                
                start_date_str = self.start_date_entry.entry.get()
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
                    filters.append("op.data_cadastro_pcp::date >= %s")
                    params.append(start_date)

                end_date_str = self.end_date_entry.entry.get()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
                    filters.append("op.data_cadastro_pcp::date <= %s")
                    params.append(end_date)
                    
                client = self.client_combobox.get()
                if client:
                    filters.append("op.cliente = %s")
                    params.append(client)
                    
                machine = self.machine_combobox.get()
                if machine:
                    filters.append("et.descricao = %s")
                    params.append(machine)

                if filters:
                    base_query += " WHERE " + " AND ".join(filters)
                
                base_query += " ORDER BY op.data_cadastro_pcp DESC, op.numero_wo, os.sequencia ASC;"

                cur.execute(base_query, tuple(params))
                rows = cur.fetchall()
                
                total_produzido = 0
                total_perda_setup = 0
                total_perda_prod = 0
                total_paradas_s = 0

                for row in rows:
                    (data_ordem, wo, cliente, servico, operador, turno, meta, prod, saldo, p_setup, p_prod, t_setup, t_prod, t_parada, eficiencia) = row

                    t_setup_fmt = self.format_seconds_to_hhmmss(t_setup)
                    t_prod_fmt = self.format_seconds_to_hhmmss(t_prod)
                    t_parada_fmt = self.format_seconds_to_hhmmss(t_parada)
                    
                    values = (
                        data_ordem.strftime('%d/%m/%Y') if data_ordem else '',
                        wo or '', cliente or '', servico or '', operador or '-', turno or '-',
                        meta or 0, prod or 0, saldo or 0,
                        p_setup or 0, p_prod or 0,
                        t_setup_fmt, t_prod_fmt, t_parada_fmt, f"{eficiencia or 0:.2f}%"
                    )
                    self.tree.insert("", "end", values=values)
                    
                    total_produzido += prod or 0
                    total_perda_setup += p_setup or 0
                    total_perda_prod += p_prod or 0
                    total_paradas_s += t_parada or 0

                self.kpi_total_produzido_label.config(text=f"{total_produzido:,}".replace(',', '.'))
                self.kpi_perdas_setup_label.config(text=f"{total_perda_setup:,}".replace(',', '.'))
                self.kpi_perdas_producao_label.config(text=f"{total_perda_prod:,}".replace(',', '.')) # Nome corrigido
                self.kpi_tempo_de_paradas_label.config(text=self.format_seconds_to_hhmmss(total_paradas_s))

        except psycopg2.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao carregar relatório: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}", parent=self)
        finally:
            if conn:
                conn.close()