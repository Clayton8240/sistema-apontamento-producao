# Ficheiro: sistema-apontamento-producao/windows/user_manager_window.py

import psycopg2
import bcrypt
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, Toplevel, END, W

from database import get_db_connection, release_db_connection
from services import get_manageable_users, ServiceError # <-- MODIFICADO

class UserManagerWindow(Toplevel):
    """
    Janela para administradores gerenciarem os usuários da aplicação.
    """
    def __init__(self, master, db_config, permission):
        super().__init__(master)
        self.master = master
        self.db_config = db_config
        self.permission = permission # <-- NOVO

        self.title("Gerenciamento de Usuários")
        self.geometry("800x600")
        self.transient(master)
        self.grab_set()

        self.create_widgets()
        self.load_users()

    def get_string(self, key, **kwargs):
        return self.master.get_string(key, **kwargs)

    def create_widgets(self):
        main_frame = tb.Frame(self, padding=15)
        main_frame.pack(fill=BOTH, expand=YES)

        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(0, 10))
        
        tb.Button(btn_frame, text="➕ Adicionar Novo", bootstyle="success-outline", command=self.open_add_edit_dialog).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="✏️ Editar Selecionado", bootstyle="info-outline", command=lambda: self.open_add_edit_dialog(edit_mode=True)).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Ativar/Desativar", bootstyle="warning-outline", command=self.toggle_user_status).pack(side=LEFT, padx=5)
        tb.Button(btn_frame, text="Redefinir Senha", bootstyle="danger-outline", command=self.reset_password).pack(side=LEFT, padx=5)

        tree_frame = tb.LabelFrame(main_frame, text="Usuários Cadastrados", bootstyle=PRIMARY, padding=10)
        tree_frame.pack(fill=BOTH, expand=YES)

        cols = ("id", "nome_usuario", "permissao", "ativo")
        headers = ("ID", "Nome de Usuário", "Permissão", "Status")
        
        self.tree = tb.Treeview(tree_frame, columns=cols, show="headings")
        for col, header in zip(cols, headers):
            self.tree.heading(col, text=header)
            self.tree.column(col, anchor=W)
        
        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("ativo", width=80, anchor=CENTER)
        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)
        
        scrollbar = tb.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

    def load_users(self):
        """Carrega e exibe os usuários permitidos na Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            users = get_manageable_users(self.permission)
            for user in users:
                status = "Ativo" if user['ativo'] else "Inativo"
                values = (user['id'], user['nome_usuario'], user['permissao'], status)
                self.tree.insert("", END, values=values)
        except ServiceError as e:
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao carregar usuários: {e}", parent=self)

    def get_allowed_permissions(self):
        """Retorna a lista de permissões que o usuário atual pode atribuir."""
        if self.permission == 'admin':
            return ['admin', 'gerencial', 'qualidade', 'pcp', 'offset']
        if self.permission == 'gerencial':
            return ['gerencial', 'qualidade', 'pcp', 'offset']
        if self.permission == 'qualidade':
            return ['qualidade', 'offset']
        return []

    def open_add_edit_dialog(self, edit_mode=False):
        """Abre uma janela para adicionar ou editar um usuário."""
        user_id, username, permission = None, "", ""
        if edit_mode:
            selected_item = self.tree.focus()
            if not selected_item:
                messagebox.showwarning("Seleção Necessária", "Por favor, selecione um usuário para editar.", parent=self)
                return
            values = self.tree.item(selected_item, "values")
            user_id, username, permission = values[0], values[1], values[2]

        dialog = Toplevel(self)
        dialog.title("Adicionar Novo Usuário" if not edit_mode else "Editar Usuário")
        dialog.transient(self)
        dialog.grab_set()

        form_frame = tb.Frame(dialog, padding=20)
        form_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(form_frame, text="Nome de Usuário:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        user_entry = tb.Entry(form_frame)
        user_entry.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
        user_entry.insert(0, username)
        if edit_mode:
            user_entry.config(state="readonly")

        tb.Label(form_frame, text="Permissão:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        perm_combo = tb.Combobox(form_frame, values=self.get_allowed_permissions(), state="readonly")
        perm_combo.grid(row=1, column=1, padx=5, pady=5, sticky=EW)
        if permission: perm_combo.set(permission)
        
        pass_entry, confirm_entry = None, None
        if not edit_mode:
            tb.Label(form_frame, text="Senha:").grid(row=2, column=0, padx=5, pady=5, sticky=W)
            pass_entry = tb.Entry(form_frame, show="*")
            pass_entry.grid(row=2, column=1, padx=5, pady=5, sticky=EW)

            tb.Label(form_frame, text="Confirmar Senha:").grid(row=3, column=0, padx=5, pady=5, sticky=W)
            confirm_entry = tb.Entry(form_frame, show="*")
            confirm_entry.grid(row=3, column=1, padx=5, pady=5, sticky=EW)

        button_text = "Salvar Alterações" if edit_mode else "Salvar"
        btn_save = tb.Button(form_frame, text=button_text, bootstyle=SUCCESS,
                             command=lambda: self.save_user(
                                 dialog, user_id, user_entry.get(), perm_combo.get(), 
                                 pass_entry.get() if pass_entry else None, 
                                 confirm_entry.get() if confirm_entry else None
                             ))
        btn_save.grid(row=4, columnspan=2, pady=10)

    def save_user(self, dialog, user_id, username, permission, password, confirm_password):
        """Salva um usuário novo ou edita um existente com validação aprimorada."""
        if not username or not permission:
            messagebox.showwarning("Campos Obrigatórios", "Nome de usuário e permissão são obrigatórios.", parent=dialog)
            return

        conn = get_db_connection()
        if not conn: return
        
        try:
            with conn.cursor() as cur:
                if user_id:  # Modo de Edição
                    cur.execute("UPDATE usuarios SET permissao = %s WHERE id = %s", (permission, user_id))
                    messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!", parent=self)
                else:  # Modo de Criação
                    if not password or not confirm_password:
                        messagebox.showwarning("Campos Obrigatórios", "Senha e confirmação são obrigatórias.", parent=dialog)
                        return
                    if password != confirm_password:
                        messagebox.showerror("Erro", "As senhas não coincidem.", parent=dialog)
                        return
                    if len(password) < 6:
                        messagebox.showerror("Senha Fraca", "A senha deve ter pelo menos 6 caracteres.", parent=dialog)
                        return

                    cur.execute("SELECT id FROM usuarios WHERE nome_usuario = %s", (username,))
                    if cur.fetchone():
                        messagebox.showerror("Erro", f"O nome de usuário '{username}' já está em uso.", parent=dialog)
                        return

                    senha_bytes = password.encode('utf-8')
                    senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
                    
                    cur.execute(
                        "INSERT INTO usuarios (nome_usuario, senha_hash, permissao) VALUES (%s, %s, %s)",
                        (username, senha_hash.decode('utf-8'), permission)
                    )
                    messagebox.showinfo("Sucesso", "Usuário criado com sucesso!", parent=self)
            
            conn.commit()
            dialog.destroy()
            self.load_users()

        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível salvar o usuário: {e}", parent=self)
        finally:
            if conn: release_db_connection(conn)

    def toggle_user_status(self):
        """Ativa ou desativa um usuário selecionado."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Seleção Necessária", "Por favor, selecione um usuário.", parent=self)
            return
            
        values = self.tree.item(selected_item, "values")
        user_id, username, _, status = values
        
        new_status = not (status == "Ativo")
        action_text = "ativar" if new_status else "desativar"

        if not messagebox.askyesno("Confirmar Ação", f"Tem certeza que deseja {action_text} o usuário '{username}'?"):
            return
        
        conn = get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE usuarios SET ativo = %s WHERE id = %s", (new_status, user_id))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Usuário {action_text} com sucesso!", parent=self)
            self.load_users()
        except psycopg2.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Não foi possível alterar o status do usuário: {e}", parent=self)
        finally:
            if conn: release_db_connection(conn)

    def reset_password(self):
        """Abre um diálogo para redefinir a senha de um usuário."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Seleção Necessária", "Por favor, selecione um usuário.", parent=self)
            return
            
        values = self.tree.item(selected_item, "values")
        user_id, username = values[0], values[1]

        dialog = Toplevel(self)
        dialog.title(f"Redefinir Senha para {username}")
        dialog.transient(self)
        dialog.grab_set()

        form_frame = tb.Frame(dialog, padding=20)
        form_frame.pack(fill=BOTH, expand=YES)
        
        tb.Label(form_frame, text="Nova Senha:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        pass_entry = tb.Entry(form_frame, show="*")
        pass_entry.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        tb.Label(form_frame, text="Confirmar Nova Senha:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        confirm_entry = tb.Entry(form_frame, show="*")
        confirm_entry.grid(row=1, column=1, padx=5, pady=5, sticky=EW)

        def do_reset():
            new_pass = pass_entry.get()
            confirm_pass = confirm_entry.get()
            if not new_pass or not confirm_pass:
                messagebox.showwarning("Campos Obrigatórios", "Todos os campos são obrigatórios.", parent=dialog)
                return
            if new_pass != confirm_pass:
                messagebox.showerror("Erro", "As senhas não coincidem.", parent=dialog)
                return
            if len(new_pass) < 6:
                messagebox.showerror("Senha Fraca", "A nova senha deve ter pelo menos 6 caracteres.", parent=dialog)
                return

            senha_bytes = new_pass.encode('utf-8')
            senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
            
            conn = get_db_connection()
            if not conn: return
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE usuarios SET senha_hash = %s WHERE id = %s", (senha_hash.decode('utf-8'), user_id))
                conn.commit()
                messagebox.showinfo("Sucesso", "Senha redefinida com sucesso!", parent=self)
                dialog.destroy()
            except psycopg2.Error as e:
                conn.rollback()
                messagebox.showerror("Erro", f"Não foi possível redefinir a senha: {e}", parent=self)
            finally:
                if conn: release_db_connection(conn)

        tb.Button(form_frame, text="Redefinir Senha", bootstyle=DANGER, command=do_reset).grid(row=2, columnspan=2, pady=10)
