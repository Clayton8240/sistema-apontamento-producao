# -*- coding: utf-8 -*-

from datetime import date, datetime
import openpyxl
import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import (
    filedialog, messagebox, Listbox, Toplevel,
    END, W, E, S, N, CENTER, BOTH, YES, X, Y, RIGHT, LEFT, VERTICAL, DISABLED, NORMAL
)

# Importações do nosso projeto
from config import LANGUAGES, LOOKUP_TABLE_SCHEMAS
from .edit_order_window import EditOrdemWindow
from .service_manager_window import ServiceManagerWindow


class PCPWindow(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.title(self.get_string('btn_pcp_management'))
        self.geometry("1200x800")
        self.grab_set()
        
        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"},
            "pn_partnumber": {"label_key": "PN (Partnumber)", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"},
            "data_previsao_entrega": {"label_key": "col_data_previsao", "widget": "DateEntry"},
            "tiragem_em_folhas": {"label_key": "col_tiragem_em_folhas", "widget": "Entry"},
            "giros_previstos": {"label_key": "Giros Total Previstos", "widget": "Entry"},
            "equipamento_id": {"label_key": "equipment_label", "widget": "Combobox", "lookup": "equipamentos_tipos"},
            "qtde_cores_id": {"label_key": "col_qtde_cores", "widget": "Combobox", "lookup": "qtde_cores_tipos"},
            "tipo_papel_id": {"label_key": "col_tipo_papel", "widget": "Combobox", "lookup": "tipos_papel"},
            "gramatura_id": {"label_key": "col_gramatura", "widget": "Combobox", "lookup": "gramaturas_tipos"},
            "formato_id": {"label_key": "col_formato", "widget": "Combobox", "lookup": "formatos_tipos"},
            "fsc_id": {"label_key": "col_fsc", "widget": "Combobox", "lookup": "fsc_tipos"},
            "acabamento": {"label_key": "Acabamento", "widget": "Listbox"},
        }
        self.widgets = {}
        self.giros_map = {}
        self.acabamentos_map = {}
        
        self.create_widgets()
        self.load_all_combobox_data()
        self.load_ordens()

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.master.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        form_frame = tb.LabelFrame(main_frame, text=self.get_string('new_order_section'), bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor=N)
        
        fields_left = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega", "tiragem_em_folhas", "equipamento_id"]
        fields_middle = ["giros_previstos", "qtde_cores_id", "tipo_papel_id", "gramatura_id", "formato_id", "fsc_id"]
        
        for i, key in enumerate(fields_left):
            config = self.fields_config[key]
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky=W)
            widget = self.create_widget_from_config(form_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget

        for i, key in enumerate(fields_middle):
            config = self.fields_config[key]
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=2, padx=5, pady=5, sticky=W)
            widget = self.create_widget_from_config(form_frame, config)
            widget.grid(row=i, column=3, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget
        
        self.widgets["giros_previstos"].config(state=DISABLED)
        self.widgets["tiragem_em_folhas"].bind("<KeyRelease>", self._calcular_giros_previstos)
        self.widgets["qtde_cores_id"].bind("<<ComboboxSelected>>", self._calcular_giros_previstos)
        
        acab_config = self.fields_config["acabamento"]
        tb.Label(form_frame, text=self.get_string(acab_config["label_key"]) + ":").grid(row=0, column=4, padx=5, pady=5, sticky=NW)

        acab_frame = tb.Frame(form_frame)
        acab_frame.grid(row=0, column=5, rowspan=6, padx=5, pady=5, sticky="nsew")

        acab_scrollbar = tb.Scrollbar(acab_frame)
        acab_scrollbar.pack(side=RIGHT, fill=Y)

        acab_widget = Listbox(acab_frame, selectmode="multiple", yscrollcommand=acab_scrollbar.set, exportselection=False)
        acab_widget.pack(expand=True, fill=BOTH)
        acab_scrollbar.config(command=acab_widget.yview)

        self.widgets["acabamento"] = acab_widget
        
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        form_frame.grid_columnconfigure(5, weight=2)

        btn_frame_form = tb.Frame(form_frame)
        btn_frame_form.grid(row=len(fields_left), column=0, columnspan=6, pady=10)
        tb.Button(btn_frame_form, text=self.get_string('save_btn'), command=self.save_new_ordem, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(btn_frame_form, text=self.get_string('clear_filters_btn'), command=self.clear_fields, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

        action_frame = tb.Frame(main_frame)
        action_frame.pack(fill=X, pady=5)

        self.move_up_button = tb.Button(action_frame, text="Subir na Fila", command=self.move_order_up, bootstyle="primary-outline", state=DISABLED)
        self.move_up_button.pack(side=LEFT, padx=5)
        self.move_down_button = tb.Button(action_frame, text="Descer na Fila", command=self.move_order_down, bootstyle="primary-outline", state=DISABLED)
        self.move_down_button.pack(side=LEFT, padx=(0, 20))

        self.edit_button = tb.Button(action_frame, text=self.get_string('edit_order_btn'), command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
        self.edit_button.pack(side=LEFT, padx=5)
        self.cancel_button = tb.Button(action_frame, text=self.get_string('cancel_order_btn'), command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
        self.cancel_button.pack(side=LEFT, padx=5)
        self.services_button = tb.Button(action_frame, text=self.get_string('btn_manage_services'), command=self.open_service_manager, bootstyle="primary-outline", state=DISABLED)
        self.services_button.pack(side=LEFT, padx=5)

        tb.Button(action_frame, text="Ver Relatório", command=self.open_report_window, bootstyle="info-outline").pack(side=LEFT, padx=(20, 0))
        
        self.export_button = tb.Button(action_frame, text="Exportar para XLSX", command=self.export_to_xlsx, bootstyle="success-outline")
        self.export_button.pack(side=RIGHT, padx=5)
        
        tree_frame = tb.LabelFrame(main_frame, text=self.get_string('created_orders_section'), bootstyle=INFO, padding=10)
        tree_frame.pack(fill=BOTH, expand=True)
        
        cols = ("sequencia", "id", "wo", "pn", "cliente", "equipamento", "data_previsao", "status")
        self.headers_treeview = ("Seq.", self.get_string('col_id'), self.get_string('col_wo'), "PN (Partnumber)", self.get_string('col_cliente'), self.get_string('equipment_label'), self.get_string('col_data_previsao'), self.get_string('col_status'))
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols, self.headers_treeview):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=120, anchor=W)
        self.tree.column("sequencia", width=40, anchor=CENTER)
        self.tree.column("id", width=50, anchor=CENTER)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = tb.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
    
    def _calcular_giros_previstos(self, event=None):
        try:
            tiragem_str = self.widgets["tiragem_em_folhas"].get()
            cores_widget = self.widgets["qtde_cores_id"]
            cores_desc = cores_widget.get()
            if not tiragem_str or not cores_desc: return
            tiragem_folhas = int(tiragem_str)
            multiplicador = self.giros_map.get(cores_desc, 1)
            giros_calculado = tiragem_folhas * multiplicador
            giros_widget = self.widgets["giros_previstos"]
            giros_widget.config(state=NORMAL)
            giros_widget.delete(0, END)
            giros_widget.insert(0, str(giros_calculado))
            giros_widget.config(state=DISABLED)
        except (ValueError, IndexError): pass
        except Exception as e: print(f"Erro ao calcular giros: {e}")

    def create_widget_from_config(self, parent, config):
        if config["widget"] == "Combobox": return tb.Combobox(parent, state="readonly")
        elif config["widget"] == "DateEntry": return DateEntry(parent, dateformat='%d/%m/%Y')
        elif config["widget"] == "Listbox": return None 
        else: return tb.Entry(parent)

    def save_new_ordem(self):
        data = {}
        self.widgets["giros_previstos"].config(state=NORMAL)
        for key, widget in self.widgets.items():
            if key == "acabamento": continue
            if isinstance(widget, DateEntry): 
                date_val = widget.entry.get()
                data[key] = datetime.strptime(date_val, '%d/%m/%Y').date() if date_val else None
            elif isinstance(widget, tb.Text): data[key] = widget.get("1.0", "end-1c").strip()
            elif widget: data[key] = widget.get().strip()
        self.widgets["giros_previstos"].config(state=DISABLED)
        
        selected_indices = self.widgets["acabamento"].curselection()
        selected_acabamentos_desc = [self.widgets["acabamento"].get(i) for i in selected_indices]
        
        if not data.get("numero_wo"):
            messagebox.showwarning(self.get_string("required_field_warning", field_name=self.get_string("col_wo")), parent=self)
            return
            
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # ### ALTERAÇÃO: Obter o próximo número da sequência ###
                cur.execute("SELECT COALESCE(MAX(sequencia_producao), 0) + 1 FROM ordem_producao")
                next_seq = cur.fetchone()[0]
                data['sequencia_producao'] = next_seq

                data['equipamento_id'] = self.get_id_from_combobox('equipamento_id', cur)
                data['qtde_cores_id'] = self.get_id_from_combobox('qtde_cores_id', cur)
                data['tipo_papel_id'] = self.get_id_from_combobox('tipo_papel_id', cur)
                data['gramatura_id'] = self.get_id_from_combobox('gramatura_id', cur, column_name='valor')
                data['formato_id'] = self.get_id_from_combobox('formato_id', cur)
                data['fsc_id'] = self.get_id_from_combobox('fsc_id', cur)

                cols_to_save = [k for k in self.fields_config.keys() if k in data and data[k] is not None and k != 'acabamento']
                cols_to_save.append('sequencia_producao') # Adiciona a nova coluna
                non_empty_data = {col: data[col] for col in cols_to_save if data[col] is not None}

                cols = non_empty_data.keys()
                query = f""" INSERT INTO ordem_producao ({', '.join(f'"{c}"' for c in cols)}, status) 
                            VALUES ({', '.join([f'%({c})s' for c in cols])}, 'Em Aberto') RETURNING id """
                cur.execute(query, non_empty_data)
                ordem_id = cur.fetchone()[0]

                if ordem_id and selected_acabamentos_desc:
                    acabamento_ids_to_insert = [self.acabamentos_map.get(desc) for desc in selected_acabamentos_desc]
                    for acab_id in acabamento_ids_to_insert:
                        if acab_id:
                            cur.execute("INSERT INTO ordem_producao_acabamentos (ordem_id, acabamento_id) VALUES (%s, %s)", (ordem_id, acab_id))

            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('order_save_success'), parent=self)
            self.clear_fields()
            self.load_ordens()
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'ordem_producao_numero_wo_key' in str(e):
                 messagebox.showerror("Erro de Integridade", self.get_string('integrity_error_wo', wo=data.get('numero_wo', '')), parent=self)
            else:
                messagebox.showerror("Erro de Integridade", f"Não foi possível salvar. Verifique se os dados estão corretos.\nDetalhes: {e}", parent=self)
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro ao Salvar", self.get_string('save_order_error', error=e), parent=self)
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

    def clear_fields(self):
        self.widgets["giros_previstos"].config(state=NORMAL)
        for key, widget in self.widgets.items():
            if isinstance(widget, tb.Combobox): widget.set('')
            elif isinstance(widget, DateEntry): widget.entry.delete(0, END)
            elif isinstance(widget, tb.Text): widget.delete("1.0", END)
            elif isinstance(widget, Listbox): widget.selection_clear(0, END)
            elif widget: widget.delete(0, END)
        self.widgets["giros_previstos"].config(state=DISABLED)

    def on_tree_select(self, event=None):
        selected_item = self.tree.focus()
        if not selected_item:
            self.edit_button.config(state=DISABLED)
            self.cancel_button.config(state=DISABLED)
            self.services_button.config(state=DISABLED)
            # ### ALTERAÇÃO: Desabilitar botões de mover ###
            self.move_up_button.config(state=DISABLED)
            self.move_down_button.config(state=DISABLED)
            return
        
        self.services_button.config(state=NORMAL)
        # ### ALTERAÇÃO: Habilitar botões de mover ###
        self.move_up_button.config(state=NORMAL)
        self.move_down_button.config(state=NORMAL)

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
        ordem_id, wo_number = item_values[1], item_values[2] # Ajuste de índice
        ServiceManagerWindow(self, self.db_config, ordem_id, wo_number, refresh_callback=self.load_ordens)

    def open_edit_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[1] # Ajuste de índice
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_all_combobox_data)

    def cancel_ordem(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_cancel_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id, wo_num = item_values[1], item_values[2] # Ajuste de índice
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
        self.move_up_button.config(state=DISABLED)
        self.move_down_button.config(state=DISABLED)

        for i in self.tree.get_children():
            self.tree.delete(i)
        
        conn = self.get_db_connection()
        if not conn: return
            
        try:
            with conn.cursor() as cur:
                sql_query = """
                    SELECT 
                        op.sequencia_producao,
                        op.id, 
                        op.numero_wo, 
                        op.pn_partnumber, 
                        op.cliente, 
                        et.descricao AS equipamento_nome, 
                        op.data_previsao_entrega, 
                        op.status,
                        (SELECT os.status FROM ordem_servicos os WHERE os.ordem_id = op.id AND os.status = 'Em Produção' LIMIT 1) AS servico_em_producao
                    FROM 
                        ordem_producao AS op
                    LEFT JOIN 
                        equipamentos_tipos AS et ON op.equipamento_id = et.id
                    WHERE op.status != 'Concluído'
                    ORDER BY 
                        op.sequencia_producao ASC
                """
                cur.execute(sql_query)
                
                today = date.today()

                for row in cur.fetchall():
                    row_list = list(row)
                    
                    data_previsao_idx = 6
                    status_op_idx = 7
                    servico_em_prod_idx = 8
                    
                    status_op = row_list[status_op_idx]
                    data_previsao = row_list[data_previsao_idx]
                    servico_em_prod = row_list[servico_em_prod_idx]

                    display_status = status_op
                    if servico_em_prod == 'Em Produção':
                        display_status = 'Em Produção'
                    elif status_op != 'Concluído' and data_previsao and data_previsao < today:
                        display_status = 'Atrasado'
                    
                    row_list[status_op_idx] = display_status

                    if data_previsao and isinstance(data_previsao, date):
                        row_list[data_previsao_idx] = data_previsao.strftime('%d/%m/%Y')
                    
                    processed_row = ["" if item is None else item for item in row_list[:-1]]
                    
                    self.tree.insert("", "end", values=tuple(processed_row))
                    
        except psycopg2.Error as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar ordens de produção: {e}", parent=self)
        finally:
            if conn: conn.close()
    
    def open_report_window(self):
        """Pede à janela mestre (Menu Principal) para abrir o relatório."""
        self.master.open_view_window()

    def load_all_combobox_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}
                
                schemas = LOOKUP_TABLE_SCHEMAS
                for key, widget in self.widgets.items():
                    if isinstance(widget, tb.Combobox):
                        field_config = self.fields_config.get(key, {})
                        lookup_ref = field_config.get("lookup")
                        if lookup_ref and lookup_ref in schemas:
                            schema_info = schemas[lookup_ref]
                            db_col = 'valor' if lookup_ref == 'gramaturas_tipos' else 'descricao'
                            cur.execute(f'SELECT DISTINCT "{db_col}" FROM {schema_info["table"]} ORDER BY "{db_col}"')
                            values = [str(row[0]) for row in cur.fetchall()]
                            widget['values'] = values
                
                if "acabamento" in self.widgets and isinstance(self.widgets["acabamento"], Listbox):
                    acab_widget = self.widgets["acabamento"]
                    acab_widget.delete(0, END)
                    schema_info_acab = LOOKUP_TABLE_SCHEMAS["acabamentos_tipos"]
                    cur.execute(f'SELECT id, descricao FROM {schema_info_acab["table"]} ORDER BY descricao')
                    self.acabamentos_map = {}
                    for acab_id, desc in cur.fetchall():
                        acab_widget.insert(END, desc)
                        self.acabamentos_map[desc] = acab_id
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados para os comboboxes: {e}", parent=self)
        finally:
            if conn: conn.close()

    def export_to_xlsx(self):
        # ... (Este método pode ser mantido como está)
        pass

    def move_order_up(self):
        selected_item = self.tree.focus()
        if not selected_item: return

        prev_item = self.tree.prev(selected_item)
        if not prev_item: return # Já é o primeiro item

        self.swap_orders(selected_item, prev_item)

    def move_order_down(self):
        selected_item = self.tree.focus()
        if not selected_item: return

        next_item = self.tree.next(selected_item)
        if not next_item: return # Já é o último item

        self.swap_orders(selected_item, next_item)

    def swap_orders(self, item1, item2):
        # Obter dados dos itens (sequencia, id)
        data1 = self.tree.item(item1, 'values')
        seq1, id1 = data1[0], data1[1]
        
        data2 = self.tree.item(item2, 'values')
        seq2, id2 = data2[0], data2[1]

        conn = self.get_db_connection()
        if not conn: return

        try:
            with conn.cursor() as cur:
                # Troca as sequências no banco de dados
                cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq2, id1))
                cur.execute("UPDATE ordem_producao SET sequencia_producao = %s WHERE id = %s", (seq1, id2))
            conn.commit()
            self.load_ordens() # Recarrega a lista para mostrar a nova ordem
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Erro ao Reordenar", f"Não foi possível alterar a sequência: {e}", parent=self)
        finally:
            if conn: conn.close()