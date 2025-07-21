# -*- coding: utf-8 -*-

from datetime import date, datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap import DateEntry
from tkinter import messagebox, Toplevel, END, BOTH, YES, X, N, W, EW, DISABLED, NORMAL

from config import LANGUAGES

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

        fields_left = ["numero_wo", "pn_partnumber", "cliente", "data_previsao_entrega", "tiragem_em_folhas", "equipamento_id"]
        fields_middle = ["giros_previstos", "qtde_cores_id", "tipo_papel_id", "gramatura_id", "formato_id", "fsc_id"]
        
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
        self.widgets["qtde_cores_id"].bind("<<ComboboxSelected>>", self._calcular_giros_previstos)

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
            cores_desc = self.widgets["qtde_cores_id"].get()
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
