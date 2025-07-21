# -*- coding: utf-8 -*-

from datetime import date, datetime
import openpyxl
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import (
    filedialog, messagebox, Listbox, Toplevel,
    END, W, E, S, N, CENTER, BOTH, YES, X, Y, RIGHT, LEFT, VERTICAL
)
import psycopg2

# Importações do nosso projeto
from config import LANGUAGES, LOOKUP_TABLE_SCHEMAS

class PCPWindow(Toplevel):
    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.title(self.get_string('btn_pcp_management'))
        self.geometry("1200x800")
        self.grab_set()
        
        self.fields_config = {
            "numero_wo": {"label_key": "col_wo", "widget": "Entry"}, "pn_partnumber": {"label_key": "PN (Partnumber)", "widget": "Entry"},
            "cliente": {"label_key": "col_cliente", "widget": "Entry"}, "data_previsao_entrega": {"label_key": "col_data_previsao", "widget": "DateEntry"},
            "tiragem_em_folhas": {"label_key": "col_tiragem_em_folhas", "widget": "Entry"}, "giros_previstos": {"label_key": "Giros Total Previstos", "widget": "Entry"},
            "equipamento": {"label_key": "equipment_label", "widget": "Combobox", "lookup": "equipamentos_tipos"}, "qtde_cores": {"label_key": "col_qtde_cores", "widget": "Combobox", "lookup": "qtde_cores_tipos"},
            "tipo_papel": {"label_key": "col_tipo_papel", "widget": "Combobox", "lookup": "tipos_papel"}, "gramatura": {"label_key": "col_gramatura", "widget": "Combobox", "lookup": "gramaturas_tipos"},
            "formato": {"label_key": "col_formato", "widget": "Combobox", "lookup": "formatos_tipos"}, "fsc": {"label_key": "col_fsc", "widget": "Combobox", "lookup": "fsc_tipos"},
            "acabamento": {"label_key": "Acabamento", "widget": "Listbox"},
        }
        self.widgets = {}
        self.giros_map = {}
        
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
        
        fields_left = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega", "tiragem_em_folhas", "equipamento"]
        fields_middle = ["giros_previstos", "qtde_cores", "tipo_papel", "gramatura", "formato", "fsc"]
        
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
        self.widgets["qtde_cores"].bind("<<ComboboxSelected>>", self._calcular_giros_previstos)
        
        acab_config = self.fields_config["acabamento"]
        tb.Label(form_frame, text=self.get_string(acab_config["label_key"]) + ":").grid(row=0, column=4, padx=5, pady=5, sticky=NW)

        # Frame para a Listbox e a Scrollbar
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
        self.edit_button = tb.Button(action_frame, text=self.get_string('edit_order_btn'), command=self.open_edit_window, bootstyle="info-outline", state=DISABLED)
        self.edit_button.pack(side=LEFT, padx=5)
        self.cancel_button = tb.Button(action_frame, text=self.get_string('cancel_order_btn'), command=self.cancel_ordem, bootstyle="danger-outline", state=DISABLED)
        self.cancel_button.pack(side=LEFT, padx=5)
        self.services_button = tb.Button(action_frame, text=self.get_string('btn_manage_services'), command=self.open_service_manager, bootstyle="primary-outline", state=DISABLED)
        self.services_button.pack(side=LEFT, padx=5)
        self.export_button = tb.Button(action_frame, text="Exportar para XLSX", command=self.export_to_xlsx, bootstyle="success-outline")
        self.export_button.pack(side=LEFT, padx=5)
        
        tree_frame = tb.LabelFrame(main_frame, text=self.get_string('created_orders_section'), bootstyle=INFO, padding=10)
        tree_frame.pack(fill=BOTH, expand=True)
        
        cols = ("id", "wo", "pn", "cliente", "equipamento", "data_previsao", "status")
        self.headers_treeview = (self.get_string('col_id'), self.get_string('col_wo'), "PN (Partnumber)", self.get_string('col_cliente'), self.get_string('equipment_label'), self.get_string('col_data_previsao'), self.get_string('col_status'))
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings", bootstyle=PRIMARY)
        for col, header in zip(cols, self.headers_treeview):
            self.tree.heading(col, text=header)
            self.tree.column(col, width=120, anchor=W)
        self.tree.column("id", width=50, anchor=CENTER)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = tb.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
    
    def _calcular_giros_previstos(self, event=None):
        try:
            tiragem_str = self.widgets["tiragem_em_folhas"].get()
            cores_desc = self.widgets["qtde_cores"].get()
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
        elif config["widget"] == "Listbox":
            # A criação da Listbox agora é manual dentro de create_widgets,
            # então aqui podemos apenas retornar None ou um placeholder.
            return None 
        else: return tb.Entry(parent)

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
        ordem_id, wo_number = item_values[0], item_values[1]
        ServiceManagerWindow(self, self.db_config, ordem_id, wo_number, refresh_callback=self.load_ordens)

    def open_edit_window(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning(self.get_string('selection_required_title'), self.get_string('select_order_to_edit_msg'), parent=self)
            return
        item_values = self.tree.item(selected_item, 'values')
        ordem_id = item_values[0]
        EditOrdemWindow(self, self.db_config, ordem_id, self.load_all_combobox_data)

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
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, numero_wo, pn_partnumber, cliente, equipamento, data_previsao_entrega, status FROM ordem_producao ORDER BY data_cadastro_pcp DESC")
                for row in cur.fetchall():
                    row_list = list(row)
                    if row_list[5] and isinstance(row_list[5], date): row_list[5] = row_list[5].strftime('%d/%m/%Y')
                    self.tree.insert("", END, values=tuple(row_list))
        except psycopg2.Error as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar ordens de produção: {e}", parent=self)
        finally:
            if conn: conn.close()

    def load_all_combobox_data(self):
        self.load_ordens()
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # Carrega o mapa de giros
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}
                
                # Itera sobre os widgets para popular os COMBOBOXES
                schemas = LOOKUP_TABLE_SCHEMAS
                for key, widget in self.widgets.items():
                    if isinstance(widget, tb.Combobox):
                        field_config = self.fields_config.get(key, {})
                        lookup_ref = field_config.get("lookup")
                        if lookup_ref and lookup_ref in schemas:
                            schema_info = schemas[lookup_ref]
                            
                            descriptive_col_key = None
                            if 'descricao' in schema_info['columns']: descriptive_col_key = 'descricao'
                            elif 'nome' in schema_info['columns']: descriptive_col_key = 'nome'
                            else: 
                                pk_db_col = schema_info['columns'][schema_info['pk_column']]['db_column']
                                for col_key, col_data in schema_info['columns'].items():
                                    if col_data['db_column'] != pk_db_col:
                                        descriptive_col_key = col_key
                                        break
                            
                            if descriptive_col_key:
                                db_col = schema_info['columns'][descriptive_col_key]['db_column']
                                cur.execute(f'SELECT DISTINCT "{db_col}" FROM {schema_info["table"]} ORDER BY "{db_col}"')
                                values = [str(row[0]) for row in cur.fetchall()]
                                widget['values'] = values
                
                # --- CORREÇÃO AQUI ---
                # O código abaixo agora está no lugar certo: DENTRO do 'try' e DEPOIS do loop dos comboboxes.
                
                # NOVO: Carregar dados para a Listbox de Acabamentos
                if "acabamento" in self.widgets and isinstance(self.widgets["acabamento"], Listbox):
                    acab_widget = self.widgets["acabamento"]
                    acab_widget.delete(0, END)  # Limpa a lista antes de carregar

                    schema_info_acab = LOOKUP_TABLE_SCHEMAS["acabamentos_tipos"]
                    
                    # Vamos buscar ID e Descrição juntos para criar o mapa
                    cur.execute(f'SELECT id, descricao FROM {schema_info_acab["table"]} ORDER BY descricao')
                    
                    self.acabamentos_map = {}  # Dicionário para mapear descrição -> id
                    for acab_id, desc in cur.fetchall():
                        acab_widget.insert(END, desc)
                        self.acabamentos_map[desc] = acab_id

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados para os comboboxes: {e}", parent=self)
        finally:
            if conn: conn.close()
    def save_new_ordem(self):
        data = {}
        self.widgets["giros_previstos"].config(state=NORMAL)
        for key, widget in self.widgets.items():
            if key == "acabamento": continue # Trataremos o acabamento separadamente
            if isinstance(widget, DateEntry): data[key] = widget.entry.get() or None
            elif isinstance(widget, tb.Text): data[key] = widget.get("1.0", "end-1c").strip()
            elif widget: data[key] = widget.get().strip()
        self.widgets["giros_previstos"].config(state=DISABLED)
        
        # Pega os acabamentos selecionados
        selected_indices = self.widgets["acabamento"].curselection()
        selected_acabamentos_desc = [self.widgets["acabamento"].get(i) for i in selected_indices]
        
        # O campo `acabamento` na tabela `ordem_producao` pode ser usado para um resumo em texto.
        data['acabamento'] = ', '.join(selected_acabamentos_desc)

        if not data["numero_wo"]:
            messagebox.showwarning(self.get_string("required_field_warning", field_name=self.get_string("col_wo")), parent=self)
            return
            
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                # Insere a ordem de produção principal
                cols_to_save = [k for k in self.fields_config.keys() if k in data]
                non_empty_data = {col: data[col] for col in cols_to_save if data[col]}
                if 'data_previsao_entrega' in non_empty_data and non_empty_data['data_previsao_entrega']:
                    non_empty_data['data_previsao_entrega'] = datetime.strptime(non_empty_data['data_previsao_entrega'], '%d/%m/%Y').date()
                
                cols = non_empty_data.keys()
                query = f""" INSERT INTO ordem_producao ({', '.join(f'"{c}"' for c in cols)}, status) 
                            VALUES ({', '.join([f'%({c})s' for c in cols])}, 'Em Aberto') RETURNING id """
                cur.execute(query, non_empty_data)
                ordem_id = cur.fetchone()[0] # Pega o ID da ordem recém-criada

                # Insere os acabamentos na tabela de ligação
                if ordem_id and selected_acabamentos_desc:
                    acabamento_ids_to_insert = [self.acabamentos_map[desc] for desc in selected_acabamentos_desc]
                    for acab_id in acabamento_ids_to_insert:
                        cur.execute("INSERT INTO ordem_producao_acabamentos (ordem_id, acabamento_id) VALUES (%s, %s)", (ordem_id, acab_id))

            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('order_save_success'), parent=self)
            self.clear_fields()
            self.load_ordens()
        except psycopg2.IntegrityError as e:
            conn.rollback()
            # Verificando se o erro é de chave única na WO
            if 'ordem_producao_numero_wo_key' in str(e):
                 messagebox.showerror("Erro de Integridade", self.get_string('integrity_error_wo', wo=data.get('numero_wo', '')), parent=self)
            else:
                messagebox.showerror("Erro de Integridade", f"Não foi possível salvar. Verifique se os dados estão corretos.\nDetalhes: {e}", parent=self)
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro ao Salvar", self.get_string('save_order_error', error=e), parent=self)
        finally:
            if conn: conn.close()

    def clear_fields(self):
        self.widgets["giros_previstos"].config(state=NORMAL)
        for key, widget in self.widgets.items():
            if isinstance(widget, tb.Combobox): widget.set('')
            elif isinstance(widget, DateEntry): widget.entry.delete(0, END)
            elif isinstance(widget, tb.Text): widget.delete("1.0", END)
            elif isinstance(widget, Listbox): widget.selection_clear(0, END) # Limpa a seleção
            elif widget: widget.delete(0, END) # Para Entry
        self.widgets["giros_previstos"].config(state=DISABLED)

    def export_to_xlsx(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma ou mais ordens na lista para exportar.", parent=self)
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Planilhas Excel", "*.xlsx"), ("Todos os Arquivos", "*.*")], title="Salvar Relatório de Ordens como XLSX")
        if not filepath: return
        conn = self.get_db_connection()
        if not conn: return
        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Ordens de Produção"
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM ordem_producao LIMIT 0")
                headers = [desc[0] for desc in cur.description]
                sheet.append(headers)
                ordem_ids_to_export = [self.tree.item(item, "values")[0] for item in selected_items]
                placeholders = ','.join(['%s'] * len(ordem_ids_to_export))
                query = f"SELECT * FROM ordem_producao WHERE id IN ({placeholders})"
                cur.execute(query, ordem_ids_to_export)
                for record in cur.fetchall():
                    processed_record = []
                    for cell_value in record:
                        if isinstance(cell_value, (date, datetime)): processed_record.append(cell_value.strftime('%d/%m/%Y'))
                        else: processed_record.append(cell_value)
                    sheet.append(processed_record)
            workbook.save(filepath)
            messagebox.showinfo("Sucesso", f"Relatório XLSX exportado com sucesso para:\n{filepath}", parent=self)
        except (psycopg2.Error, IOError, Exception) as e:
            messagebox.showerror("Erro na Exportação", f"Ocorreu um erro ao exportar a planilha:\n{e}", parent=self)
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
        self.giros_map = self.master.giros_map

        self.create_widgets()
        self.load_ordem_data()
        
        self.transient(master)
        self.grab_set()
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.master.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)
        form_frame = tb.LabelFrame(main_frame, text=self.get_string('form_data_section'), bootstyle=PRIMARY, padding=10)
        form_frame.pack(fill=X, pady=(0, 10), anchor=N)

        fields_left = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega", "tiragem_em_folhas", "equipamento"]
        fields_middle = ["giros_previstos", "qtde_cores", "tipo_papel", "gramatura", "formato", "fsc"]
        
        for i, key in enumerate(fields_left):
            if key not in self.fields_config: continue
            config = self.fields_config[key]
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=0, padx=5, pady=5, sticky=W)
            widget = self.master.create_widget_from_config(form_frame, config)
            widget.grid(row=i, column=1, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget

        for i, key in enumerate(fields_middle):
            if key not in self.fields_config: continue
            config = self.fields_config[key]
            tb.Label(form_frame, text=self.get_string(config["label_key"]) + ":").grid(row=i, column=2, padx=5, pady=5, sticky=W)
            widget = self.master.create_widget_from_config(form_frame, config)
            widget.grid(row=i, column=3, padx=5, pady=5, sticky=EW)
            self.widgets[key] = widget
            
        self.widgets["tiragem_em_folhas"].bind("<KeyRelease>", self._calcular_giros_previstos)
        self.widgets["qtde_cores"].bind("<<ComboboxSelected>>", self._calcular_giros_previstos)

        if "acabamento" in self.fields_config:
            acab_config = self.fields_config["acabamento"]
            tb.Label(form_frame, text=self.get_string(acab_config["label_key"]) + ":").grid(row=0, column=4, padx=5, pady=5, sticky=NW)
            acab_widget = tb.Text(form_frame, height=8, width=40)
            acab_widget.grid(row=0, column=5, rowspan=6, padx=5, pady=5, sticky="nsew")
            self.widgets["acabamento"] = acab_widget
        
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        form_frame.grid_columnconfigure(5, weight=2)

        btn_frame = tb.Frame(form_frame)
        btn_frame.grid(row=len(fields_left), column=0, columnspan=6, pady=10)
        tb.Button(btn_frame, text=self.get_string('save_changes_btn'), command=self.save_changes, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text=self.get_string('cancel_btn'), command=self.destroy, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

    def _calcular_giros_previstos(self, event=None):
        try:
            tiragem_str = self.widgets["tiragem_em_folhas"].get()
            cores_desc = self.widgets["qtde_cores"].get()
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
        except Exception as e: print(f"Erro ao calcular giros (edição): {e}")

    def load_ordem_data(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cols_to_fetch = [f'"{key}"' for key in self.fields_config.keys()]
                cur.execute(f"SELECT {', '.join(cols_to_fetch)} FROM ordem_producao WHERE id = %s", (self.ordem_id,))
                data = cur.fetchone()
                
                if data:
                    data_dict = dict(zip(self.fields_config.keys(), data))
                    self.title(self.get_string('edit_order_title', wo=data_dict.get('numero_wo', '')))
                    
                    for key, widget in self.widgets.items():
                        value = data_dict.get(key)
                        if value is not None:
                            if isinstance(widget, tb.Combobox):
                                if key in self.master.widgets:
                                     widget['values'] = self.master.widgets[key]['values']
                                widget.set(str(value))
                            elif isinstance(widget, DateEntry):
                                widget.entry.delete(0, END)
                                if isinstance(value, date): widget.entry.insert(0, value.strftime('%d/%m/%Y'))
                                else: widget.entry.insert(0, str(value))
                            elif isinstance(widget, tb.Text):
                                widget.delete('1.0', END)
                                widget.insert('1.0', str(value))
                            else: # Entry
                                widget.delete(0, END)
                                widget.insert(0, str(value))
                    self.widgets['giros_previstos'].config(state=DISABLED)
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", f"Falha ao carregar dados da ordem: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def save_changes(self):
        data = {}
        self.widgets["giros_previstos"].config(state=NORMAL)
        for key, widget in self.widgets.items():
            if isinstance(widget, DateEntry):
                date_val = widget.entry.get()
                data[key] = datetime.strptime(date_val, '%d/%m/%Y').date() if date_val else None
            elif isinstance(widget, tb.Text):
                data[key] = widget.get("1.0", "end-1c").strip()
            else:
                data[key] = widget.get().strip()
        self.widgets["giros_previstos"].config(state=DISABLED)

        if not data["numero_wo"]:
            messagebox.showwarning(self.get_string("required_field_warning", field_name=self.get_string("col_wo")), parent=self)
            return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                update_data = {k: v if v != '' else None for k, v in data.items()}
                set_clauses = [f'"{col}" = %s' for col in update_data.keys()]
                values = list(update_data.values()) + [self.ordem_id]
                query = f"UPDATE ordem_producao SET {', '.join(set_clauses)} WHERE id = %s"
                cur.execute(query, values)
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('update_order_success'), parent=self)
            if self.refresh_callback: self.refresh_callback()
            self.destroy()
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Erro ao Salvar", self.get_string('update_order_failed', error=e), parent=self)
        finally:
            if conn: conn.close()
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
