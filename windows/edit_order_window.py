# -*- coding: utf-8 -*-

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

class EditOrdemWindow(Toplevel):
    def __init__(self, master, db_config, ordem_id, refresh_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.ordem_id = ordem_id
        self.refresh_callback = refresh_callback
        self.current_language = self.master.current_language
        
        # Dicionários de configuração copiados da janela pai para consistência
        self.fields_config = self.master.fields_config
        self.machine_fields_left = self.master.material_fields
        self.machine_fields_right = self.master.machine_fields_static
        self.giros_map = self.master.giros_map
        self.equipment_speed_map = self.master.equipment_speed_map
        
        self.widgets = {}
        self.machine_widgets = {}
        
        self.title("Editar Ordem de Produção")
        self.geometry("1200x800")
        self.grab_set()

        self.create_widgets()
        self.load_all_combobox_data()
        self.load_ordem_data()
        
        self.transient(master)

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        # A estrutura visual é a mesma da janela do PCP
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        form_frame = tb.LabelFrame(main_frame, text="Dados da Ordem de Produção", bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor=N)
        form_frame.grid_columnconfigure(1, weight=1)

        fields = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega"]
        for i, key in enumerate(fields):
            config = self.fields_config[key]
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky=W)
            widget = self.create_widget_from_config(form_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget

        machines_frame = tb.LabelFrame(main_frame, text="Detalhes de Produção por Máquina", bootstyle=INFO, padding=10)
        machines_frame.pack(fill=X, pady=10)
        machines_frame.grid_columnconfigure(1, weight=1)
        machines_frame.grid_columnconfigure(3, weight=1)

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

        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(pady=10)
        # MOD: Padronização do texto do botão para "Salvar Alterações"
        tb.Button(btn_frame, text="Salvar Alterações", command=self.save_changes, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Cancelar", command=self.destroy, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

    def create_widget_from_config(self, parent, config):
        if config.get("widget") == "Combobox": return tb.Combobox(parent, state="readonly")
        elif config.get("widget") == "DateEntry": return DateEntry(parent, dateformat='%d/%m/%Y')
        else: return tb.Entry(parent)

    def load_all_combobox_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
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
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados dos comboboxes: {e}", parent=self)
        finally:
            if conn: conn.close()

    def format_seconds_to_hhmmss(self, seconds):
        if not isinstance(seconds, (int, float)) or seconds < 0: return "00:00:00"
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def load_ordem_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # Query to get order details including material descriptions
                cur.execute("""
                    SELECT 
                        op.numero_wo, op.pn_partnumber, op.cliente, op.data_previsao_entrega,
                        qc.descricao as cores, 
                        tp.descricao as papel, 
                        g.valor as gramatura
                    FROM ordem_producao op
                    LEFT JOIN qtde_cores_tipos qc ON op.qtde_cores_id = qc.id
                    LEFT JOIN tipos_papel tp ON op.tipo_papel_id = tp.id
                    LEFT JOIN gramaturas_tipos g ON op.gramatura_id = g.id
                    WHERE op.id = %s
                """, (self.ordem_id,))
                
                order_data = cur.fetchone()
                if not order_data:
                    messagebox.showerror("Erro", "Ordem de produção não encontrada.", parent=self)
                    self.destroy()
                    return

                (wo_num, pn, cliente, previsao, cores_desc, papel_desc, gramatura_valor) = order_data
                
                self.title(f"Editar Ordem de Produção - WO: {wo_num}")
                self.widgets['numero_wo'].insert(0, wo_num or '')
                self.widgets['pn_partnumber'].insert(0, pn or '')
                self.widgets['cliente'].insert(0, cliente or '')
                if previsao:
                    self.widgets['data_previsao_entrega'].entry.insert(0, previsao.strftime('%d/%m/%Y'))

                # Now, load the machine list for the order
                cur.execute("""
                    SELECT 
                        et.descricao, 
                        opm.tiragem_em_folhas, 
                        opm.giros_previstos, 
                        opm.tempo_producao_previsto_ms
                    FROM ordem_producao_maquinas opm
                    LEFT JOIN equipamentos_tipos et ON opm.equipamento_id = et.id
                    WHERE opm.ordem_id = %s 
                    ORDER BY opm.sequencia_producao;
                """, (self.ordem_id,))
                
                for equip, tiragem, giros, tempo_ms in cur.fetchall():
                    tempo_s = (tempo_ms / 1000.0) if tempo_ms else 0.0
                    tempo_formatado = self.format_seconds_to_hhmmss(tempo_s)
                    
                    # Use the material data from the main order for all machines
                    values = (
                        equip or '', 
                        tiragem or '', 
                        giros or '', 
                        cores_desc or '', 
                        papel_desc or '', 
                        gramatura_valor or '', 
                        tempo_formatado
                    )
                    self.machines_tree.insert("", "end", values=values)

        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar dados da ordem: {e}", parent=self)
        finally:
            if conn: conn.close()

    def save_changes(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # 1. Get material IDs from widgets
                # These widgets are now in self.machine_widgets, based on the fix from the previous step
                
                # Helper to get ID from description/value
                def get_id_from_value(table, column, value):
                    if not value:
                        return None
                    cur.execute(f"SELECT id FROM {table} WHERE {column} = %s", (value,))
                    result = cur.fetchone()
                    return result[0] if result else None

                tipo_papel_id = get_id_from_value("tipos_papel", "descricao", self.machine_widgets["tipo_papel_id"].get())
                gramatura_id = get_id_from_value("gramaturas_tipos", "valor", self.machine_widgets["gramatura_id"].get())
                formato_id = get_id_from_value("formatos_tipos", "descricao", self.machine_widgets.get("formato_id").get() if self.machine_widgets.get("formato_id") else None) # formato is not in the old edit window, need to check
                fsc_id = get_id_from_value("fsc_tipos", "descricao", self.machine_widgets.get("fsc_id").get() if self.machine_widgets.get("fsc_id") else None) # fsc is not in the old edit window
                qtde_cores_id = get_id_from_value("qtde_cores_tipos", "descricao", self.machine_widgets["qtde_cores_id"].get())

                # 2. Update ordem_producao with general and material data
                data_previsao_str = self.widgets['data_previsao_entrega'].entry.get()
                data_previsao = datetime.strptime(data_previsao_str, '%d/%m/%Y').date() if data_previsao_str else None
                
                cur.execute("""
                    UPDATE ordem_producao 
                    SET numero_wo = %s, pn_partnumber = %s, cliente = %s, data_previsao_entrega = %s,
                        tipo_papel_id = %s, gramatura_id = %s, formato_id = %s, fsc_id = %s, qtde_cores_id = %s
                    WHERE id = %s
                """, (
                    self.widgets['numero_wo'].get(),
                    self.widgets['pn_partnumber'].get(),
                    self.widgets['cliente'].get(),
                    data_previsao,
                    tipo_papel_id,
                    gramatura_id,
                    formato_id,
                    fsc_id,
                    qtde_cores_id,
                    self.ordem_id
                ))
                
                # 3. Apagar serviços e máquinas antigas para recriá-los
                cur.execute("DELETE FROM ordem_servicos WHERE ordem_id = %s", (self.ordem_id,))
                cur.execute("DELETE FROM ordem_producao_maquinas WHERE ordem_id = %s", (self.ordem_id,))
                
                # 4. Inserir as novas máquinas e serviços da lista
                sequencia_servico = 1
                for item in self.machines_tree.get_children():
                    (equip_nome, tiragem_str, giros_str, _, _, _, _) = self.machines_tree.item(item, 'values')
                    
                    equipamento_id = get_id_from_value("equipamentos_tipos", "descricao", equip_nome)
                    if not equipamento_id:
                        raise ValueError(f"Equipamento '{equip_nome}' não encontrado.")

                    tiragem_int = int(tiragem_str)
                    giros_int = int(giros_str)
                    tempo_previsto_ms = tiragem_int * self.equipment_speed_map.get(equip_nome, 1)

                    # Inserir máquina (without material fields)
                    cur.execute(
                        """
                        INSERT INTO ordem_producao_maquinas (ordem_id, equipamento_id, tiragem_em_folhas, giros_previstos, tempo_producao_previsto_ms, sequencia_producao)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                        """,
                        (self.ordem_id, equipamento_id, tiragem_int, giros_int, tempo_previsto_ms, sequencia_servico)
                    )
                    maquina_id = cur.fetchone()[0]

                    # Inserir serviço
                    cur.execute(
                        "INSERT INTO ordem_servicos (ordem_id, maquina_id, descricao, status, sequencia) VALUES (%s, %s, %s, 'Pendente', %s);",
                        (self.ordem_id, maquina_id, equip_nome, sequencia_servico)
                    )
                    sequencia_servico += 1

            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('update_order_success'), parent=self)
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Salvar", f"Falha ao salvar alterações: {e}", parent=self)
        finally:
            if conn: conn.close()

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
        except (ValueError, TypeError):
            messagebox.showerror("Erro de Formato", "O valor da Tiragem deve ser um número.", parent=self)

    def remove_selected_machine(self):
        for item in self.machines_tree.selection():
            self.machines_tree.delete(item)
        
    def _calcular_giros_para_maquina(self, event=None):
        try:
            equipamento = self.machine_widgets["equipamento_id"].get()
            tiragem_str = self.machine_widgets["tiragem_em_folhas"].get()
            cores_desc = self.machine_widgets["qtde_cores_id"].get()
            giros_widget = self.machine_widgets["giros_previstos"]
            
            giros_widget.delete(0, END)
            if "impressora" in equipamento.lower() and tiragem_str and cores_desc:
                giros_calculado = int(tiragem_str) * self.giros_map.get(cores_desc, 1)
                giros_widget.insert(0, str(giros_calculado))
            else:
                giros_widget.insert(0, "0")
        except (ValueError, IndexError):
            giros_widget = self.machine_widgets.get("giros_previstos")
            if giros_widget:
                giros_widget.delete(0, END)
                giros_widget.insert(0, "0")