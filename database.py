# -*- coding: utf-8 -*-

"""
Este módulo gerencia a conexão com o banco de dados.
"""

import psycopg2

def get_connection_params(config_dict):
    """Extrai os parâmetros de conexão de um dicionário de configuração."""
    return {
        'host': config_dict.get('host'),
        'port': config_dict.get('porta'),
        'dbname': config_dict.get('banco'),
        'user': config_dict.get('usuário'),
        'password': config_dict.get('senha')
    }

def get_db_connection(config):
    """
    Estabelece e retorna uma conexão com o banco de dados.
    Retorna None se a conexão falhar ou a configuração estiver incompleta.
    """
    if not all(config.get(k) for k in ['host', 'porta', 'banco', 'usuário', 'senha']):
        print("Erro: Configuração do banco de dados incompleta ou ausente.")
        return None
    try:
        conn = psycopg2.connect(**get_connection_params(config))
        return conn
    except psycopg2.Error as e:
        print(f"Erro de Conexão: Não foi possível conectar ao banco de dados: {e}")
        return None