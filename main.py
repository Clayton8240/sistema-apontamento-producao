# Ficheiro: sistema-apontamento-producao/main.py

import tkinter as tk

from tkinter import messagebox
import os
import json
import base64
import traceback
import logging

# Configuração do logging para vermos mensagens detalhadas no terminal  
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Importações dos Módulos Principais
from database import close_connection_pool, initialize_connection_pool
from windows.login_window import LoginWindow
from windows.main_menu_window import MenuPrincipalWindow
from windows.pcp_window import PCPWindow
from windows.production_app_window import App
from windows.configure_db_window import ConfigureDBWindow

class AppController:
    """
    Controlador principal da aplicação, responsável por gerenciar as janelas e o fluxo de dados.
    Esta classe não é uma janela tk.Tk, mas sim um orquestrador para as janelas da aplicação.
    """
    def __init__(self):
        """
        Inicializa o controlador da aplicação.

        Este método configura a janela raiz do Tkinter, a torna invisível e carrega as
        configurações do banco de dados. Ele também inicializa as variáveis de estado
        que serão usadas para gerenciar a janela principal e as permissões do usuário.
        """
        logging.debug("AppController: __init__")
        self.root = tk.Tk()  # Cria a instância da janela raiz
        self.root.attributes("-alpha",0) # torna a janela raiz invisível
        self.db_config = self.load_db_config()
        self.main_window = None
        self.user_permission = None # Adicionado para armazenar a permissão

    def load_db_config(self):
        """
        Carrega as configurações do banco de dados a partir do arquivo 'db_config.json'.

        O arquivo de configuração é codificado em base64 para ofuscar os dados de conexão.
        Se o arquivo não existir ou estiver vazio, um dicionário vazio é retornado,
        permitindo que a aplicação inicie e solicite a configuração.

        Retorna:
            dict: Um dicionário com as configurações do banco de dados ou um dicionário vazio em caso de falha.
        """
        logging.debug("AppController: load_db_config")
        config_path = 'db_config.json'
        if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
            logging.warning("Ficheiro 'db_config.json' não encontrado. Use a tela de login para configurar.")
            return {}
        try:
            with open(config_path, 'rb') as f:
                encoded_data = f.read()
                decoded_data = base64.b64decode(encoded_data)
                return json.loads(decoded_data)
        except Exception as e:
            logging.error(f"Não foi possível ler 'db_config.json'. Detalhes: {e}")
            messagebox.showerror("Erro de Configuração", f"Não foi possível ler 'db_config.json'.\n\nDetalhes: {e}")
            return {}

    def run(self):
        """
        Inicia a execução da aplicação.

        Este método é o ponto de entrada principal do fluxo da aplicação. Ele exibe a
        janela de login e inicia o loop de eventos do Tkinter, que mantém a aplicação
        em execução e responsiva às interações do usuário.
        """
        logging.debug("AppController: run")
        self.show_login_window()
        # O mainloop é chamado na janela raiz, que gere toda a aplicação
        self.root.mainloop()

    def show_login_window(self):
        """
        Cria e exibe a janela de login.

        Esta função instancia a janela de login, passando as referências necessárias
        do controlador e as configurações do banco de dados. Também define o comportamento
        de fechamento da janela para garantir que a aplicação seja encerrada corretamente.
        """
        logging.debug("AppController: show_login_window")
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icon.ico')
        logo_path = os.path.join(base_path, 'logo.png')

        login_win = LoginWindow(self.root, self, self.db_config, icon_path, logo_path)
        login_win.protocol("WM_DELETE_WINDOW", self.on_app_close)
        login_win.grab_set()

    def on_login_success(self, db_config, permission):
        """
        Callback executado após um login bem-sucedido.

        Este método é chamado pela janela de login para notificar o controlador sobre
        o sucesso da autenticação. Ele armazena as configurações do banco de dados e a
        permissão do usuário, destrói a janela de login e abre a janela principal
        correspondente ao nível de permissão do usuário.

        Parâmetros:
            db_config (dict): As configurações do banco de dados validadas.
            permission (str): O nível de permissão do usuário ('admin', 'gerencial', 'pcp', etc.).
        """
        logging.debug(f"AppController: on_login_success - permission: {permission}")
        self.db_config = db_config
        self.user_permission = permission # Armazena a permissão
        
        # Destrói a janela de login atual para abrir a próxima
        for widget in self.root.winfo_children():
            if isinstance(widget, LoginWindow):
                widget.destroy()

        try:
            initialize_connection_pool(self.db_config)
            
            if self.user_permission in ['admin', 'gerencial', 'qualidade']:
                self.main_window = MenuPrincipalWindow(self.root, self, self.db_config, self.user_permission)
            elif self.user_permission == 'pcp':
                self.main_window = PCPWindow(self.root, self.db_config)
            elif self.user_permission == 'offset':
                self.main_window = App(self.root, self.db_config)
            else:
                raise ValueError("Permissão de utilizador inválida.")
            
            self.main_window.protocol("WM_DELETE_WINDOW", self.on_app_close)

        except Exception as e:
            messagebox.showerror("Erro de Inicialização", f"Não foi possível iniciar a aplicação principal:\n{e}")
            self.on_app_close()

    def open_configure_db_window(self, parent):
        """
Abre a janela de configuração do banco de dados.

        Esta função é chamada para permitir que o usuário configure a conexão com o
        banco de dados. A janela de configuração é aberta como uma janela modal,
        bloqueando a interação com a janela pai até que seja fechada.

        Parâmetros:
            parent (tk.Toplevel): A janela pai sobre a qual a janela de configuração será exibida.
        """
        config_win = ConfigureDBWindow(parent, self)
        config_win.grab_set()

    def on_app_close(self):
        """
        Encerra a aplicação de forma limpa.

        Este método é chamado quando a janela principal é fechada. Ele garante que o
        pool de conexões com o banco de dados seja fechado antes de destruir a janela
        raiz do Tkinter, prevenindo vazamentos de recursos.
        """
        logging.debug("AppController: on_app_close")
        logging.info("Encerrando a aplicação.")
        close_connection_pool()
        self.root.destroy()




if __name__ == "__main__":
    try:
        app = AppController()
        app.run()
    except Exception:
        logging.critical("Ocorreu um erro fatal.", exc_info=True)
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro inesperado:\n\n{traceback.format_exc()}")
    
    print("Aplicação encerrada.")