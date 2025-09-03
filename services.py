# -*- coding: utf-8 -*-
"""
Módulo de Serviços

Esta camada de serviço abstrai a lógica de negócio e as interações complexas
com o banco de dados, desacoplando a UI da lógica de dados.
Todas as funções aqui devem garantir a atomicidade das operações através de transações.
"""

from datetime import datetime
import psycopg2
from database import get_db_connection, release_db_connection
import logging

# Configuração do logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ServiceError(Exception):
    """Exceção base para erros na camada de serviço."""
    pass

def create_production_order(order_data, machine_list, acabamento_ids):
    logging.debug(f"create_production_order called with order_data: {order_data}, machine_list: {machine_list}, acabamento_ids: {acabamento_ids}")
    """
    Cria uma nova Ordem de Produção e todos os seus componentes (máquinas, serviços, acabamentos)
    de forma transacional.

    Args:
        order_data (dict): Dicionário com os dados da OP (numero_wo, cliente, data_previsao_entrega, tipo_papel_id, gramatura_id, formato_id, fsc_id, qtde_cores_id).
        machine_list (list): Lista de dicionários, onde cada dicionário representa os dados de uma máquina.
                             Ex: [{"equipamento_id": 1, "tiragem": 1000, "tempo_previsto_ms": 1000, "giros_previstos": 500, "dynamic_fields": {"giros_previstos": 500, "qtde_cores_id": 1}}]
        acabamento_ids (list): Lista de IDs dos acabamentos selecionados.

    Raises:
        ServiceError: Se ocorrer um erro durante a operação no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1. Inserir a Ordem de Produção principal
            query_op = """
                INSERT INTO ordem_producao (numero_wo, pn_partnumber, cliente, data_previsao_entrega, status, tipo_papel_id, gramatura_id, formato_id, fsc_id, qtde_cores_id)
                VALUES (%(numero_wo)s, %(pn_partnumber)s, %(cliente)s, %(data_previsao_entrega)s, 'Em Aberto', %(tipo_papel_id)s, %(gramatura_id)s, %(formato_id)s, %(fsc_id)s, %(qtde_cores_id)s) RETURNING id;
            """
            cur.execute(query_op, order_data)
            ordem_id = cur.fetchone()[0]
            logging.debug(f"Ordem de produção criada com ID: {ordem_id}")

            # 2. Inserir os acabamentos associados
            if acabamento_ids:
                args_str = ','.join(cur.mogrify("(%s, %s)", (ordem_id, acab_id)).decode('utf-8') for acab_id in acabamento_ids)
                cur.execute("INSERT INTO ordem_producao_acabamentos (ordem_id, acabamento_id) VALUES " + args_str)
                logging.debug(f"Acabamentos inseridos para a ordem ID: {ordem_id}")

            # 3. Inserir as máquinas e os serviços correspondentes
            sequencia_servico = 1
            for machine_data in machine_list:
                # Inserir máquina
                query_maquina = """
                    INSERT INTO ordem_producao_maquinas (
                        ordem_id, equipamento_id, tiragem_em_folhas, 
                        tempo_producao_previsto_ms, sequencia_producao, giros_previstos
                    ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                """
                cur.execute(query_maquina, (
                    ordem_id, machine_data['equipamento_id'], int(machine_data['tiragem']), 
                    int(machine_data['tempo_previsto_ms']), sequencia_servico, machine_data['giros_previstos']
                ))
                maquina_id = cur.fetchone()[0]
                logging.debug(f"Máquina inserida para a ordem ID: {ordem_id} com ID: {maquina_id}")

                # Inserir valores dos campos dinâmicos
                for field_name, field_value in machine_data.get('dynamic_fields', {}).items():
                    # Get field_id from field_name
                    field_id = get_field_id_by_name(field_name)
                    if field_id:
                        query_dynamic_value = """
                            INSERT INTO ordem_producao_maquinas_valores (ordem_producao_maquinas_id, equipamento_campo_id, valor)
                            VALUES (%s, %s, %s);
                        """
                        cur.execute(query_dynamic_value, (maquina_id, field_id, str(field_value)))
                        logging.debug(f"Valor dinâmico inserido para a máquina ID: {maquina_id}, campo ID: {field_id}")

                # Inserir serviço
                query_servico = """
                    INSERT INTO ordem_servicos (ordem_id, maquina_id, descricao, status, sequencia)
                    VALUES (%s, %s, %s, 'Pendente', %s);
                """
                cur.execute(query_servico, (ordem_id, maquina_id, machine_data['equipamento_nome'], sequencia_servico))
                logging.debug(f"Serviço inserido para a ordem ID: {ordem_id}")
                
                sequencia_servico += 1
        
        conn.commit()
        logging.debug("Transação commitada.")

    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao criar ordem de produção: {e}")
        raise ServiceError(f"Não foi possível salvar a ordem: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def get_equipment_fields(equipamento_id):
    logging.debug(f"get_equipment_fields called for equipamento_id: {equipamento_id}")
    """
    Retorna os campos dinâmicos associados a um tipo de equipamento.

    Args:
        equipamento_id (int): O ID do tipo de equipamento.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um campo,
              contendo 'nome_campo', 'label_traducao', 'tipo_dado', 'widget_type', 'lookup_table'.
    Raises:
        ServiceError: Se ocorrer um erro durante a operação no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                SELECT
                    ec.nome_campo,
                    ec.label_traducao,
                    ec.tipo_dado,
                    ec.widget_type,
                    ec.lookup_table
                FROM
                    equipamento_campos ec
                JOIN
                    equipamentos_tipos_campos etc ON ec.id = etc.equipamento_campo_id
                WHERE
                    etc.equipamento_tipo_id = %s
                ORDER BY
                    etc.ordem_exibicao;
            """
            cur.execute(query, (equipamento_id,))
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar campos do equipamento: {e}")
        raise ServiceError(f"Erro ao buscar campos do equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def get_field_id_by_name(field_name):
    logging.debug(f"get_field_id_by_name called for field_name: {field_name}")
    """
    Retorna o ID de um campo dinâmico dado o seu nome.

    Args:
        field_name (str): O nome do campo (nome_campo na tabela equipamento_campos).

    Returns:
        int: O ID do campo, ou None se não encontrado.
    Raises:
        ServiceError: Se ocorrer um erro durante a operação no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "SELECT id FROM equipamento_campos WHERE nome_campo = %s;"
            cur.execute(query, (field_name,))
            result = cur.fetchone()
            return result[0] if result else None
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar ID do campo '{field_name}': {e}")
        raise ServiceError(f"Erro ao buscar ID do campo '{field_name}': {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- Equipment Types Services ---
def get_all_equipment_types():
    logging.debug("get_all_equipment_types called")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, descricao, tempo_por_folha_ms FROM equipamentos_tipos ORDER BY descricao")
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar todos os tipos de equipamento: {e}")
        raise ServiceError(f"Erro ao buscar todos os tipos de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def create_equipment_type(description, tempo_por_folha_ms):
    logging.debug(f"create_equipment_type called with description: {description}, tempo_por_folha_ms: {tempo_por_folha_ms}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO equipamentos_tipos (descricao, tempo_por_folha_ms) VALUES (%s, %s) RETURNING id",
                        (description, tempo_por_folha_ms))
            new_id = cur.fetchone()[0]
            conn.commit()
            logging.debug(f"Tipo de equipamento criado com ID: {new_id}")
            return new_id
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao criar tipo de equipamento: {e}")
        raise ServiceError(f"Erro ao criar tipo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def update_equipment_type(id, description, tempo_por_folha_ms):
    logging.debug(f"update_equipment_type called with id: {id}, description: {description}, tempo_por_folha_ms: {tempo_por_folha_ms}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE equipamentos_tipos SET descricao = %s, tempo_por_folha_ms = %s WHERE id = %s",
                        (description, tempo_por_folha_ms, id))
            conn.commit()
            logging.debug(f"Tipo de equipamento atualizado com ID: {id}")
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao atualizar tipo de equipamento: {e}")
        raise ServiceError(f"Erro ao atualizar tipo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def delete_equipment_type(id):
    logging.debug(f"delete_equipment_type called with id: {id}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM equipamentos_tipos WHERE id = %s", (id,))
            conn.commit()
            logging.debug(f"Tipo de equipamento deletado com ID: {id}")
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao deletar tipo de equipamento: {e}")
        raise ServiceError(f"Erro ao deletar tipo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- Equipment Fields Services ---
def get_all_equipment_fields():
    logging.debug("get_all_equipment_fields called")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome_campo, label_traducao, tipo_dado, widget_type, lookup_table FROM equipamento_campos ORDER BY nome_campo")
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar todos os campos de equipamento: {e}")
        raise ServiceError(f"Erro ao buscar todos os campos de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def create_equipment_field(nome_campo, label_traducao, tipo_dado, widget_type, lookup_table):
    logging.debug(f"create_equipment_field called with nome_campo: {nome_campo}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO equipamento_campos (nome_campo, label_traducao, tipo_dado, widget_type, lookup_table) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                        (nome_campo, label_traducao, tipo_dado, widget_type, lookup_table))
            new_id = cur.fetchone()[0]
            conn.commit()
            logging.debug(f"Campo de equipamento criado com ID: {new_id}")
            return new_id
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao criar campo de equipamento: {e}")
        raise ServiceError(f"Erro ao criar campo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def update_equipment_field(id, nome_campo, label_traducao, tipo_dado, widget_type, lookup_table):
    logging.debug(f"update_equipment_field called with id: {id}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE equipamento_campos SET nome_campo = %s, label_traducao = %s, tipo_dado = %s, widget_type = %s, lookup_table = %s WHERE id = %s",
                        (nome_campo, label_traducao, tipo_dado, widget_type, lookup_table, id))
            conn.commit()
            logging.debug(f"Campo de equipamento atualizado com ID: {id}")
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao atualizar campo de equipamento: {e}")
        raise ServiceError(f"Erro ao atualizar campo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def delete_equipment_field(id):
    logging.debug(f"delete_equipment_field called with id: {id}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM equipamento_campos WHERE id = %s", (id,))
            conn.commit()
            logging.debug(f"Campo de equipamento deletado com ID: {id}")
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao deletar campo de equipamento: {e}")
        raise ServiceError(f"Erro ao deletar campo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- Equipment Type Field Association Services ---
def get_equipment_type_fields(equipamento_type_id):
    logging.debug(f"get_equipment_type_fields called with equipamento_type_id: {equipamento_type_id}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                SELECT ec.id, ec.nome_campo, ec.label_traducao, ec.tipo_dado, ec.widget_type, ec.lookup_table
                FROM equipamento_campos ec
                JOIN equipamentos_tipos_campos etc ON ec.id = etc.equipamento_campo_id
                WHERE etc.equipamento_tipo_id = %s
                ORDER BY etc.ordem_exibicao
            """
            cur.execute(query, (equipamento_type_id,))
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar campos atribuídos ao tipo de equipamento: {e}")
        raise ServiceError(f"Erro ao buscar campos atribuídos ao tipo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def add_equipment_type_field(equipamento_type_id, field_id, order):
    logging.debug(f"add_equipment_type_field called with equipamento_type_id: {equipamento_type_id}, field_id: {field_id}, order: {order}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO equipamentos_tipos_campos (equipamento_tipo_id, equipamento_campo_id, ordem_exibicao) VALUES (%s, %s, %s)",
                        (equipamento_type_id, field_id, order))
            conn.commit()
            logging.debug("Campo atribuído ao tipo de equipamento com sucesso.")
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao atribuir campo ao tipo de equipamento: {e}")
        raise ServiceError(f"Erro ao atribuir campo ao tipo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def remove_equipment_type_field(equipamento_type_id, field_id):
    logging.debug(f"remove_equipment_type_field called with equipamento_type_id: {equipamento_type_id}, field_id: {field_id}")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM equipamentos_tipos_campos WHERE equipamento_tipo_id = %s AND equipamento_campo_id = %s",
                        (equipamento_type_id, field_id))
            conn.commit()
            logging.debug("Campo desatribuído do tipo de equipamento com sucesso.")
    except (Exception, psycopg2.Error) as e:
        if conn: conn.rollback()
        logging.error(f"Erro ao desatribuir campo do tipo de equipamento: {e}")
        raise ServiceError(f"Erro ao desatribuir campo do tipo de equipamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- Appointments Services ---
def get_appointments_for_editing():
    """
    Busca todos os apontamentos com detalhes para edição.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                SELECT
                    a.id,
                    a.servico_id,
                    op.numero_wo,
                    os.descricao AS servico,
                    i.nome AS operador,
                    a.data,
                    a.horainicio,
                    a.horafim,
                    a.giros_rodados,
                    a.quantidadeproduzida,
                    a.perdas_producao,
                    a.ocorrencias,
                    a.impressor_id,
                    a.turno_id,
                    a.motivo_perda_id
                FROM apontamento a
                JOIN ordem_servicos os ON a.servico_id = os.id
                JOIN ordem_producao op ON os.ordem_id = op.id
                LEFT JOIN impressores i ON a.impressor_id = i.id
                ORDER BY a.data DESC, a.horainicio DESC;
            """
            cur.execute(query)
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar apontamentos para edição: {e}")
        raise ServiceError(f"Erro ao buscar apontamentos para edição: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def update_appointment(appointment_id, data):
    """
    Atualiza um apontamento existente.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                UPDATE apontamento
                SET
                    data = %(data)s,
                    horainicio = %(horainicio)s,
                    horafim = %(horafim)s,
                    giros_rodados = %(giros_rodados)s,
                    quantidadeproduzida = %(quantidadeproduzida)s,
                    perdas_producao = %(perdas_producao)s,
                    ocorrencias = %(ocorrencias)s,
                    impressor_id = %(impressor_id)s,
                    turno_id = %(turno_id)s,
                    motivo_perda_id = %(motivo_perda_id)s
                WHERE id = %(id)s;
            """
            data['id'] = appointment_id
            cur.execute(query, data)
            conn.commit()
            logging.debug(f"Apontamento atualizado com ID: {appointment_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao atualizar apontamento: {e}")
        raise ServiceError(f"Erro ao atualizar apontamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def delete_appointment(appointment_id):
    """
    Deleta um apontamento.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "DELETE FROM apontamento WHERE id = %s;"
            cur.execute(query, (appointment_id,))
            conn.commit()
            logging.debug(f"Apontamento deletado com ID: {appointment_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao deletar apontamento: {e}")
        raise ServiceError(f"Erro ao deletar apontamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def finish_service(service_id):
    """
    Finaliza um serviço, mudando seu status para 'Concluído'.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "UPDATE ordem_servicos SET status = 'Concluído' WHERE id = %s;"
            cur.execute(query, (service_id,))
            conn.commit()
            logging.debug(f"Serviço finalizado com ID: {service_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao finalizar serviço: {e}")
        raise ServiceError(f"Erro ao finalizar serviço: {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- User Services ---
def get_manageable_users(current_user_role):
    """
    Retorna uma lista de usuários que o usuário atual pode gerenciar.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            if current_user_role in ['admin', 'gerencial']:
                cur.execute("SELECT id, nome_usuario, permissao, ativo FROM usuarios ORDER BY nome_usuario")
            elif current_user_role == 'qualidade':
                cur.execute("SELECT id, nome_usuario, permissao, ativo FROM usuarios WHERE permissao IN ('qualidade', 'offset') ORDER BY nome_usuario")
            else:
                return [] # Outros perfis não gerenciam usuários
            
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar usuários gerenciáveis: {e}")
        raise ServiceError(f"Erro ao buscar usuários gerenciáveis: {e}")
    finally:
        if conn:
            release_db_connection(conn)