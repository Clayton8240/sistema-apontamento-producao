# -*- coding: utf-8 -*-

import os
import json
import bcrypt
import psycopg2
import getpass
import base64

def carregar_config_db():
    """Carrega a configuração do banco de dados do arquivo db_config.json."""
    config_path = 'db_config.json'
    if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
        print("Erro: Arquivo 'db_config.json' não encontrado ou está vazio.")
        print("Por favor, use a aplicação para salvar a configuração primeiro.")
        return None
    try:
        # Abre o arquivo em modo de leitura de bytes ('rb')
        with open(config_path, 'rb') as f:
            encoded_data = f.read()
            # Decodifica de Base64 para JSON
            decoded_data = base64.b64decode(encoded_data)
            return json.loads(decoded_data)
    except Exception as e:
        print(f"Erro ao ler o arquivo de configuração: {e}")
        return None

def obter_conexao(config):
    """Obtém uma conexão com o banco de dados PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=config.get('host'),
            port=config.get('porta'),
            dbname=config.get('banco'),
            user=config.get('usuário'),
            password=config.get('senha')
        )
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def criar_usuarios_padrao():
    """Cria os usuários padrão no banco de dados."""
    db_config = carregar_config_db()
    if not db_config:
        return

    conn = obter_conexao(db_config)
    if not conn:
        return

    # Lista de usuários padrão e suas permissões
    usuarios = [
        {'username': 'admin', 'permission': 'admin'},
        {'username': 'pcp', 'permission': 'pcp'},
        {'username': 'offset', 'permission': 'offset'}
    ]

    try:
        print("--- Criação de Usuários Padrão ---")
        # getpass.getpass esconde a senha enquanto o usuário digita
        senha_padrao_str = getpass.getpass("Digite a senha padrão para todos os usuários: ")
        
        if not senha_padrao_str:
            print("Senha não pode ser vazia. Operação cancelada.")
            return

        # Gera o hash da senha
        senha_bytes = senha_padrao_str.encode('utf-8')
        senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())
        
        with conn.cursor() as cur:
            for usuario in usuarios:
                nome_usuario = usuario['username']
                permissao = usuario['permission']
                
                print(f"Verificando usuário '{nome_usuario}'...")
                
                # O comando ON CONFLICT garante que o script não falhe se o usuário já existir.
                # Ele simplesmente não faz nada (DO NOTHING) nesse caso.
                query = """
                    INSERT INTO usuarios (nome_usuario, senha_hash, permissao)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (nome_usuario) DO NOTHING;
                """
                cur.execute(query, (nome_usuario, senha_hash.decode('utf-8'), permissao))

                if cur.rowcount > 0:
                    print(f" -> Usuário '{nome_usuario}' criado com sucesso.")
                else:
                    print(f" -> Usuário '{nome_usuario}' já existe. Nenhuma alteração foi feita.")
        
        conn.commit()
        print("\nOperação concluída com sucesso!")

    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    criar_usuarios_padrao()