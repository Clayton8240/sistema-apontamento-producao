# -*- coding: utf-8 -*-
import psycopg2
import json
import base64
import os
from tkinter import messagebox

CONFIG_FILE = 'db_config.json'

def get_db_config():
    """Lê o arquivo de configuração do banco de dados."""
    if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
        try:
            with open(CONFIG_FILE, 'rb') as f:
                encoded_data = f.read()
                decoded_data = base64.b64decode(encoded_data)
                return json.loads(decoded_data)
        except Exception as e:
            messagebox.showerror("Erro de Configuração", f"Não foi possível ler o arquivo '{CONFIG_FILE}'.\n\nDetalhes: {e}")
            return {}
    return {}

def get_connection_params(config_dict):
    """Retorna os parâmetros de conexão a partir do dicionário de configuração."""
    return {
        'host': config_dict.get('host'),
        'port': config_dict.get('porta'),
        'dbname': config_dict.get('banco'),
        'user': config_dict.get('usuário'),
        'password': config_dict.get('senha')
    }

def get_db_connection():
    """Estabelece e retorna uma nova conexão com o banco de dados."""
    config = get_db_config()
    if not all(config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
        # Evita mostrar o messagebox se a janela principal ainda não existe
        # messagebox.showerror("Configuração Incompleta", "A configuração do banco de dados está incompleta.")
        return None
    try:
        conn_params = get_connection_params(config)
        conn = psycopg2.connect(**conn_params)
        return conn
    except psycopg2.Error as e:
        # Evita mostrar o messagebox se a janela principal ainda não existe
        # messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}")
        return None
