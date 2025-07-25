# -*- coding: utf-8 -*-

"""
Este módulo gerencia a conexão com o banco de dados.
"""

import psycopg2

def get_connection_params(config_dict):
    """
    Extrai e traduz os parâmetros de conexão de um dicionário de configuração
    para o formato esperado pelo psycopg2 (inglês).
    """
    # Mapeia as chaves em português (usadas no config) para as chaves em inglês (usadas pelo psycopg2)
    key_map = {
        'host': 'host',
        'porta': 'port',
        'banco': 'dbname',
        'usuário': 'user',
        'senha': 'password'
    }
    
    params = {}
    for pt_key, en_key in key_map.items():
        if pt_key in config_dict:
            params[en_key] = config_dict[pt_key]
            
    return params

def get_db_connection(config):
    """
    Estabelece e retorna uma conexão com o banco de dados.
    Retorna None se a conexão falhar ou a configuração estiver incompleta.
    """
    required_keys = ['host', 'porta', 'banco', 'usuário', 'senha']
    if not all(config.get(k) for k in required_keys):
        print("Erro: Configuração do banco de dados incompleta ou ausente.")
        return None
    try:
        conn_params = get_connection_params(config)
        conn = psycopg2.connect(**conn_params)
        return conn
    except psycopg2.Error as e:
        # Retorna o erro para a interface do usuário poder exibi-lo.
        raise e