# -*- coding: utf-8 -*-

from datetime import datetime, time, date
import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Canvas, Toplevel, END, W, E, S, N, CENTER, BOTH, YES, X, Y, LEFT, RIGHT, DISABLED, NORMAL, VERTICAL
from tkinter.ttk import Treeview

from languages import LANGUAGES
from schemas import LOOKUP_TABLE_SCHEMAS
from database import get_db_connection, release_db_connection

# --- Constantes de Estilo ---
PAD_X = 10
PAD_Y = 5
PAD_Y_LARGE = 10
PAD_Y_XXL = 20
FRAME_PADDING = 10
TIMER_FONT = ('Helvetica', 20, 'bold')

class StopDetailsWindow(Toplevel):
    """Janela para visualizar os detalhes das paradas de um apontamento."""
    def __init__(self, master, stops_data, wo_number):
        super().__init__(master)
        self.master = master
        self.stops_data = stops_data
        self.wo_number = wo_number

        self.title(f"Detalhes de Parada - WO: {self.wo_number}")
        self.geometry("600x400")
        self.transient(master)
        self.grab_set()

        self.create_widgets()
        self.load_stops_data()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=FRAME_PADDING)
        main_frame.pack(fill=BOTH, expand=YES)

        cols = ("tipo", "motivo", "inicio", "fim", "duracao")
        headers = ("Tipo", "Motivo da Parada", "Hora Início", "Hora Fim", "Duração")
        self.tree = Treeview(main_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor=CENTER)
        self.tree.column("motivo", anchor=W, width=200)
        
        scrollbar = tb.Scrollbar(main_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)

    def load_stops_data(self):
        if not self.stops_data:
            tb.Label(self, text="Nenhuma parada registrada.").pack(pady=PAD_Y_XXL)
            return

        for stop in self.stops_data:
            start, end = stop.get('hora_inicio_parada'), stop.get('hora_fim_parada')
            start_str = start.strftime('%H:%M:%S') if start else ''
            end_str = end.strftime('%H:%M:%S') if end else ''

            duration_str = ""
            if start and end:
                try:
                    delta = datetime.combine(date.min, end) - datetime.combine(date.min, start)
                    duration_str = str(delta)
                except TypeError:
                    duration_str = "Erro de tipo"

            motivo_display = stop.get('motivo_text', '')
            if motivo_display and motivo_display.lower() == 'outros' and stop.get('motivo_extra_detail'):
                motivo_display = f"Outros: {stop['motivo_extra_detail']}"
            
            values = (stop.get('type', ''), motivo_display, start_str, end_str, duration_str)
            self.tree.insert("", END, values=values)

