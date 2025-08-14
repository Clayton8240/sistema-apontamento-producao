# -*- coding: utf-8 -*-

"""
Este módulo gerencia a conexão com o banco de dados usando um pool de conexões.
"""

import psycopg2
from psycopg2 import pool
import logging

# Configuração do logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Variável global para o pool de conexões
connection_pool = None

def get_connection_params(config_dict):
    logging.debug("get_connection_params called")
    """
    Extrai e traduz os parâmetros de conexão de um dicionário de configuração
    para o formato esperado pelo psycopg2 (inglês).
    """
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

def initialize_connection_pool(config):
    logging.debug("initialize_connection_pool called")
    """
    Inicializa o pool de conexões. Esta função deve ser chamada uma vez,
    idealmente após o login bem-sucedido.
    """
    global connection_pool
    if connection_pool:
        logging.debug("Connection pool already initialized.")
        return # Pool já foi inicializado

    required_keys = ['host', 'porta', 'banco', 'usuário', 'senha']
    if not all(config.get(k) for k in required_keys):
        raise ValueError("Configuração do banco de dados incompleta ou ausente.")
    
    try:
        conn_params = get_connection_params(config)
        logging.debug("Initializing connection pool.")
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10, # Ajuste conforme a necessidade
            **conn_params
        )
        logging.info("Pool de conexões com o banco de dados inicializado com sucesso.")
    except psycopg2.Error as e:
        logging.error(f"Erro ao inicializar o pool de conexões: {e}")
        connection_pool = None
        raise e

def get_db_connection():
    logging.debug("get_db_connection called")
    """
    Obtém uma conexão do pool.
    """
    global connection_pool
    if not connection_pool:
        raise ConnectionError("O pool de conexões não foi inicializado. Chame 'initialize_connection_pool' primeiro.")
    try:
        logging.debug("Getting connection from pool.")
        return connection_pool.getconn()
    except psycopg2.Error as e:
        logging.error(f"Erro ao obter conexão do pool: {e}")
        raise e

def release_db_connection(conn):
    logging.debug("release_db_connection called")
    """
    Devolve uma conexão ao pool.
    """
    global connection_pool
    if connection_pool and conn:
        logging.debug("Putting connection back to pool.")
        connection_pool.putconn(conn)

def close_connection_pool():
    logging.debug("close_connection_pool called")
    """
    Fecha todas as conexões no pool. Deve ser chamada ao encerrar a aplicação.
    """
    global connection_pool
    if connection_pool:
        logging.info("Closing connection pool.")
        connection_pool.closeall()
        connection_pool = None

def test_db_connection(config):
    logging.debug("test_db_connection called")
    """
    Testa uma única conexão sem usar o pool.
    """
    try:
        conn_params = get_connection_params(config)
        conn = psycopg2.connect(**conn_params)
        conn.close()
        logging.info("Conexão com o banco de dados bem-sucedida!")
        return True, "Conexão bem-sucedida!"
    except psycopg2.Error as e:
        logging.error(f"Erro ao testar a conexão com o banco de dados: {e}")
        return False, str(e)