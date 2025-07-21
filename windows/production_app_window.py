# -*- coding: utf-8 -*-

from datetime import datetime, time, date
import json
import os
import psycopg2
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, END, W, E, S, N, CENTER, BOTH, YES, X
from tkinter.ttk import Treeview

# Importações do nosso projeto
from config import LANGUAGES, LOOKUP_TABLE_SCHEMAS

class App(Toplevel):
    STATE_FILE = 'session_state.json' # Ficheiro para guardar o estado

    def __init__(self, master, db_config):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.current_language = self.db_config.get('language', 'portugues')
        self.grab_set()
        self.set_localized_title()
        self.geometry("1200x850")

        # Variáveis de estado
        self.current_state = 'IDLE'
        self.setup_start_time, self.setup_end_time = None, None
        self.prod_start_time, self.prod_end_time = None, None
        self.setup_timer_job, self.prod_timer_job = None, None
        self.all_stops_data = []
        self.selected_ordem_id, self.selected_servico_id, self.setup_id = None, None, None
        self.open_wos_data, self.pending_services_data = {}, {}
        self.motivos_perda_data = {}
        self.giros_map = {}
        self.initial_fields, self.setup_fields, self.production_fields, self.info_labels = {}, {}, {}, {}
        
        self.create_widgets()
        self.load_initial_data()
        
        self.after(100, self.check_and_restore_state)
        self.periodic_save()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.master.current_language, LANGUAGES.get('portugues', {}))
        return lang_dict.get(key, f"_{key}_").format(**kwargs)

    def set_localized_title(self):
        self.title(self.get_string('btn_production_entry'))
        
    def save_state(self):
        if self.current_state == 'IDLE':
            if os.path.exists(self.STATE_FILE):
                try:
                    os.remove(self.STATE_FILE)
                except OSError as e:
                    print(f"Erro ao remover ficheiro de estado: {e}")
            return

        def time_to_str(t):
            return t.strftime('%H:%M:%S.%f') if t else None

        serializable_stops = []
        for stop in self.all_stops_data:
            s_copy = stop.copy()
            s_copy['hora_inicio_parada'] = time_to_str(s_copy.get('hora_inicio_parada'))
            s_copy['hora_fim_parada'] = time_to_str(s_copy.get('hora_fim_parada'))
            serializable_stops.append(s_copy)

        state_data = {
            'current_state': self.current_state,
            'selected_wo_text': self.wo_combobox.get(),
            'selected_service_text': self.service_combobox.get(),
            'selected_impressor': self.initial_fields['impressor'].get(),
            'selected_turno': self.initial_fields['turno'].get(),
            'setup_start_time': self.setup_start_time.isoformat() if self.setup_start_time else None,
            'setup_end_time': self.setup_end_time.isoformat() if self.setup_end_time else None,
            'prod_start_time': self.prod_start_time.isoformat() if self.prod_start_time else None,
            'prod_end_time': self.prod_end_time.isoformat() if self.prod_end_time else None,
            'all_stops_data': serializable_stops,
            'setup_fields': {key: widget.get() for key, widget in self.setup_fields.items()},
            'production_fields': {key: widget.get() for key, widget in self.production_fields.items() if isinstance(widget, tb.Entry)},
            'production_fields_combo': self.production_fields['motivo_perda'].get(),
            'setup_id': self.setup_id,
            'selected_ordem_id': self.selected_ordem_id,
            'selected_servico_id': self.selected_servico_id
        }
        try:
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado da sessão: {e}")

    def check_and_restore_state(self):
        if not os.path.exists(self.STATE_FILE) or os.path.getsize(self.STATE_FILE) == 0:
            self.update_ui_state()
            return
        try:
            with open(self.STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            if not state_data or state_data.get('current_state') == 'IDLE':
                 if os.path.exists(self.STATE_FILE): os.remove(self.STATE_FILE)
                 return

            if messagebox.askyesno("Restaurar Sessão", "Encontrámos um apontamento não finalizado. Deseja restaurá-lo?"):
                self.load_state(state_data)
            else:
                 if os.path.exists(self.STATE_FILE): os.remove(self.STATE_FILE)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Erro ao restaurar estado: {e}")
            if os.path.exists(self.STATE_FILE):
                os.remove(self.STATE_FILE)
        finally:
            self.update_ui_state()

    def load_state(self, state):
        try:
            self.current_state = state.get('current_state', 'IDLE')
            self.setup_id = state.get('setup_id')
            self.selected_ordem_id = state.get('selected_ordem_id')
            self.selected_servico_id = state.get('selected_servico_id')
            
            self.wo_combobox.set(state.get('selected_wo_text', ''))
            self.on_wo_selected(restoring=True)
            self.service_combobox.set(state.get('selected_service_text', ''))
            self.impressor_combobox.set(state.get('selected_impressor', ''))
            self.turno_combobox.set(state.get('selected_turno', ''))
            
            for key, value in state.get('setup_fields', {}).items():
                if key in self.setup_fields: self.setup_fields[key].insert(0, value)
            for key, value in state.get('production_fields', {}).items():
                if key in self.production_fields and isinstance(self.production_fields[key], tb.Entry): self.production_fields[key].insert(0, value)
            self.production_fields['motivo_perda'].set(state.get('production_fields_combo', ''))
            
            def str_to_time(t_str):
                return datetime.strptime(t_str, '%H:%M:%S.%f').time() if t_str else None
                
            self.all_stops_data = []
            for stop_data_str in state.get('all_stops_data', []):
                s_copy = stop_data_str.copy()
                s_copy['hora_inicio_parada'] = str_to_time(s_copy.get('hora_inicio_parada'))
                s_copy['hora_fim_parada'] = str_to_time(s_copy.get('hora_fim_parada'))
                self.all_stops_data.append(s_copy)
            self.refresh_stops_tree()
            
            def load_datetime_from_iso(iso_str):
                return datetime.fromisoformat(iso_str) if iso_str else None
                
            self.setup_start_time = load_datetime_from_iso(state.get('setup_start_time'))
            self.setup_end_time = load_datetime_from_iso(state.get('setup_end_time'))
            self.prod_start_time = load_datetime_from_iso(state.get('prod_start_time'))
            self.prod_end_time = load_datetime_from_iso(state.get('prod_end_time'))

            self.update_setup_timer()
            self.update_prod_timer()

        except Exception as e:
            messagebox.showerror("Erro de Restauração", f"Falha ao carregar dados da sessão anterior: {e}")
            self.reset_state()

    def periodic_save(self):
        self.save_state()
        self.after(30000, self.periodic_save)

    def on_close(self):
        if self.current_state != 'IDLE':
            self.save_state()
        self.destroy()
        
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
        self.update_wo_info_panel()
        self.update_ui_state()
        
        if os.path.exists(self.STATE_FILE):
            os.remove(self.STATE_FILE)

    def on_wo_selected(self, event=None, restoring=False):
        if not restoring:
            self.reset_state()
            
        self.service_combobox.set('')
        self.service_combobox.config(state='disabled')
        self.pending_services_data = {}
        
        selected_wo_text = self.wo_combobox.get()
        if not selected_wo_text: 
            self.selected_ordem_id = None
            self.update_wo_info_panel()
            self.update_ui_state()
            return

        wo_data = self.open_wos_data.get(selected_wo_text)
        if not wo_data: return
        
        self.selected_ordem_id = wo_data['id']
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, descricao FROM ordem_servicos WHERE ordem_id = %s AND status = 'Pendente' ORDER BY sequencia", (self.selected_ordem_id,))
                services = cur.fetchall()
                if services:
                    service_list = [f"{service_id}: {desc}" for service_id, desc in services]
                    self.pending_services_data = {f"{service_id}: {desc}": service_id for service_id, desc in services}
                    self.service_combobox['values'] = service_list
                    self.service_combobox.config(state='readonly')
                    if not restoring: self.service_combobox.set('')
                else:
                    self.service_combobox['values'] = []
                    self.service_combobox.set(self.get_string('no_pending_services'))
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Falha ao carregar etapas da WO: {e}", parent=self)
        finally:
            if conn: conn.close()
        
        self.update_wo_info_panel()
        self.update_ui_state()
        
        if not restoring:
            self.save_state()

    def toggle_setup(self):
        if self.current_state == 'IDLE':
            if not self.service_combobox.get() or not self.impressor_combobox.get() or not self.turno_combobox.get() or self.service_combobox.get() == self.get_string('no_pending_services'):
                messagebox.showwarning("Seleção Incompleta", "Selecione WO, Etapa, Impressor e Turno para iniciar.")
                return
            
            selected_service_text = self.service_combobox.get()
            self.selected_servico_id = self.pending_services_data.get(selected_service_text)
            if not self.selected_servico_id:
                messagebox.showerror("Erro", f"Não foi possível encontrar o ID para a etapa: {selected_service_text}")
                return

            self.current_state = 'SETUP_RUNNING'
            self.setup_start_time = datetime.now()
            self.update_setup_timer()
            
        elif self.current_state == 'SETUP_RUNNING':
            self.setup_end_time = datetime.now()
            if self.setup_timer_job: self.after_cancel(self.setup_timer_job)
            self.update_setup_timer() # Atualiza a label uma última vez com o tempo final
            
            if not self.validate_and_save_setup():
                self.setup_end_time = None
                self.update_setup_timer() # Reinicia o timer se a validação falhar
                return
            self.current_state = 'PRODUCTION_READY'

        self.update_ui_state()
        self.save_state()

    def toggle_production(self):
        if self.current_state == 'PRODUCTION_READY':
            self.current_state = 'PRODUCTION_RUNNING'
            self.prod_start_time = datetime.now()
            self.update_prod_timer()
        elif self.current_state == 'PRODUCTION_RUNNING':
            self.current_state = 'FINISHED'
            self.prod_end_time = datetime.now()
            if self.prod_timer_job: self.after_cancel(self.prod_timer_job)
            self.update_prod_timer() # Atualiza a label com o tempo final

        self.update_ui_state()
        self.save_state()
    
    def validate_and_save_setup(self):
        data = {key: widget.get().strip() for key, widget in self.setup_fields.items()}
        for key, value in data.items():
            if not value:
                messagebox.showerror("Campos Obrigatórios", self.get_string('setup_fields_required'))
                return False
        
        conn = self.get_db_connection()
        if not conn: return False
        try:
            with conn.cursor() as cur:
                params = (
                    self.setup_start_time.date(),
                    self.setup_start_time,
                    self.setup_end_time,
                    int(data['perdas']),
                    int(data['malas']),
                    int(data['total_lavagens']),
                    data['numero_inspecao']
                )

                if self.setup_id: # UPDATE
                    query = "UPDATE apontamento_setup SET data_apontamento=%s, hora_inicio=%s, hora_fim=%s, perdas=%s, malas=%s, total_lavagens=%s, numero_inspecao=%s WHERE id=%s"
                    cur.execute(query, params + (self.setup_id,))
                    cur.execute("DELETE FROM paradas_setup WHERE setup_id = %s", (self.setup_id,))
                
                else: # INSERT
                    query = "INSERT INTO apontamento_setup (servico_id, data_apontamento, hora_inicio, hora_fim, perdas, malas, total_lavagens, numero_inspecao) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
                    cur.execute(query, (self.selected_servico_id,) + params)
                    self.setup_id = cur.fetchone()[0]

                for stop in self.all_stops_data:
                    if stop.get('type') == 'Setup':
                        cur.execute("INSERT INTO paradas_setup (setup_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s)",
                            (self.setup_id, stop.get('motivo_id'), stop.get('hora_inicio_parada'), stop.get('hora_fim_parada'), stop.get('motivo_extra_detail')))
            
            conn.commit()
            messagebox.showinfo("Sucesso", self.get_string('setup_saved_success'))
            return True
            
        except (psycopg2.Error, ValueError) as e:
            conn.rollback()
            messagebox.showerror("Erro", self.get_string('setup_save_failed', error=e))
            return False
        finally:
            if conn: conn.close()

    def update_setup_timer(self):
        if self.setup_start_time:
            if self.current_state == 'SETUP_RUNNING' and not self.setup_end_time:
                elapsed = datetime.now() - self.setup_start_time
                self.setup_timer_label.config(text=str(elapsed).split('.')[0])
                self.setup_timer_job = self.after(1000, self.update_setup_timer)
            elif self.setup_end_time:
                elapsed = self.setup_end_time - self.setup_start_time
                self.setup_timer_label.config(text=str(elapsed).split('.')[0])
        else:
            self.setup_timer_label.config(text="00:00:00")
            
    def update_prod_timer(self):
        if self.prod_start_time:
            if self.current_state == 'PRODUCTION_RUNNING' and not self.prod_end_time:
                elapsed = datetime.now() - self.prod_start_time
                self.prod_timer_label.config(text=str(elapsed).split('.')[0])
                self.prod_timer_job = self.after(1000, self.update_prod_timer)
            elif self.prod_end_time:
                elapsed = self.prod_end_time - self.prod_start_time
                self.prod_timer_label.config(text=str(elapsed).split('.')[0])
        else:
            self.prod_timer_label.config(text="00:00:00")

    def refresh_stops_tree(self):
        for item in self.stops_tree.get_children(): self.stops_tree.delete(item)
        for stop in self.all_stops_data:
            start = stop.get('hora_inicio_parada')
            end = stop.get('hora_fim_parada')
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

    def submit_final_production(self):
        self.production_fields['giros_rodados'].config(state=NORMAL)
        prod_data = {key: (widget.get().strip() if isinstance(widget, (tb.Entry, tb.Combobox)) else None) for key, widget in self.production_fields.items()}
        self.production_fields['giros_rodados'].config(state=DISABLED)

        if not prod_data.get('giros_rodados') or not prod_data.get('quantidadeproduzida'):
            messagebox.showerror("Validação", self.get_string('final_appointment_validation_error'), parent=self)
            return

        final_data = {
            'servico_id': self.selected_servico_id,
            'data': date.today(),
            'horainicio': self.prod_start_time.time() if self.prod_start_time else None,
            'horafim': self.prod_end_time.time() if self.prod_end_time else None,
            'giros_rodados': int(prod_data['giros_rodados']) if prod_data.get('giros_rodados') else None,
            'quantidadeproduzida': int(prod_data['quantidadeproduzida']) if prod_data.get('quantidadeproduzida') else None,
            'perdas_producao': int(prod_data['perdas_producao']) if prod_data.get('perdas_producao') else None,
            'motivo_perda_id': self.motivos_perda_data.get(prod_data.get('motivo_perda')),
        }
        
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM impressores WHERE nome = %s", (self.impressor_combobox.get(),))
                final_data['impressor_id'] = cur.fetchone()[0]
                cur.execute("SELECT id FROM turnos_tipos WHERE descricao = %s", (self.turno_combobox.get(),))
                final_data['turno_id'] = cur.fetchone()[0]

                cols = [f'"{k}"' for k, v in final_data.items() if v is not None]
                vals = {k: v for k, v in final_data.items() if v is not None}
                placeholders = [f"%({k})s" for k in vals.keys()]
                
                query = f"INSERT INTO apontamento ({', '.join(cols)}) VALUES ({', '.join(placeholders)}) RETURNING id"
                cur.execute(query, vals)
                apontamento_id = cur.fetchone()[0]

                for stop in self.all_stops_data:
                    if stop.get('type') == 'Produção':
                        cur.execute("INSERT INTO paradas (apontamento_id, motivo_id, hora_inicio_parada, hora_fim_parada, motivo_extra_detail) VALUES (%s, %s, %s, %s, %s)",
                            (apontamento_id, stop.get('motivo_id'), stop.get('hora_inicio_parada'), stop.get('hora_fim_parada'), stop.get('motivo_extra_detail')))
                
                cur.execute("UPDATE ordem_servicos SET status = 'Concluído' WHERE id = %s", (self.selected_servico_id,))
                cur.execute("SELECT COUNT(*) FROM ordem_servicos WHERE ordem_id = %s AND status = 'Pendente'", (self.selected_ordem_id,))
                if cur.fetchone()[0] == 0:
                    cur.execute("UPDATE ordem_producao SET status = 'Concluído' WHERE id = %s", (self.selected_ordem_id,))

            conn.commit()
            
            if os.path.exists(self.STATE_FILE):
                os.remove(self.STATE_FILE)

            messagebox.showinfo("Sucesso", self.get_string('production_saved_success'), parent=self)
            self.current_state = 'IDLE'
            self.destroy()

        except (psycopg2.Error, ValueError, KeyError, TypeError) as e:
            conn.rollback()
            messagebox.showerror("Erro ao Salvar", self.get_string('production_save_failed', error=e), parent=self)
        finally:
            if conn: conn.close()
    
    def update_setup_timer(self):
        if self.setup_start_time:
            if self.current_state == 'SETUP_RUNNING':
                elapsed = datetime.now() - self.setup_start_time
                self.setup_timer_label.config(text=str(elapsed).split('.')[0])
                self.setup_timer_job = self.after(1000, self.update_setup_timer)
            elif self.setup_end_time:
                elapsed = self.setup_end_time - self.setup_start_time
                self.setup_timer_label.config(text=str(elapsed).split('.')[0])
        else:
            self.setup_timer_label.config(text="00:00:00")
            
    def update_prod_timer(self):
        if self.prod_start_time:
            if self.current_state == 'PRODUCTION_RUNNING':
                elapsed = datetime.now() - self.prod_start_time
                self.prod_timer_label.config(text=str(elapsed).split('.')[0])
                self.prod_timer_job = self.after(1000, self.update_prod_timer)
            elif self.prod_end_time:
                elapsed = self.prod_end_time - self.prod_start_time
                self.prod_timer_label.config(text=str(elapsed).split('.')[0])
        else:
            self.prod_timer_label.config(text="00:00:00")
    
    def open_stop_window(self, stop_type):
        callback = self.add_setup_stop if stop_type == 'setup' else self.add_prod_stop
        RealTimeStopWindow(self, self.db_config, callback)

    def add_setup_stop(self, stop_data):
        stop_data['type'] = 'Setup'
        self.all_stops_data.append(stop_data)
        self.refresh_stops_tree()
        self.save_state()
    
    def add_prod_stop(self, stop_data):
        stop_data['type'] = 'Produção'
        self.all_stops_data.append(stop_data)
        self.refresh_stops_tree()
        self.save_state()

    def refresh_stops_tree(self):
        for item in self.stops_tree.get_children(): self.stops_tree.delete(item)
        for stop in self.all_stops_data:
            start_str = stop['hora_inicio_parada'].strftime('%H:%M:%S') if stop.get('hora_inicio_parada') else ''
            end_str = stop['hora_fim_parada'].strftime('%H:%M:%S') if stop.get('hora_fim_parada') else ''
            
            duration_str = ''
            if stop.get('hora_inicio_parada') and stop.get('hora_fim_parada'):
                duration = (datetime.combine(date.min, stop['hora_fim_parada']) - datetime.combine(date.min, stop['hora_inicio_parada']))
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            
            motivo_display = stop.get('motivo_text', '')
            if motivo_display and motivo_display.lower() == 'outros' and stop.get('motivo_extra_detail'):
                motivo_display = f"Outros: {stop['motivo_extra_detail']}"
                
            self.stops_tree.insert('', END, values=(stop.get('type', ''), motivo_display, start_str, end_str, duration_str))
            
    # Inclua aqui os métodos que não foram alterados:
    # create_widgets, _calcular_giros_rodados, get_db_connection,
    # load_initial_data, load_open_wos, update_wo_info_panel, update_ui_state
    def create_widgets(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        main_frame.grid_columnconfigure(0, weight=1)

        top_frame = tb.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        selection_frame = tb.LabelFrame(top_frame, text=self.get_string('initial_selection_section'), bootstyle=PRIMARY, padding=15)
        selection_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        selection_frame.grid_columnconfigure(1, weight=1)
        
        tb.Label(selection_frame, text="Selecionar WO:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.wo_combobox = tb.Combobox(selection_frame, state="readonly")
        self.wo_combobox.grid(row=0, column=1, sticky=EW, padx=5, pady=2)
        self.wo_combobox.bind("<<ComboboxSelected>>", self.on_wo_selected)

        tb.Label(selection_frame, text=self.get_string("service_select_label")).grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.service_combobox = tb.Combobox(selection_frame, state="disabled")
        self.service_combobox.grid(row=1, column=1, sticky=EW, padx=5, pady=2)
        self.service_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_ui_state())

        tb.Label(selection_frame, text=self.get_string("printer_label") + ":").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.impressor_combobox = tb.Combobox(selection_frame, state="readonly")
        self.impressor_combobox.grid(row=2, column=1, sticky=EW, padx=5, pady=2)
        self.initial_fields['impressor'] = self.impressor_combobox
        
        tb.Label(selection_frame, text=self.get_string("shift_label") + ":").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        self.turno_combobox = tb.Combobox(selection_frame, state="readonly")
        self.turno_combobox.grid(row=3, column=1, sticky=EW, padx=5, pady=2)
        self.initial_fields['turno'] = self.turno_combobox
        
        self.wo_info_frame = tb.LabelFrame(top_frame, text="Informações da Ordem", bootstyle=PRIMARY, padding=15)
        self.wo_info_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        info_keys = {
            'col_cliente': 'Cliente', 'equipment_label': 'Equipamento', 
            'col_tipo_papel': 'Tipo Papel', 'col_tiragem_em_folhas': 'Tiragem Meta',
            'col_qtde_cores': 'QTDE Cores', 'giros_previstos': 'Giros Previstos'
        }
        for i, (key, text) in enumerate(info_keys.items()):
            display_text = self.get_string(key) if self.get_string(key) != key else text
            tb.Label(self.wo_info_frame, text=f"{display_text}:", font="-weight bold").grid(row=i, column=0, sticky=W, padx=5, pady=2)
            label_widget = tb.Label(self.wo_info_frame, text="-")
            label_widget.grid(row=i, column=1, sticky=W, padx=5, pady=2)
            self.info_labels[key] = label_widget

        process_frame = tb.Frame(main_frame)
        process_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=5)
        process_frame.grid_columnconfigure(0, weight=1)
        process_frame.grid_columnconfigure(1, weight=1)

        self.setup_frame = tb.LabelFrame(process_frame, text=self.get_string('setup_section'), bootstyle=INFO, padding=15)
        self.setup_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.setup_frame.grid_columnconfigure(0, weight=1)
        
        setup_entries_frame = tb.Frame(self.setup_frame)
        setup_entries_frame.pack(fill=X, expand=YES, pady=(0,10))
        setup_fields_defs = {'perdas': 'col_perdas', 'malas': 'col_malas', 'total_lavagens': 'col_total_lavagens', 'numero_inspecao': 'col_numeroinspecao'}
        for key, label_key in setup_fields_defs.items():
            tb.Label(setup_entries_frame, text=self.get_string(label_key) + ":").pack(fill=X, pady=2)
            entry = tb.Entry(setup_entries_frame)
            entry.pack(fill=X)
            self.setup_fields[key] = entry
        
        setup_control_frame = tb.Frame(self.setup_frame)
        setup_control_frame.pack(fill=X, expand=YES)
        self.setup_timer_label = tb.Label(setup_control_frame, text="00:00:00", font=("Helvetica", 20, "bold"))
        self.setup_timer_label.pack(pady=5)
        self.setup_button = tb.Button(setup_control_frame, text=self.get_string('start_setup_btn'), bootstyle="info", command=self.toggle_setup, width=20)
        self.setup_button.pack(pady=5, ipady=5)
        self.setup_stop_button = tb.Button(setup_control_frame, text=self.get_string('point_setup_stop_btn'), command=lambda: self.open_stop_window('setup'), state=DISABLED, width=20)
        self.setup_stop_button.pack(pady=5, ipady=5)
        
        self.prod_frame = tb.LabelFrame(process_frame, text=self.get_string('production_section'), bootstyle=SUCCESS, padding=15)
        self.prod_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.prod_frame.grid_columnconfigure(0, weight=1)

        prod_entries_frame = tb.Frame(self.prod_frame)
        prod_entries_frame.pack(fill=X, expand=YES, pady=(0,10))
        prod_fields_defs = {'giros_rodados': 'col_giros_rodados', 'quantidadeproduzida': 'col_quantidadeproduzida', 'perdas_producao': 'col_perdas_producao'}
        for key, label_key in prod_fields_defs.items():
            tb.Label(prod_entries_frame, text=self.get_string(label_key) + ":").pack(fill=X, pady=2)
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
        self.prod_timer_label = tb.Label(prod_control_frame, text="00:00:00", font=("Helvetica", 20, "bold"))
        self.prod_timer_label.pack(pady=5)
        self.prod_button = tb.Button(prod_control_frame, text=self.get_string('start_production_btn'), bootstyle="success", command=self.toggle_production, width=20)
        self.prod_button.pack(pady=5, ipady=5)
        self.prod_stop_button = tb.Button(prod_control_frame, text=self.get_string('point_prod_stop_btn'), command=lambda: self.open_stop_window('production'), state=DISABLED, width=20)
        self.prod_stop_button.pack(pady=5, ipady=5)

        stops_frame = tb.LabelFrame(main_frame, text="Histórico de Paradas", padding=10)
        stops_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=5)
        
        self.stops_tree = tb.Treeview(stops_frame, columns=('tipo', 'motivo', 'inicio', 'fim', 'duracao'), show='headings', height=5)
        self.stops_tree.heading('tipo', text="Tipo"); self.stops_tree.column('tipo', width=80, anchor=CENTER)
        self.stops_tree.heading('motivo', text="Motivo"); self.stops_tree.column('motivo', width=250)
        self.stops_tree.heading('inicio', text="Início"); self.stops_tree.column('inicio', width=100, anchor=CENTER)
        self.stops_tree.heading('fim', text="Fim"); self.stops_tree.column('fim', width=100, anchor=CENTER)
        self.stops_tree.heading('duracao', text="Duração"); self.stops_tree.column('duracao', width=100, anchor=CENTER)
        self.stops_tree.pack(fill=BOTH, expand=YES)
        
        self.final_register_button = tb.Button(main_frame, text=self.get_string("register_entry_btn"), command=self.submit_final_production, state=DISABLED)
        self.final_register_button.grid(row=3, column=0, columnspan=2, pady=20, ipady=10)

        status_bar = tb.Frame(main_frame, padding=(10, 5))
        status_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10,0))
        tb.Label(status_bar, text="Status:", font=("Helvetica", 12, "bold")).pack(side=LEFT)
        self.status_label = tb.Label(status_bar, text=self.get_string('status_idle'), font=("Helvetica", 12, "bold"), bootstyle="secondary")
        self.status_label.pack(side=LEFT, padx=10)

    def _calcular_giros_rodados(self, event=None):
        try:
            qtde_produzida_str = self.production_fields['quantidadeproduzida'].get()
            cores_desc = self.info_labels.get('col_qtde_cores', tb.Label()).cget("text") 

            if not qtde_produzida_str or not cores_desc or cores_desc == '-': return
            
            qtde_produzida = int(qtde_produzida_str)
            multiplicador = self.giros_map.get(cores_desc, 1) 
            giros_calculado = qtde_produzida * multiplicador
            
            giros_widget = self.production_fields['giros_rodados']
            giros_widget.config(state=NORMAL)
            giros_widget.delete(0, END)
            giros_widget.insert(0, str(giros_calculado))
            giros_widget.config(state=DISABLED)
            
        except (ValueError, TclError): pass 
        except Exception as e: print(f"Erro ao calcular giros rodados: {e}")

    def get_db_connection(self):
        return self.master.get_db_connection()

    def load_initial_data(self):
        self.load_open_wos()
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT descricao, giros FROM qtde_cores_tipos')
                self.giros_map = {desc: giros if giros is not None else 1 for desc, giros in cur.fetchall()}
                
                cur.execute('SELECT nome FROM impressores ORDER BY nome')
                self.impressor_combobox['values'] = [row[0] for row in cur.fetchall()]
                cur.execute('SELECT descricao FROM turnos_tipos ORDER BY id')
                self.turno_combobox['values'] = [row[0] for row in cur.fetchall()]
                cur.execute('SELECT id, descricao FROM motivos_perda_tipos ORDER BY descricao')
                self.motivos_perda_data = {desc: mid for mid, desc in cur.fetchall()}
                self.motivo_perda_combobox['values'] = list(self.motivos_perda_data.keys())
        except Exception as e:
            messagebox.showwarning("Erro", f"Falha ao carregar dados iniciais: {e}", parent=self)
        finally:
            if conn: conn.close()

    def load_open_wos(self):
        self.open_wos_data = {}
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, numero_wo, cliente FROM ordem_producao WHERE status != 'Concluído' ORDER BY numero_wo")
                wos_list = []
                for ordem_id, numero_wo, cliente in cur.fetchall():
                    display_text = f"{numero_wo} - {cliente or 'Sem Cliente'}"
                    wos_list.append(display_text)
                    self.open_wos_data[display_text] = {"id": ordem_id}
                self.wo_combobox['values'] = wos_list
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Não foi possível carregar as Ordens de Serviço: {e}", parent=self)
        finally:
            if conn: conn.close()

    def update_wo_info_panel(self):
        for label in self.info_labels.values(): label.config(text="-")
        if not self.selected_ordem_id: return

        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:            
                info_cols = ['cliente', 'equipamento', 'tipo_papel', 'tiragem_em_folhas', 'qtde_cores', 'giros_previstos']
                cur.execute(f"SELECT {', '.join(info_cols)} FROM ordem_producao WHERE id = %s", (self.selected_ordem_id,))
                data = cur.fetchone()
                if data:
                    data_dict = dict(zip(info_cols, data))
                    self.info_labels['col_cliente'].config(text=data_dict.get('cliente', '-'))
                    self.info_labels['equipment_label'].config(text=data_dict.get('equipamento', '-'))
                    self.info_labels['col_tipo_papel'].config(text=data_dict.get('tipo_papel', '-'))
                    self.info_labels['col_tiragem_em_folhas'].config(text=data_dict.get('tiragem_em_folhas', '-'))
                    self.info_labels['col_qtde_cores'].config(text=data_dict.get('qtde_cores', '-'))
                    self.info_labels['giros_previstos'].config(text=data_dict.get('giros_previstos', '-'))
        except psycopg2.Error as e:
            messagebox.showerror("Erro", f"Falha ao carregar informações da WO: {e}", parent=self)
        finally:
            if conn: conn.close()
            
    def update_ui_state(self):
        state = self.current_state
        is_idle = state == 'IDLE'
        is_setup_running = state == 'SETUP_RUNNING'
        is_prod_ready = state == 'PRODUCTION_READY'
        is_prod_running = state == 'PRODUCTION_RUNNING'
        is_finished = state == 'FINISHED'

        # Controla campos iniciais
        for widget in [self.wo_combobox, self.service_combobox, self.impressor_combobox, self.turno_combobox]:
            widget.config(state='readonly' if is_idle else 'disabled')

        # Controla campos de setup
        for widget in self.setup_fields.values():
            widget.config(state='normal' if is_setup_running else 'disabled')

        # Controla campos de produção
        for key, widget in self.production_fields.items():
            if key != 'giros_rodados':
                widget.config(state='normal' if is_prod_running or is_finished else 'disabled')
        if not (is_prod_running or is_finished):
            self.production_fields['giros_rodados'].config(state='disabled')


        # Controla botões
        self.setup_button.config(state='normal' if is_idle or is_setup_running else 'disabled')
        if is_idle: self.setup_button.config(text=self.get_string('start_setup_btn'))
        if is_setup_running: self.setup_button.config(text=self.get_string('finish_setup_btn'))

        self.setup_stop_button.config(state='normal' if is_setup_running else 'disabled')

        self.prod_button.config(state='normal' if is_prod_ready or is_prod_running else 'disabled')
        if is_prod_ready: self.prod_button.config(text=self.get_string('start_production_btn'))
        if is_prod_running: self.prod_button.config(text=self.get_string('finish_production_btn'))

        self.prod_stop_button.config(state='normal' if is_prod_running else 'disabled')
        self.final_register_button.config(state='normal' if is_finished else 'disabled')
        
        status_map = {
            'IDLE': ('status_idle', 'secondary'),
            'SETUP_RUNNING': ('status_setup_running', 'info'),
            'PRODUCTION_READY': ('status_setup_done', 'primary'),
            'PRODUCTION_RUNNING': ('status_prod_running', 'success'),
            'FINISHED': ('status_prod_done', 'warning')
        }
        status_key, bootstyle = status_map.get(state, ('status_idle', 'secondary'))
        self.status_label.config(text=self.get_string(status_key), bootstyle=bootstyle)

