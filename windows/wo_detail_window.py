# -*- coding: utf-8 -*-

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel

from config import LANGUAGES

class WODetailWindow(Toplevel):
    def __init__(self, master, db_config, ordem_id):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.ordem_id = ordem_id
        self.current_language = self.master.current_language

        self.title(f"Detalhes da Ordem de Produção")
        self.geometry("1000x600")
        self.grab_set()

        self.create_widgets()
        self.load_details()

    def get_string(self, key, **kwargs):
        lang_dict = LANGUAGES.get(self.current_language, LANGUAGES['portugues'])
        return lang_dict.get(key, key).format(**kwargs)

    def get_db_connection(self):
        return self.master.get_db_connection()

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=True)

        self.title_label = tb.Label(main_frame, text=f"Acompanhamento da WO:", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=(0, 15))

        tree_frame = tb.Frame(main_frame)
        tree_frame.pack(fill=BOTH, expand=True)

        cols = ('sequencia', 'servico', 'status', 'papel', 'cores', 'tiragem', 'operador', 'inicio', 'fim')
        headers = ('Seq.', 'Serviço/Máquina', 'Status', 'Papel', 'Cores', 'Tiragem Meta', 'Operador', 'Início Prod.', 'Fim Prod.')
        
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor=CENTER, width=110)
        
        self.tree.column('servico', anchor=W, width=180)
        self.tree.pack(fill=BOTH, expand=True)

    def load_details(self):
            conn = self.get_db_connection()
            if not conn: return
            try:
                with conn.cursor() as cur:
                    # Query que junta todas as informações de cada etapa da WO
                    query = """
                        SELECT 
                            os.sequencia,
                            os.descricao,
                            os.status,
                            tp.descricao as papel,
                            qc.descricao as cores,
                            opm.tiragem_em_folhas,
                            imp.nome as impressor_nome,
                            ap.horainicio,
                            ap.horafim,
                            op.numero_wo
                        FROM ordem_servicos os
                        JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                        JOIN ordem_producao op ON os.ordem_id = op.id
                        LEFT JOIN tipos_papel tp ON opm.tipo_papel_id = tp.id
                        LEFT JOIN qtde_cores_tipos qc ON opm.qtde_cores_id = qc.id
                        LEFT JOIN apontamento ap ON ap.servico_id = os.id
                        LEFT JOIN impressores imp ON ap.impressor_id = imp.id
                        WHERE os.ordem_id = %s
                        ORDER BY os.sequencia;
                    """
                    cur.execute(query, (self.ordem_id,))

                    wo_number_set = False
                    for row in cur.fetchall():
                        # Formata os dados para exibição
                        seq, serv, status, papel, cores, tiragem, op, inicio, fim, wo_num = row
                        if not wo_number_set and wo_num:
                            self.title_label.config(text=f"Acompanhamento da WO: {wo_num}")
                            wo_number_set = True

                        values = (
                            seq or '',
                            serv or '',
                            status or '',
                            papel or '-',
                            cores or '-',
                            tiragem or '',
                            op or '-',
                            inicio.strftime('%H:%M') if inicio else '-',
                            fim.strftime('%H:%M') if fim else '-'
                        )
                        self.tree.insert('', 'end', values=values)

            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível carregar os detalhes da WO: {e}", parent=self)
            finally:
                # CORREÇÃO AQUI
                if conn: conn.close()
            conn = self.get_db_connection()
            if not conn: return
            try:
                with conn.cursor() as cur:
                    # Query que junta todas as informações de cada etapa da WO
                    query = """
                        SELECT 
                            os.sequencia,
                            os.descricao,
                            os.status,
                            tp.descricao as papel,
                            qc.descricao as cores,
                            opm.tiragem_em_folhas,
                            imp.nome as impressor_nome,
                            ap.horainicio,
                            ap.horafim,
                            op.numero_wo
                        FROM ordem_servicos os
                        JOIN ordem_producao_maquinas opm ON os.maquina_id = opm.id
                        JOIN ordem_producao op ON os.ordem_id = op.id
                        LEFT JOIN tipos_papel tp ON opm.tipo_papel_id = tp.id
                        LEFT JOIN qtde_cores_tipos qc ON opm.qtde_cores_id = qc.id
                        LEFT JOIN apontamento ap ON ap.servico_id = os.id
                        LEFT JOIN impressores imp ON ap.impressor_id = imp.id
                        WHERE os.ordem_id = %s
                        ORDER BY os.sequencia;
                    """
                    cur.execute(query, (self.ordem_id,))

                    wo_number_set = False
                    for row in cur.fetchall():
                        # Formata os dados para exibição
                        seq, serv, status, papel, cores, tiragem, op, inicio, fim, wo_num = row
                        if not wo_number_set and wo_num:
                            self.title_label.config(text=f"Acompanhamento da WO: {wo_num}")
                            wo_number_set = True

                        values = (
                            seq or '',
                            serv or '',
                            status or '',
                            papel or '-',
                            cores or '-',
                            tiragem or '',
                            op or '-',
                            inicio.strftime('%H:%M') if inicio else '-',
                            fim.strftime('%H:%M') if fim else '-'
                        )
                        self.tree.insert('', 'end', values=values)

            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível carregar os detalhes da WO: {e}", parent=self)
            finally:
                if conn: conn.close()