class App(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')

        self.transient(master)
        self.focus_set()

        self.set_localized_title()
        self.state('zoomed')
        self.wm_minsize(1280, 720)

        self.current_state = 'IDLE'
        self.setup_start_time, self.setup_end_time = None, None
        self.prod_start_time, self.prod_end_time = None, None
        self.setup_timer_job, self.prod_timer_job = None, None
        self.all_stops_data = []
        self.selected_ordem_id, self.selected_servico_id, self.setup_id = None, None, None
        self.pending_services_data, self.motivos_perda_data, self.giros_map = {}, {}, {}
        self.initial_fields, self.setup_fields, self.production_fields, self.info_labels = {}, {}, {}, {}

        self.create_widgets()
        self.load_initial_data()

        self.after(100, self.check_and_restore_state_from_db)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES.get('portugues', {}))
        return lang_dict.get(key, f"_{key}_").format(**kwargs)

    def set_localized_title(self):
        self.title(self.get_string('btn_production_entry'))

    def _clear_field_highlights(self):
        """Remove o destaque de erro de todos os campos de entrada."""
        all_fields = list(self.initial_fields.values()) + \
                     list(self.setup_fields.values()) + \
                     list(self.production_fields.values())
        
        for widget in all_fields:
            if widget is None: # Adiciona verificação para None
                continue
            # Verifica se o widget tem o método cget e se 'bootstyle' é uma opção válida
            if hasattr(widget, 'cget'):
                config_options = widget.configure()
                if config_options is not None and 'bootstyle' in config_options:
                    style = widget.cget('bootstyle')
                    if 'danger' in style:
                        widget.configure(bootstyle=style.replace('danger', ''))

    def create_widgets(self):
        # --- Configuração do Grid Principal ---
        self.grid_columnconfigure(0, weight=1) # Coluna Esquerda
        self.grid_columnconfigure(1, weight=1) # Coluna Direita
        self.grid_rowconfigure(1, weight=1)

        # --- COLUNA ESQUERDA ---
        left_column_frame = tb.Frame(self)
        left_column_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(PAD_X, PAD_Y), pady=PAD_Y)
        left_column_frame.grid_rowconfigure(1, weight=1)

        selection_frame = tb.LabelFrame(left_column_frame, text=self.get_string('initial_selection_section'), bootstyle=PRIMARY, padding=FRAME_PADDING)
        selection_frame.grid(row=0, column=0, sticky="new", pady=PAD_Y)
        selection_frame.grid_columnconfigure(1, weight=1)
        
        tb.Label(selection_frame, text=self.get_string('equipment_label') + ": *").grid(row=0, column=0, sticky=W, padx=PAD_X, pady=PAD_Y)
        self.equipment_combobox = tb.Combobox(selection_frame, state="readonly")
        self.equipment_combobox.grid(row=0, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)
        self.initial_fields['equipment'] = self.equipment_combobox
        self.equipment_combobox.bind("<<ComboboxSelected>>", self.on_equipment_select)

        tb.Label(selection_frame, text=self.get_string('service_on_machine_queue_label') + ": *").grid(row=1, column=0, sticky=W, padx=PAD_X, pady=PAD_Y)
        self.service_combobox = tb.Combobox(selection_frame, state="disabled")
        self.service_combobox.grid(row=1, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)
        self.initial_fields['service'] = self.service_combobox
        self.service_combobox.bind("<<ComboboxSelected>>", self.on_service_select)
        
        tb.Label(selection_frame, text=self.get_string("printer_label") + ": *").grid(row=2, column=0, sticky=W, padx=PAD_X, pady=PAD_Y)
        self.impressor_combobox = tb.Combobox(selection_frame, state="readonly")
        self.impressor_combobox.grid(row=2, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)
        self.initial_fields['impressor'] = self.impressor_combobox
        
        tb.Label(selection_frame, text=self.get_string("shift_label") + ": *").grid(row=3, column=0, sticky=W, padx=PAD_X, pady=PAD_Y)
        self.turno_combobox = tb.Combobox(selection_frame, state="readonly")
        self.turno_combobox.grid(row=3, column=1, sticky="ew", padx=PAD_X, pady=PAD_Y)
        self.initial_fields['turno'] = self.turno_combobox

        notebook = tb.Notebook(left_column_frame)
        notebook.grid(row=1, column=0, sticky='nsew', pady=PAD_Y)
        
        tab_setup = tb.Frame(notebook, padding=FRAME_PADDING)
        notebook.add(tab_setup, text='  Etapa 1: Setup  ')
        tab_setup.grid_columnconfigure(0, weight=1)

        self.setup_frame = tb.LabelFrame(tab_setup, text=self.get_string('setup_section'), bootstyle=INFO, padding=FRAME_PADDING)
        self.setup_frame.grid(row=0, column=0, sticky="nsew")
        self.setup_frame.grid_columnconfigure(0, weight=1)
        
        setup_entries_frame = tb.Frame(self.setup_frame)
        setup_entries_frame.pack(fill=X, expand=YES, pady=(0, PAD_Y_LARGE))
        setup_fields_defs = {'perdas': 'col_perdas', 'malas': 'col_malas', 'total_lavagens': 'col_total_lavagens', 'numero_inspecao': 'col_numeroinspecao'}
        for key, label_key in setup_fields_defs.items():
            tb.Label(setup_entries_frame, text=self.get_string(label_key) + ": *").pack(fill=X, pady=2)
            entry = tb.Entry(setup_entries_frame)
            entry.pack(fill=X)
            self.setup_fields[key] = entry
        
        setup_control_frame = tb.Frame(self.setup_frame)
        setup_control_frame.pack(fill=X, expand=YES)
        self.setup_timer_label = tb.Label(setup_control_frame, text="00:00:00", font=TIMER_FONT, bootstyle="info")
        self.setup_timer_label.pack(pady=PAD_Y)
        self.setup_button = tb.Button(setup_control_frame, text=self.get_string('start_setup_btn'), bootstyle="info", command=self.toggle_setup, width=20)
        self.setup_button.pack(pady=PAD_Y, ipady=PAD_Y)
        self.setup_stop_button = tb.Button(setup_control_frame, text=self.get_string('point_setup_stop_btn'), command=lambda: self.open_stop_window('setup'), state=DISABLED, width=20)
        self.setup_stop_button.pack(pady=PAD_Y, ipady=PAD_Y)

        tab_prod = tb.Frame(notebook, padding=FRAME_PADDING)
        notebook.add(tab_prod, text='  Etapa 2: Produção  ')
        tab_prod.grid_columnconfigure(0, weight=1)

        self.prod_frame = tb.LabelFrame(tab_prod, text=self.get_string('production_section'), bootstyle=SUCCESS, padding=FRAME_PADDING)
        self.prod_frame.grid(row=0, column=0, sticky="nsew")
        self.prod_frame.grid_columnconfigure(0, weight=1)

        prod_entries_frame = tb.Frame(self.prod_frame)
        prod_entries_frame.pack(fill=X, expand=YES, pady=(0, PAD_Y_LARGE))
        prod_fields_defs = {'giros_rodados': 'col_giros_rodados', 'quantidadeproduzida': 'col_quantidadeproduzida', 'perdas_producao': 'col_perdas_producao'}
        for key, label_key in prod_fields_defs.items():
            req = ": *" if key == 'quantidadeproduzida' else ":"
            tb.Label(prod_entries_frame, text=self.get_string(label_key) + req).pack(fill=X, pady=2)
            entry = tb.Entry(prod_entries_frame)
            entry.pack(fill=X)
            self.production_fields[key] = entry

        self.production_fields['quantidadeproduzida'].bind("<KeyRelease>", self._calcular_giros_rodados)
        self.production_fields['giros_rodados'].config(state=DISABLED)
        tb.Label(prod_entries_frame, text=self.get_string("col_motivo_perda") + ":").pack(fill=X, pady=2)
        self.motivo_perda_combobox = tb.Combobox(prod_entries_frame, state="readonly")
        self.motivo_perda_combobox.pack(fill=X)
        self.production_fields['motivo_perda'] = self.motivo_perda_combobox
        
        prod_control_frame = tb.Frame(self.prod_frame)
        prod_control_frame.pack(fill=X, expand=YES)
        self.prod_timer_label = tb.Label(prod_control_frame, text="00:00:00", font=TIMER_FONT, bootstyle="success")
        self.prod_timer_label.pack(pady=PAD_Y)
        self.prod_button = tb.Button(prod_control_frame, text=self.get_string('start_production_btn'), bootstyle="success", command=self.toggle_production, width=20)
        self.prod_button.pack(pady=PAD_Y, ipady=PAD_Y)
        self.prod_stop_button = tb.Button(prod_control_frame, text=self.get_string('point_prod_stop_btn'), command=lambda: self.open_stop_window('production'), state=DISABLED, width=20)
        self.prod_stop_button.pack(pady=PAD_Y, ipady=PAD_Y)

        # --- COLUNA DIREITA ---
        right_column_frame = tb.Frame(self)
        right_column_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(PAD_Y, PAD_X), pady=PAD_Y)
        right_column_frame.grid_rowconfigure(1, weight=1)

        self.wo_info_frame = tb.LabelFrame(right_column_frame, text=self.get_string('order_info_section'), bootstyle=PRIMARY, padding=FRAME_PADDING)
        self.wo_info_frame.grid(row=0, column=0, sticky="new")
        info_keys = {'col_wo': 'Nº WO', 'col_cliente': 'Cliente', 'equipment_label': 'Equipamento do Serviço', 'col_tipo_papel': 'Tipo Papel', 'col_tiragem_em_folhas': 'Tiragem Meta', 'giros_previstos': 'Giros Previstos', 'tempo_previsto': 'Tempo Previsto'}
        for i, (key, text) in enumerate(info_keys.items()):
            display_text = self.get_string(key) if self.get_string(key) != f"_{key}_" else text
            tb.Label(self.wo_info_frame, text=f"{display_text}:", font="-weight bold").grid(row=i, column=0, sticky=W, padx=PAD_X, pady=2)
            label_widget = tb.Label(self.wo_info_frame, text="-")
            label_widget.grid(row=i, column=1, sticky=W, padx=PAD_X, pady=2)
            self.info_labels[key] = label_widget

        stops_frame = tb.LabelFrame(right_column_frame, text=self.get_string('stops_history_section'), padding=FRAME_PADDING)
        stops_frame.grid(row=1, column=0, sticky='nsew', pady=(PAD_Y_LARGE, 0))
        stops_frame.grid_columnconfigure(0, weight=1)
        stops_frame.grid_rowconfigure(0, weight=1)

        self.stops_tree = Treeview(stops_frame, columns=('tipo', 'motivo', 'inicio', 'fim', 'duracao'), show='headings', height=5)
        self.stops_tree.heading('tipo', text="Tipo"); self.stops_tree.column('tipo', width=80, anchor=CENTER)
        self.stops_tree.heading('motivo', text="Motivo"); self.stops_tree.column('motivo', width=250)
        self.stops_tree.heading('inicio', text="Início"); self.stops_tree.column('inicio', width=100, anchor=CENTER)
        self.stops_tree.heading('fim', text="Fim"); self.stops_tree.column('fim', width=100, anchor=CENTER)
        self.stops_tree.heading('duracao', text="Duração"); self.stops_tree.column('duracao', width=100, anchor=CENTER)
        self.stops_tree.grid(row=0, column=0, sticky='nsew')

        stops_scrollbar = tb.Scrollbar(stops_frame, orient=VERTICAL, command=self.stops_tree.yview)
        stops_scrollbar.grid(row=0, column=1, sticky='ns')
        self.stops_tree.configure(yscrollcommand=stops_scrollbar.set)

        details_button = tb.Button(stops_frame, text="Ver Detalhes das Paradas", command=self.view_stop_details)
        details_button.grid(row=1, column=0, columnspan=2, pady=PAD_Y)
        
        # --- RODAPÉ ---
        footer_frame = tb.Frame(self)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        self.final_register_button = tb.Button(footer_frame, text=self.get_string("register_entry_btn"), command=self.submit_final_production, state=DISABLED)
        self.final_register_button.pack(pady=PAD_Y_XXL, ipady=PAD_Y_LARGE)
        
        status_bar = tb.Frame(self)
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew", padx=PAD_X, pady=(0, PAD_Y))
        tb.Label(status_bar, text="Status:", font="-size 12 -weight bold").pack(side=LEFT)
        self.status_label = tb.Label(status_bar, text=self.get_string('status_idle'), font="-size 12 -weight bold", bootstyle="secondary")
        self.status_label.pack(side=LEFT, padx=PAD_X)

    def set_cursor_watch(self):
        self.config(cursor="watch")
        self.update_idletasks()

    def set_cursor_default(self):
        if self.winfo_exists():
            self.config(cursor="")

    def load_initial_data(self):
        self.set_cursor_watch()
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}
                cur.execute('SELECT id, descricao FROM equipamentos_tipos ORDER BY descricao')
                self.equipments_data = {desc: eq_id for eq_id, desc in cur.fetchall()}
                self.equipment_combobox['values'] = list(self.equipments_data.keys())
                cur.execute('SELECT nome FROM impressores ORDER BY nome')
                self.impressor_combobox['values'] = [row[0] for row in cur.fetchall()]
                cur.execute('SELECT descricao FROM turnos_tipos ORDER BY id')
                self.turno_combobox['values'] = [row[0] for row in cur.fetchall()]
                cur.execute('SELECT id, descricao FROM motivos_perda_tipos ORDER BY descricao')
                self.motivos_perda_data = {desc: mid for mid, desc in cur.fetchall()}
                self.motivo_perda_combobox['values'] = list(self.motivos_perda_data.keys())
        except Exception as e:
            messagebox.showwarning(self.get_string('error_title_generic'), f"{self.get_string('load_initial_data_failed')}{e}", parent=self)
        finally:
            if 'conn' in locals() and conn: release_db_connection(conn)
            self.set_cursor_default()

    def update_wo_info_panel(self):
        if not self.selected_servico_id: return
        print(f"DEBUG: selected_servico_id: {self.selected_servico_id}") # Added debug print
        self.set_cursor_watch()
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                sql = """
                    SELECT op.numero_wo, op.cliente, et.descricao as equipamento_nome,
                           tp.descricao as tipo_papel, opm.giros_previstos,
                           opm.tiragem_em_folhas, opm.tempo_producao_previsto_ms,
                           qc.descricao as qtde_cores
                    FROM ordem_servicos os
                    JOIN ordem_producao op ON os.ordem_id = op.id
                    JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                    JOIN equipamentos_tipos et ON opm.equipamento_id = et.id
                    LEFT JOIN tipos_papel tp ON op.tipo_papel_id = tp.id
                    LEFT JOIN qtde_cores_tipos qc ON op.qtde_cores_id = qc.id
                    WHERE os.id = %s
                """
                cur.execute(sql, (self.selected_servico_id,))
                result = cur.fetchone()
                print(f"DEBUG: Query result: {result}") # Added debug print
                if result:
                    wo_num, cliente, equip, papel, giros, tiragem, tempo_ms, cores_desc = result
                    self.cores_desc = cores_desc
                    tempo_s = (tempo_ms / 1000.0) if tempo_ms else 0
                    info_map = {
                        'col_wo': wo_num, 'col_cliente': cliente, 'equipment_label': equip,
                        'col_tipo_papel': papel, 'col_tiragem_em_folhas': tiragem,
                        'giros_previstos': giros, 'tempo_previsto': self.format_seconds_to_hhmmss(tempo_s)
                    }
                    for key, value in info_map.items():
                        if key in self.info_labels:
                            self.info_labels[key].config(text=value if value is not None else '')
        except Exception as e:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar informações do serviço:\n{e}", parent=self)
        finally:
            if 'conn' in locals() and conn: release_db_connection(conn)
            self.set_cursor_default()

    def on_equipment_select(self, event=None):
        self.service_combobox.set('')
        self.service_combobox.config(state='disabled')
        self.pending_services_data = {}
        selected_equipment_name = self.equipment_combobox.get()
        equipment_id = self.equipments_data.get(selected_equipment_name)
        if not equipment_id: return
        
        self.set_cursor_watch()
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                query = """
                    SELECT os.id, op.numero_wo, os.descricao FROM ordem_servicos os
                    JOIN ordem_producao op ON os.ordem_id = op.id
                    JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                    WHERE opm.equipamento_id = %s AND os.status = 'Pendente'
                    ORDER BY op.sequencia_producao, os.sequencia;
                """
                cur.execute(query, (equipment_id,))
                services = cur.fetchall()
                if services:
                    service_list = [f"{wo}: {desc}" for s_id, wo, desc in services]
                    self.pending_services_data = {f"{wo}: {desc}": s_id for s_id, wo, desc in services}
                    self.service_combobox['values'] = service_list
                    self.service_combobox.config(state='readonly')
                else:
                    self.service_combobox.set("Nenhum serviço pendente para esta máquina")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar serviços: {e}", parent=self)
        finally:
            if 'conn' in locals() and conn: release_db_connection(conn)
            self.set_cursor_default()
        self.update_ui_state()

    def validate_and_save_setup(self):
        self._clear_field_highlights()
        invalid_widgets = []
        data = {}
        for key, widget in self.setup_fields.items():
            value = widget.get().strip()
            if not value:
                invalid_widgets.append(widget)
            data[key] = value

        if invalid_widgets:
            for widget in invalid_widgets:
                widget.configure(bootstyle='danger')
            messagebox.showerror("Campos Obrigatórios", self.get_string('setup_fields_required'), parent=self)
            return False

        self.set_cursor_watch()
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("UPDATE ordem_servicos SET status = 'Em Produção' WHERE id = %s", (self.selected_servico_id,))
                params = (self.setup_start_time.date(), self.setup_start_time, self.setup_end_time, int(data['perdas']), int(data['malas']), int(data['total_lavagens']), data['numero_inspecao'])
                if self.setup_id:
                    query = "UPDATE apontamento_setup SET data_apontamento=%s, hora_inicio=%s, hora_fim=%s, perdas=%s, malas=%s, total_lavagens=%s, numero_inspecao=%s WHERE id=%s"
                    cur.execute(query, params + (self.setup_id,))
                    cur.execute("DELETE FROM paradas_setup WHERE setup_id = %s", (self.setup_id,))
                else:
                    query = "INSERT INTO apontamento_setup (servico_id, data_apontamento, hora_inicio, hora_fim, perdas, malas, total_lavagens, numero_inspecao) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
                    cur.execute(query, (self.selected_servico_id,) + params)
                    self.setup_id = cur.fetchone()[0]

                for stop in self.all_stops_data:
                    if stop.get('type') == 'Setup':
                        cur.execute("INSERT INTO paradas_setup (setup_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s)",
                                    (self.setup_id, stop.get('motivo_id'), stop.get('hora_inicio_parada'), stop.get('hora_fim_parada'), stop.get('motivo_extra_detail')))
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('setup_saved_success'), parent=self)
            return True
        except (psycopg2.Error, ValueError) as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro", self.get_string('setup_save_failed', error=e), parent=self)
            return False
        finally:
            if conn: release_db_connection(conn)
            self.set_cursor_default()

    def submit_final_production(self):
        self._clear_field_highlights()
        required_fields = {
            'impressor': self.initial_fields['impressor'],
            'turno': self.initial_fields['turno'],
            'quantidadeproduzida': self.production_fields['quantidadeproduzida']
        }
        invalid_widgets = [w for w in required_fields.values() if not w.get().strip()]

        if invalid_widgets:
            for widget in invalid_widgets:
                widget.configure(bootstyle='danger')
            messagebox.showwarning("Campos Obrigatórios", "Quantidade Produzida, Impressor e Turno devem ser preenchidos.", parent=self)
            return

        try:
            quantidade_produzida = int(self.production_fields['quantidadeproduzida'].get())
            giros_rodados = int(self.production_fields['giros_rodados'].get() or 0)
            perdas_producao = int(self.production_fields['perdas_producao'].get() or 0)
            motivo_perda_texto = self.production_fields['motivo_perda'].get()
            impressor_nome = self.initial_fields['impressor'].get()
            turno_nome = self.initial_fields['turno'].get()
        except (ValueError, KeyError) as e:
            messagebox.showerror("Erro de Dados", f"Não foi possível ler os dados do formulário.\nDetalhe: {e}", parent=self)
            return

        self.set_cursor_watch()
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM impressores WHERE nome = %s", (impressor_nome,))
                impressor_id = cur.fetchone()[0] if cur.rowcount > 0 else None
                cur.execute("SELECT id FROM turnos_tipos WHERE descricao = %s", (turno_nome,))
                turno_id = cur.fetchone()[0] if cur.rowcount > 0 else None
                motivo_perda_id = self.motivos_perda_data.get(motivo_perda_texto)

                query_apontamento = "INSERT INTO apontamento (servico_id, data, horainicio, horafim, giros_rodados, quantidadeproduzida, perdas_producao, impressor_id, turno_id, motivo_perda_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                dados_apontamento = (self.selected_servico_id, self.prod_start_time.date(), self.prod_start_time.time(), self.prod_end_time.time(), giros_rodados, quantidade_produzida, perdas_producao, impressor_id, turno_id, motivo_perda_id)
                cur.execute(query_apontamento, dados_apontamento)

                cur.execute("SELECT op.id, opm.equipamento_id, opm.tiragem_em_folhas FROM ordem_servicos os JOIN ordem_producao op ON os.ordem_id = op.id JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id WHERE os.id = %s", (self.selected_servico_id,))
                result = cur.fetchone()
                if not result: raise Exception("Falha ao encontrar os detalhes do serviço para a lógica de produção parcial.")
                ordem_id, equipamento_id, tiragem_planejada = result

                if quantidade_produzida < tiragem_planejada:
                    msg = f"A quantidade produzida ({quantidade_produzida}) é menor que a planejada ({tiragem_planejada}).\n\nDeseja gerar um novo serviço com a quantidade restante?"
                    if messagebox.askyesno("Produção Parcial Detectada", msg, parent=self):
                        quantidade_restante = tiragem_planejada - quantidade_produzida
                        data_hoje = datetime.now().strftime('%d/%m/%Y')
                        nova_descricao = f"RESTANTE de {quantidade_restante} peças em {data_hoje}"
                        cur.execute("SELECT tempo_por_folha_ms FROM equipamentos_tipos WHERE id = %s", (equipamento_id,))
                        tempo_por_folha_ms = cur.fetchone()[0] or 1
                        tempo_restante_ms = quantidade_restante * tempo_por_folha_ms
                        cur.execute("INSERT INTO ordem_producao_maquinas (ordem_id, equipamento_id, tiragem_em_folhas, tempo_producao_previsto_ms) VALUES (%s, %s, %s, %s) RETURNING id;", (ordem_id, equipamento_id, quantidade_restante, tempo_restante_ms))
                        nova_maquina_id = cur.fetchone()[0]
                        cur.execute("INSERT INTO ordem_servicos (ordem_id, maquina_id, descricao, status, sequencia) VALUES (%(ordem_id)s, %(maquina_id)s, %(descricao)s, 'Pendente', (SELECT COALESCE(MAX(sequencia), 0) + 1 FROM ordem_servicos WHERE ordem_id = %(ordem_id)s));", {'ordem_id': ordem_id, 'maquina_id': nova_maquina_id, 'descricao': nova_descricao})

                cur.execute("UPDATE ordem_servicos SET status = 'Concluído' WHERE id = %s", (self.selected_servico_id,))
            conn.commit()
            messagebox.showinfo("Sucesso", "Apontamento finalizado e registrado com sucesso!", parent=self)
            self.reset_state()
            self.destroy()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Finalizar Apontamento", f"Ocorreu um erro inesperado:\n{e}", parent=self)
        finally:
            if conn: release_db_connection(conn)
            self.set_cursor_default()

    def on_close(self):
        self.destroy()

    def update_ui_state(self):
        state = self.current_state
        is_idle = state == 'IDLE'
        is_setup_running = state == 'SETUP_RUNNING'
        is_prod_ready = state == 'PRODUCTION_READY'
        is_prod_running = state == 'PRODUCTION_RUNNING'
        is_finished = state == 'FINISHED'
        has_selection = self.selected_servico_id is not None
        
        self.equipment_combobox.config(state='readonly' if is_idle else 'disabled')
        self.service_combobox.config(state='readonly' if is_idle and self.pending_services_data else 'disabled')
        self.impressor_combobox.config(state='readonly' if is_idle else 'disabled')
        self.turno_combobox.config(state='readonly' if is_idle else 'disabled')
        
        for widget in self.setup_fields.values():
            widget.config(state='normal' if is_setup_running else 'disabled')
        for key, widget in self.production_fields.items():
            is_readonly = isinstance(widget, tb.Combobox) and 'readonly' or 'normal'
            if key != 'giros_rodados':
                widget.config(state=is_readonly if is_prod_running or is_finished else 'disabled')
        
        self.setup_button.config(state='normal' if (is_idle and has_selection) or is_setup_running else 'disabled')
        self.setup_button.config(text=self.get_string('finish_setup_btn' if is_setup_running else 'start_setup_btn'))
        self.setup_stop_button.config(state='normal' if is_setup_running else 'disabled')
        
        self.prod_button.config(state='normal' if is_prod_ready or is_prod_running else 'disabled')
        self.prod_button.config(text=self.get_string('finish_production_btn' if is_prod_running else 'start_production_btn'))
        self.prod_stop_button.config(state='normal' if is_prod_running else 'disabled')
        self.final_register_button.config(state='normal' if is_finished else 'disabled')
        
        status_map = {
            'IDLE': ('status_idle', 'secondary'), 'SETUP_RUNNING': ('status_setup_running', 'info'),
            'PRODUCTION_READY': ('status_setup_done', 'primary'), 'PRODUCTION_RUNNING': ('status_prod_running', 'success'),
            'FINISHED': ('status_prod_done', 'warning')
        }
        status_key, bootstyle = status_map.get(state, ('status_idle', 'secondary'))
        self.status_label.config(text=self.get_string(status_key), bootstyle=bootstyle)

    def check_and_restore_state_from_db(self):
        self.set_cursor_watch()
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                query_setup = "SELECT s.id, s.servico_id, s.hora_inicio FROM apontamento_setup s JOIN ordem_servicos os ON s.servico_id = os.id WHERE s.hora_fim IS NULL ORDER BY s.hora_inicio DESC LIMIT 1;"
                cur.execute(query_setup)
                setup_aberto = cur.fetchone()
                if setup_aberto:
                    setup_id, servico_id, hora_inicio = setup_aberto
                    msg = self.get_string('restore_session_prompt', servico_id=servico_id)
                    if messagebox.askyesno(self.get_string('restore_session_title'), msg):
                        self.selected_servico_id = servico_id
                        self.setup_id = setup_id
                        self.setup_start_time = hora_inicio
                        self.current_state = 'SETUP_RUNNING'
                        self.load_data_for_restored_service()
                        self.update_setup_timer()
                        self.update_ui_state()
                        return
        except psycopg2.Error as e:
            messagebox.showerror(self.get_string('error_title'), self.get_string('db_restore_failed', error=e), parent=self)
        finally:
            if conn: release_db_connection(conn)
            self.set_cursor_default()
            if self.current_state == 'IDLE': self.update_ui_state()

    def load_data_for_restored_service(self):
        """
        Carrega e seleciona os dados de equipamento e serviço para uma sessão restaurada.
        """
        if not self.selected_servico_id:
            return

        self.set_cursor_watch()
        conn = None
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                query = """
                    SELECT opm.equipamento_id, os.descricao, op.numero_wo
                    FROM ordem_servicos os
                    JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                    JOIN ordem_producao op ON os.ordem_id = op.id
                    WHERE os.id = %s;
                """
                cur.execute(query, (self.selected_servico_id,))
                result = cur.fetchone()
                if not result:
                    return

                equipamento_id, servico_desc, wo_num = result

                equip_name = next((name for name, eid in self.equipments_data.items() if eid == equipamento_id), None)
                
                if equip_name:
                    self.equipment_combobox.set(equip_name)
                    self.on_equipment_select()
                    service_full_text = f"{wo_num}: {servico_desc}"
                    if service_full_text in self.pending_services_data:
                        self.service_combobox.set(service_full_text)
                    self.update_wo_info_panel()

        except Exception as e:
            messagebox.showerror(self.get_string('error_title'), f"Erro ao restaurar dados do serviço: {e}", parent=self)
        finally:
            if conn:
                release_db_connection(conn)
            self.set_cursor_default()
        
    def reset_state(self):
        self.current_state = 'IDLE'
        self.setup_start_time, self.setup_end_time = None, None
        self.prod_start_time, self.prod_end_time = None, None
        if self.setup_timer_job: self.after_cancel(self.setup_timer_job)
        if self.prod_timer_job: self.after_cancel(self.prod_timer_job)
        self.all_stops_data = []
        self.selected_ordem_id, self.selected_servico_id, self.setup_id = None, None, None
        
        for widget in self.initial_fields.values(): widget.set('')
        for widget in self.setup_fields.values(): widget.delete(0, END)
        for widget in self.production_fields.values():
            if isinstance(widget, tb.Entry): widget.delete(0, END)
            elif isinstance(widget, tb.Combobox): widget.set('')
        
        self.refresh_stops_tree()
        self.on_equipment_select()
        
    def toggle_setup(self):
        if self.current_state == 'IDLE':
            self._clear_field_highlights()
            required_widgets = [self.equipment_combobox, self.service_combobox, self.impressor_combobox, self.turno_combobox]
            invalid_widgets = [w for w in required_widgets if not w.get().strip() or "Nenhum serviço" in w.get()]
            if invalid_widgets:
                for w in invalid_widgets:
                    w.configure(bootstyle='danger')
                messagebox.showwarning("Seleção Incompleta", "Selecione Equipamento, Etapa, Impressor e Turno para iniciar.")
                return
            
            selected_service_text = self.service_combobox.get()
            self.selected_servico_id = self.pending_services_data.get(selected_service_text)
            if not self.selected_servico_id:
                messagebox.showerror("Erro", "ID do serviço não encontrado. Seleção inválida.")
                return

            self.current_state = 'SETUP_RUNNING'
            self.setup_start_time = datetime.now()
            self.update_setup_timer()
            
        elif self.current_state == 'SETUP_RUNNING':
            self.setup_end_time = datetime.now()
            if self.setup_timer_job: self.after_cancel(self.setup_timer_job)
            self.update_setup_timer()
            
            if not self.validate_and_save_setup():
                self.setup_end_time = None 
                self.update_setup_timer() 
                return
            self.current_state = 'PRODUCTION_READY'
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
            self.update_prod_timer()
        self.update_ui_state()
    
    def update_setup_timer(self):
        if self.setup_start_time:
            end = self.setup_end_time or datetime.now()
            elapsed = end - self.setup_start_time
            self.setup_timer_label.config(text=str(elapsed).split('.')[0])
            if self.current_state == 'SETUP_RUNNING':
                self.setup_timer_job = self.after(1000, self.update_setup_timer)
        else:
            self.setup_timer_label.config(text="00:00:00")
            
    def update_prod_timer(self):
        if self.prod_start_time:
            end = self.prod_end_time or datetime.now()
            elapsed = end - self.prod_start_time
            self.prod_timer_label.config(text=str(elapsed).split('.')[0])
            if self.current_state == 'PRODUCTION_RUNNING':
                self.prod_timer_job = self.after(1000, self.update_prod_timer)
        else:
            self.prod_timer_label.config(text="00:00:00")

    def refresh_stops_tree(self):
        for item in self.stops_tree.get_children(): self.stops_tree.delete(item)
        for stop in self.all_stops_data:
            start, end = stop.get('hora_inicio_parada'), stop.get('hora_fim_parada')
            start_str = start.strftime('%H:%M:%S') if start else ''
            end_str = end.strftime('%H:%M:%S') if end else ''
            
            duration_str = ''
            if start and end:
                duration = (datetime.combine(date.min, end) - datetime.combine(date.min, start))
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            
            motivo_display = stop.get('motivo_text', '')
            if motivo_display and motivo_display.lower() == 'outros' and stop.get('motivo_extra_detail'):
                motivo_display = f"Outros: {stop['motivo_extra_detail']}"
                
            self.stops_tree.insert('', END, values=(stop.get('type', ''), motivo_display, start_str, end_str, duration_str))

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

    def _calcular_giros_rodados(self, event=None):
        try:
            qtde_produzida_str = self.production_fields['quantidadeproduzida'].get()
            if not qtde_produzida_str or not hasattr(self, 'cores_desc') or not self.cores_desc or self.cores_desc == '-': return

            qtde_produzida = int(qtde_produzida_str)
            multiplicador = self.giros_map.get(self.cores_desc, 1)
            giros_calculado = qtde_produzida * multiplicador

            giros_widget = self.production_fields['giros_rodados']
            giros_widget.config(state=NORMAL)
            giros_widget.delete(0, END)
            giros_widget.insert(0, str(giros_calculado))
            giros_widget.config(state=DISABLED)
        except (ValueError, Exception): pass

    def on_service_select(self, event=None):
        self._clear_field_highlights()
        selected_service_text = self.service_combobox.get()
        self.selected_servico_id = self.pending_services_data.get(selected_service_text)
        if self.selected_servico_id:
            self.update_wo_info_panel()
        self.update_ui_state()

    def view_stop_details(self):
        wo_number_label = self.info_labels.get('col_wo')
        wo_number = wo_number_label.cget("text") if wo_number_label else "N/A"
        if not self.all_stops_data:
            messagebox.showinfo("Sem Paradas", "Não há detalhes de paradas para exibir.", parent=self)
            return
        StopDetailsWindow(self, self.all_stops_data, wo_number)

    def format_seconds_to_hhmmss(self, seconds):
        if not isinstance(seconds, (int, float)) or seconds < 0: return "00:00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