class RealTimeStopWindow(Toplevel):
    
    def __init__(self, master, db_config, stop_callback):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.stop_callback = stop_callback

        self.title(self.master.get_string('stop_tracking_window_title'))
        self.geometry("500x300") # Aumentei um pouco a altura
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
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(main_frame, text=self.get_string('stop_reason_label'), font=("Helvetica", 10)).pack(pady=(0, 5))
        self.motivo_combobox = tb.Combobox(main_frame, state="readonly")
        self.motivo_combobox.pack(fill=X, pady=(0, 10))
        self.motivo_combobox.bind("<<ComboboxSelected>>", self.on_reason_selected)

        # --- WIDGETS PARA "OUTROS" ---
        # Criamos os widgets aqui, mas eles serão exibidos apenas quando necessário
        self.other_reason_label = tb.Label(main_frame, text=self.get_string('other_motives_label') + ":", font=("Helvetica", 10))
        self.other_reason_entry = tb.Entry(main_frame)
        
        # Frame para o timer e o botão, para mantê-los juntos
        timer_button_frame = tb.Frame(main_frame)
        timer_button_frame.pack(fill=X, pady=(10,0))
        
        tb.Label(timer_button_frame, text=self.get_string('stop_time_label'), font=("Helvetica", 10)).pack()
        self.timer_label = tb.Label(timer_button_frame, text="00:00:00", font=("Helvetica", 20, "bold"), bootstyle=DANGER)
        self.timer_label.pack()

        self.finish_button = tb.Button(timer_button_frame, text=self.get_string('finish_stop_btn'), bootstyle="danger", state=DISABLED, command=self.finish_stop)
        self.finish_button.pack(pady=(10,0), ipadx=10, ipady=5)


    def get_db_connection(self):
        return self.master.get_db_connection()

    def load_motivos_parada(self):
        conn = self.get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                schema = LOOKUP_TABLE_SCHEMAS["motivos_parada_tipos"]
                query = f'SELECT "{schema["columns"]["descricao"]["db_column"]}", "{schema["pk_column"]}" FROM {schema["table"]} ORDER BY "{schema["columns"]["descricao"]["db_column"]}"'
                cur.execute(query)
                self.motivos_parada_options = cur.fetchall()
                self.motivo_combobox['values'] = [opt[0] for opt in self.motivos_parada_options]
        except psycopg2.Error as e:
            messagebox.showwarning("Erro", f"Falha ao carregar motivos de parada: {e}", parent=self)
        finally:
            if conn: conn.close()

    def on_reason_selected(self, event=None):
        selected_reason = self.motivo_combobox.get()
        
        # Lógica para mostrar/ocultar widgets - AGORA CORRIGIDA
        # Usamos o método .lower() para ser à prova de "Outros" vs "outros"
        if selected_reason and selected_reason.lower() == 'outros':
            self.other_reason_label.pack(fill=X, pady=(10, 0), before=self.timer_label.master)
            self.other_reason_entry.pack(fill=X, before=self.timer_label.master)
            self.other_reason_entry.focus()
        else:
            self.other_reason_entry.delete(0, END) # Limpa o campo antes de esconder
            self.other_reason_label.pack_forget()
            self.other_reason_entry.pack_forget()

        # Habilita o botão de finalizar
        if selected_reason:
            self.finish_button.config(state=NORMAL)
        else:
            self.finish_button.config(state=DISABLED)

    def update_timer(self):
        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
        self.timer_job = self.after(1000, self.update_timer)

    def finish_stop(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
        
        end_time = datetime.now()
        selected_motivo_text = self.motivo_combobox.get()
        motivo_id = next((opt[1] for opt in self.motivos_parada_options if opt[0] == selected_motivo_text), None)

        extra_detail = None
        if selected_motivo_text and selected_motivo_text.lower() == 'outros':
            extra_detail = self.other_reason_entry.get().strip()
            if not extra_detail:
                messagebox.showwarning("Campo Obrigatório", "Por favor, especifique o motivo da parada.", parent=self)
                self.update_timer() # Reinicia o timer para não perder tempo
                return
        
        stop_data = {
            "motivo_text": selected_motivo_text,
            "motivo_id": motivo_id,
            "hora_inicio_parada": self.start_time.time(),
            "hora_fim_parada": end_time.time(),
            "motivo_extra_detail": extra_detail
        }
        
        self.stop_callback(stop_data)
        self.destroy()
