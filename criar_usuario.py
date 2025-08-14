import json
import psycopg2
from psycopg2 import sql
import base64
import bcrypt # Importa a biblioteca bcrypt
import keyring # Importa a biblioteca keyring
import logging

# Configuração do logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def criar_usuario():
    """
    Script para criar um novo usuário no banco de dados com senha hasheada.
    """
    try:
        logging.debug("Iniciando a criação de usuário.")
        # Carrega as configurações do banco de dados
        with open('db_config.json', 'rb') as f: # Abre em modo binário
            encoded_data = f.read()
            decoded_data = base64.b64decode(encoded_data)
            db_config = json.loads(decoded_data)
        logging.debug("Configurações do banco de dados carregadas.")

        # Coleta as informações do novo usuário
        print("--- Criação de Novo Usuário ---")
        nome_usuario = input("Digite o nome de usuário: ")
        senha = input("Digite a senha: ")
        permissao = input("Digite o nível de permissão (ex: admin, pcp, offset): ")

        # Gera um salt e hasheia a senha usando bcrypt
        # O salt é incluído no hash resultante
        hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        senha_hash = hashed_password.decode('utf-8') # Armazena como string UTF-8
        logging.debug("Senha hasheada com sucesso.")

        # Conecta ao banco de dados
        KEYRING_SERVICE_NAME = "sistema-apontamento-producao" # Define o nome do serviço para o keyring
        db_user = db_config.get('usuário')
        db_password = keyring.get_password(KEYRING_SERVICE_NAME, db_user)

        if not db_password:
            raise Exception("Senha do banco de dados não encontrada no keyring. Por favor, configure a conexão no aplicativo principal primeiro.")

        logging.debug("Conectando ao banco de dados...")
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['porta'],
            dbname=db_config['banco'],
            user=db_config['usuário'],
            password=db_password # Usa a senha do keyring
        )
        cur = conn.cursor()
        logging.debug("Conexão com o banco de dados estabelecida.")

        # Verifica se o usuário já existe
        cur.execute("SELECT id FROM public.usuarios WHERE nome_usuario = %s", (nome_usuario,))
        existing_user = cur.fetchone()

        if existing_user:
            # Atualiza o usuário existente
            logging.debug(f"Usuário '{nome_usuario}' já existe. Atualizando...")
            query = sql.SQL("""
                UPDATE public.usuarios
                SET senha_hash = %s, permissao = %s, ativo = TRUE
                WHERE id = %s
            """)
            cur.execute(query, (senha_hash, permissao, existing_user[0]))
            logging.info(f"Usuário '{nome_usuario}' atualizado com sucesso!")
        else:
            # Insere um novo usuário
            logging.debug(f"Criando novo usuário '{nome_usuario}'...")
            query = sql.SQL("""
                INSERT INTO public.usuarios (nome_usuario, senha_hash, permissao, ativo)
                VALUES (%s, %s, %s, %s)
            """)
            cur.execute(query, (nome_usuario, senha_hash, permissao, True))
            logging.info(f"Usuário '{nome_usuario}' criado com sucesso!")

        # Confirma a transação
        conn.commit()
        logging.debug("Transação commitada.")

        # Fecha a conexão
        cur.close()
        conn.close()
        logging.debug("Conexão com o banco de dados fechada.")

    except FileNotFoundError:
        logging.error("Arquivo 'db_config.json' não encontrado. Execute este script do diretório raiz do projeto.")
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar 'db_config.json'. Verifique se o conteúdo está no formato JSON válido após a decodificação base64: {e}")
    except base64.binascii.Error as e:
        logging.error(f"Erro ao decodificar base64 de 'db_config.json'. Verifique se o arquivo está corretamente codificado: {e}")
    except psycopg2.Error as e:
        logging.error(f"Não foi possível criar/atualizar o usuário: {e}")
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    criar_usuario()