class RealTimeStopWindow(Toplevel):
    def __init__(self, master, db_config, stop_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.stop_callback = stop_callback

        self.title(self.master.get_string('stop_tracking_window_title'))
        self.geometry("500x300")
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
        main_frame = tb.Frame(self, padding=FRAME_PADDING)
        main_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(main_frame, text=self.get_string('stop_reason_label') + ": *", font="-weight bold").pack(pady=(0, PAD_Y))
        self.motivo_combobox = tb.Combobox(main_frame, state="readonly")
        self.motivo_combobox.pack(fill=X, pady=(0, PAD_Y_LARGE))
        self.motivo_combobox.bind("<<ComboboxSelected>>", self.on_reason_selected)

        self.other_reason_label = tb.Label(main_frame, text=self.get_string('other_motives_label') + ": *", font="-weight bold")
        self.other_reason_entry = tb.Entry(main_frame)
        
        timer_button_frame = tb.Frame(main_frame)
        timer_button_frame.pack(fill=X, pady=(PAD_Y_LARGE, 0))
        
        tb.Label(timer_button_frame, text=self.get_string('stop_time_label')).pack()
        self.timer_label = tb.Label(timer_button_frame, text="00:00:00", font=TIMER_FONT, bootstyle="danger")
        self.timer_label.pack()

        self.finish_button = tb.Button(timer_button_frame, text=self.get_string('finish_stop_btn'), bootstyle="danger", state=DISABLED, command=self.finish_stop)
        self.finish_button.pack(pady=(PAD_Y_LARGE, 0), ipadx=10, ipady=5)

    def load_motivos_parada(self):
        self.master.set_cursor_watch()
        try:
            conn = get_db_connection()
            if not conn: return
            with conn.cursor() as cur:
                schema = LOOKUP_TABLE_SCHEMAS["motivos_parada_tipos"]
                query = f'SELECT "{schema["columns"]["descricao"]["db_column"]}", "{schema["pk_column"]}" FROM {schema["table"]} ORDER BY "{schema["columns"]["descricao"]["db_column"]}"'
                cur.execute(query)
                self.motivos_parada_options = cur.fetchall()
                self.motivo_combobox['values'] = [opt[0] for opt in self.motivos_parada_options]
        except psycopg2.Error as e:
            messagebox.showwarning("Erro", f"Falha ao carregar motivos de parada: {e}", parent=self)
        finally:
            if 'conn' in locals() and conn: release_db_connection(conn)
            self.master.set_cursor_default()

    def on_reason_selected(self, event=None):
        selected_reason = self.motivo_combobox.get()
        if selected_reason and selected_reason.lower() == 'outros':
            self.other_reason_label.pack(fill=X, pady=(PAD_Y_LARGE, 0))
            self.other_reason_entry.pack(fill=X)
            self.other_reason_entry.focus_set()
        else:
            self.other_reason_entry.delete(0, END)
            self.other_reason_label.pack_forget()
            self.other_reason_entry.pack_forget()
        self.finish_button.config(state=NORMAL if selected_reason else DISABLED)

    def update_timer(self):
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
        self.timer_job = self.after(1000, self.update_timer)

    def finish_stop(self):
        if self.timer_job: self.after_cancel(self.timer_job)
        
        selected_motivo_text = self.motivo_combobox.get()
        extra_detail = None
        if selected_motivo_text and selected_motivo_text.lower() == 'outros':
            extra_detail = self.other_reason_entry.get().strip()
            if not extra_detail:
                self.other_reason_entry.configure(bootstyle='danger')
                messagebox.showwarning("Campo Obrigatório", "Por favor, especifique o motivo da parada.", parent=self)
                self.update_timer()
                return
        elif not selected_motivo_text:
             self.motivo_combobox.configure(bootstyle='danger')
             messagebox.showwarning("Campo Obrigatório", "Por favor, selecione um motivo para a parada.", parent=self)
             self.update_timer()
             return

        end_time = datetime.now()
        motivo_id = next((opt[1] for opt in self.motivos_parada_options if opt[0] == selected_motivo_text), None)
        
        stop_data = {
            "motivo_text": selected_motivo_text, "motivo_id": motivo_id,
            "hora_inicio_parada": self.start_time.time(), "hora_fim_parada": end_time.time(),
            "motivo_extra_detail": extra_detail
        }
        
        self.stop_callback(stop_data)
        self.destroy()