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
    """
    Cria uma nova Ordem de Produção e seus componentes de forma transacional.

    A função insere a ordem de produção principal, os acabamentos associados,
    as máquinas da sequência de produção e os serviços correspondentes.
    Toda a operação é executada dentro de uma transação para garantir a
    consistência dos dados. Em caso de erro, um rollback é executado.

    Parâmetros:
        order_data (dict): Dicionário com os dados da OP.
        machine_list (list): Lista de dicionários com os dados de cada máquina na sequência.
        acabamento_ids (list): Lista de IDs dos acabamentos selecionados.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a operação no banco de dados.
    """
    logging.debug(f"create_production_order called with order_data: {order_data}, machine_list: {machine_list}, acabamento_ids: {acabamento_ids}")
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
    """
    Busca os campos dinâmicos associados a um tipo de equipamento.

    Esta função consulta o banco de dados para obter a lista de campos
    personalizados que devem ser preenchidos para um determinado tipo de
    equipamento, respeitando a ordem de exibição definida.

    Parâmetros:
        equipamento_id (int): O ID do tipo de equipamento.

    Retorna:
        list: Uma lista de dicionários, onde cada dicionário representa um campo
              e contém suas propriedades (nome, label, tipo, etc.).

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    logging.debug(f"get_equipment_fields called for equipamento_id: {equipamento_id}")
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
    """
    Obtém o ID de um campo dinâmico a partir do seu nome.

    Função utilitária para encontrar o ID de um campo na tabela
    `equipamento_campos` usando seu `nome_campo` único.

    Parâmetros:
        field_name (str): O nome do campo a ser buscado.

    Retorna:
        int: O ID do campo, ou None se não for encontrado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    logging.debug(f"get_field_id_by_name called for field_name: {field_name}")
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
    """
    Busca todos os tipos de equipamentos cadastrados.

    Retorna uma lista completa de todos os tipos de equipamentos, ordenados
    pela descrição.

    Parâmetros:
        Nenhum.

    Retorna:
        list: Uma lista de dicionários, cada um representando um tipo de equipamento.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
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
    """
    Cria um novo tipo de equipamento.

    Insere um novo registro na tabela `equipamentos_tipos` e retorna o ID
    do registro recém-criado.

    Parâmetros:
        description (str): A descrição do novo tipo de equipamento.
        tempo_por_folha_ms (int): O tempo médio de processamento por folha em milissegundos.

    Retorna:
        int: O ID do novo tipo de equipamento criado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
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
    """
    Atualiza um tipo de equipamento existente.

    Modifica a descrição e o tempo por folha de um tipo de equipamento
    identificado pelo seu ID.

    Parâmetros:
        id (int): O ID do tipo de equipamento a ser atualizado.
        description (str): A nova descrição para o tipo de equipamento.
        tempo_por_folha_ms (int): O novo tempo médio por folha em milissegundos.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
    """
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
    """
    Deleta um tipo de equipamento.

    Remove um tipo de equipamento do banco de dados com base no seu ID.
    A operação é transacional e será revertida em caso de erro.

    Parâmetros:
        id (int): O ID do tipo de equipamento a ser deletado.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro (ex: violação de chave estrangeira)
                      durante a exclusão no banco de dados.
    """
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
    """
    Busca todos os campos de equipamento cadastrados.

    Retorna uma lista completa de todos os campos dinâmicos disponíveis
    para associação com tipos de equipamentos, ordenados pelo nome do campo.

    Parâmetros:
        Nenhum.

    Retorna:
        list: Uma lista de dicionários, cada um representando um campo de equipamento.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
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
    """
    Cria um novo campo de equipamento.

    Insere um novo registro na tabela `equipamento_campos` e retorna o ID
    do campo recém-criado.

    Parâmetros:
        nome_campo (str): Nome interno do campo (deve ser único).
        label_traducao (str): Rótulo do campo exibido na interface.
        tipo_dado (str): Tipo de dado do campo (ex: 'texto', 'inteiro').
        widget_type (str): Tipo de widget para renderização (ex: 'entry', 'combobox').
        lookup_table (str, opcional): Tabela de consulta para widgets como combobox.

    Retorna:
        int: O ID do novo campo criado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
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
    """
    Atualiza um campo de equipamento existente.

    Modifica as propriedades de um campo de equipamento identificado pelo seu ID.

    Parâmetros:
        id (int): O ID do campo a ser atualizado.
        nome_campo (str): Novo nome interno do campo.
        label_traducao (str): Novo rótulo de exibição.
        tipo_dado (str): Novo tipo de dado.
        widget_type (str): Novo tipo de widget.
        lookup_table (str, opcional): Nova tabela de consulta.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
    """
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
    """
    Deleta um campo de equipamento.

    Remove um campo de equipamento do banco de dados com base no seu ID.

    Parâmetros:
        id (int): O ID do campo de equipamento a ser deletado.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a exclusão no banco de dados.
    """
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
    """
    Busca os campos associados a um tipo de equipamento específico.

    Retorna uma lista de campos que foram explicitamente associados a um
    determinado tipo de equipamento, ordenados pela ordem de exibição definida.

    Parâmetros:
        equipamento_type_id (int): O ID do tipo de equipamento.

    Retorna:
        list: Uma lista de dicionários, cada um representando um campo associado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
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
    """
    Associa um campo a um tipo de equipamento.

    Cria um registro na tabela de associação `equipamentos_tipos_campos` para
    vincular um campo a um tipo de equipamento com uma ordem de exibição.

    Parâmetros:
        equipamento_type_id (int): O ID do tipo de equipamento.
        field_id (int): O ID do campo a ser associado.
        order (int): A ordem de exibição do campo.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
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
    """
    Desassocia um campo de um tipo de equipamento.

    Remove o registro de associação da tabela `equipamentos_tipos_campos`.

    Parâmetros:
        equipamento_type_id (int): O ID do tipo de equipamento.
        field_id (int): O ID do campo a ser desassociado.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a exclusão no banco de dados.
    """
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
def get_all_appointments_for_editing():
    """
    Busca todos os apontamentos com dados detalhados para edição.

    Esta função realiza uma consulta complexa que junta várias tabelas
    (apontamento, ordem_servicos, ordem_producao, etc.) para retornar
    uma visão completa de cada apontamento, facilitando a edição.

    Parâmetros:
        Nenhum.

    Retorna:
        list: Uma lista de dicionários, onde cada dicionário representa um
              apontamento com todos os seus dados relacionados.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
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
                    op.pn_partnumber,
                    op.cliente,
                    os.descricao AS servico,
                    os.status,
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
                    a.motivo_perda_id,
                    op.fsc_id,
                    op.tipo_papel_id,
                    op.gramatura_id,
                    op.formato_id,
                    op.qtde_cores_id,
                    asetup.numero_inspecao
                FROM apontamento a
                JOIN ordem_servicos os ON a.servico_id = os.id
                JOIN ordem_producao op ON os.ordem_id = op.id
                LEFT JOIN impressores i ON a.impressor_id = i.id
                LEFT JOIN apontamento_setup asetup ON a.servico_id = asetup.servico_id
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
    Atualiza um apontamento de produção existente de forma transacional.

    Esta função atualiza dados em múltiplas tabelas (`apontamento`,
    `ordem_producao`, `apontamento_setup`) relacionadas a um único
    apontamento. A operação é atômica.

    Parâmetros:
        appointment_id (int): O ID do apontamento a ser atualizado.
        data (dict): Dicionário contendo os novos dados do apontamento e
                     das tabelas relacionadas.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Update apontamento table
            query_apontamento = """
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
            cur.execute(query_apontamento, data)

            # Update ordem_producao table
            query_ordem_producao = """
                UPDATE ordem_producao
                SET
                    fsc_id = %(fsc_id)s,
                    tipo_papel_id = %(tipo_papel_id)s,
                    gramatura_id = %(gramatura_id)s,
                    qtde_cores_id = %(qtde_cores_id)s,
                    pn_partnumber = %(pn_partnumber)s,
                    cliente = %(cliente)s,
                    formato_id = %(formato_id)s
                WHERE id = (SELECT ordem_id FROM ordem_servicos WHERE id = %(servico_id)s);
            """
            cur.execute(query_ordem_producao, data)

            # Update apontamento_setup table
            query_apontamento_setup = """
                UPDATE apontamento_setup
                SET
                    numero_inspecao = %(numero_inspecao)s
                WHERE servico_id = %(servico_id)s;
            """
            cur.execute(query_apontamento_setup, data)

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
    Deleta um apontamento de produção.

    Remove um registro da tabela `apontamento` com base no seu ID.

    Parâmetros:
        appointment_id (int): O ID do apontamento a ser deletado.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a exclusão no banco de dados.
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
    Finaliza um serviço, alterando seu status para 'Concluído'.

    Atualiza o status de um serviço na tabela `ordem_servicos`, indicando
    que sua execução foi finalizada.

    Parâmetros:
        service_id (int): O ID do serviço a ser finalizado.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
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
    Busca a lista de usuários que o usuário atual pode gerenciar.

    A lógica de permissão é aplicada para determinar quais usuários podem ser
    visualizados e gerenciados pelo usuário logado.
    - 'admin' e 'gerencial' podem ver todos.
    - 'qualidade' pode ver 'qualidade' e 'offset'.
    - Outros perfis não gerenciam usuários.

    Parâmetros:
        current_user_role (str): A permissão do usuário logado.

    Retorna:
        list: Uma lista de dicionários, cada um representando um usuário gerenciável.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
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

def _get_all_from_table(table_name, order_by='id'):
    """
    Função genérica para buscar todos os registros de uma tabela.

    Esta função auxiliar abstrai a lógica de buscar todos os dados de uma
    tabela de lookup (tabelas de tipos, como 'impressores', 'turnos', etc.).

    Parâmetros:
        table_name (str): O nome da tabela a ser consultada.
        order_by (str): O campo pelo qual os resultados devem ser ordenados.

    Retorna:
        list: Uma lista de dicionários, onde cada dicionário representa um registro.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}")
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar dados da tabela {table_name}: {e}")
        raise ServiceError(f"Erro ao buscar dados da tabela {table_name}: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def get_all_impressores():
    """Busca todos os impressores cadastrados, ordenados por nome."""
    return _get_all_from_table('impressores', 'nome')

def get_all_turnos():
    """Busca todos os turnos cadastrados, ordenados por descrição."""
    return _get_all_from_table('turnos_tipos', 'descricao')

def get_all_motivos_perda():
    """Busca todos os motivos de perda cadastrados, ordenados por descrição."""
    return _get_all_from_table('motivos_perda_tipos', 'descricao')

def get_all_motivos_parada():
    """Busca todos os motivos de parada cadastrados, ordenados por descrição."""
    return _get_all_from_table('motivos_parada_tipos', 'descricao')

def get_all_fsc():
    """Busca todos os tipos de FSC cadastrados, ordenados por descrição."""
    return _get_all_from_table('fsc_tipos', 'descricao')

def get_all_tipos_papel():
    """Busca todos os tipos de papel cadastrados, ordenados por descrição."""
    return _get_all_from_table('tipos_papel', 'descricao')

def get_all_gramaturas():
    """Busca todas as gramaturas de papel cadastradas, ordenadas por valor."""
    return _get_all_from_table('gramaturas_tipos', 'valor')

def get_all_qtde_cores():
    """Busca todas as quantidades de cores cadastradas, ordenadas por descrição."""
    return _get_all_from_table('qtde_cores_tipos', 'descricao')

def get_all_formatos():
    """Busca todos os formatos de papel cadastrados, ordenados por descrição."""
    return _get_all_from_table('formatos_tipos', 'descricao')

def get_last_servico_id():
    """
    Busca o ID do último serviço criado.

    Retorna o maior ID da tabela `ordem_servicos`, que corresponde ao último
    serviço inserido.

    Parâmetros:
        Nenhum.

    Retorna:
        int: O ID do último serviço, ou 0 se a tabela estiver vazia.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM ordem_servicos ORDER BY id DESC LIMIT 1")
            result = cur.fetchone()
            return result[0] if result else 0
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar o último ID de serviço: {e}")
        raise ServiceError(f"Erro ao buscar o último ID de serviço: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def get_closed_production_orders():
    """
    Busca todas as Ordens de Produção com status 'Encerrada' e seus detalhes completos.

    Retorna uma lista de dicionários, onde cada dicionário representa uma Ordem de Produção
    encerrada, incluindo seus acabamentos e máquinas associadas com campos dinâmicos.

    Retorna:
        list: Uma lista de dicionários, cada um representando uma OP encerrada.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1. Buscar Ordens de Produção encerradas (onde todos os serviços estão concluídos)
            query_ops = """
                SELECT
                    op.id, op.numero_wo, op.pn_partnumber, op.cliente, op.data_previsao_entrega,
                    op.tipo_papel_id, op.gramatura_id, op.formato_id, op.fsc_id, op.qtde_cores_id
                FROM ordem_producao op
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM ordem_servicos os
                    WHERE os.ordem_id = op.id
                    AND LOWER(os.status) != LOWER('Concluído')
                )
                ORDER BY op.data_previsao_entrega DESC, op.numero_wo DESC;
            """
            cur.execute(query_ops)
            op_columns = [col[0] for col in cur.description]
            closed_orders = [dict(zip(op_columns, row)) for row in cur.fetchall()]

            for order in closed_orders:
                ordem_id = order['id']

                # 2. Buscar Acabamentos associados
                query_acabamentos = """
                    SELECT ac.id, ac.descricao
                    FROM acabamentos_tipos ac
                    JOIN ordem_producao_acabamentos opa ON ac.id = opa.acabamento_id
                    WHERE opa.ordem_id = %s;
                """
                cur.execute(query_acabamentos, (ordem_id,))
                acab_columns = [col[0] for col in cur.description]
                order['acabamentos'] = [dict(zip(acab_columns, row)) for row in cur.fetchall()]

                # 3. Buscar Máquinas associadas e seus campos dinâmicos
                query_maquinas = """
                    SELECT
                        opm.id AS maquina_op_id, opm.equipamento_id, et.descricao AS equipamento_nome,
                        opm.tiragem_em_folhas, opm.giros_previstos, opm.tempo_producao_previsto_ms
                    FROM ordem_producao_maquinas opm
                    JOIN equipamentos_tipos et ON opm.equipamento_id = et.id
                    WHERE opm.ordem_id = %s
                    ORDER BY opm.sequencia_producao;
                """
                cur.execute(query_maquinas, (ordem_id,))
                maq_columns = [col[0] for col in cur.description]
                machines = [dict(zip(maq_columns, row)) for row in cur.fetchall()]

                for machine in machines:
                    maquina_op_id = machine['maquina_op_id']
                    query_dynamic_fields = """
                        SELECT ec.nome_campo, opmv.valor
                        FROM ordem_producao_maquinas_valores opmv
                        JOIN equipamento_campos ec ON opmv.equipamento_campo_id = ec.id
                        WHERE opmv.ordem_producao_maquinas_id = %s;
                    """
                    cur.execute(query_dynamic_fields, (maquina_op_id,))
                    dynamic_fields = {row[0]: row[1] for row in cur.fetchall()}
                    machine['dynamic_fields'] = dynamic_fields
                order['machines'] = machines

            return closed_orders

    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar ordens de produção encerradas: {e}")
        raise ServiceError(f"Erro ao buscar ordens de produção encerradas: {e}")
    finally:
        if conn:
            release_db_connection(conn)


def create_appointment(data):
    """
    Cria um novo apontamento de produção.

    Insere um novo registro na tabela `apontamento` com os dados fornecidos.

    Parâmetros:
        data (dict): Dicionário contendo todos os dados do novo apontamento.

    Retorna:
        int: O ID do novo apontamento criado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                INSERT INTO apontamento (servico_id, data, horainicio, horafim, giros_rodados, quantidadeproduzida, perdas_producao, ocorrencias, impressor_id, turno_id, motivo_perda_id)
                VALUES (%(servico_id)s, %(data)s, %(horainicio)s, %(horafim)s, %(giros_rodados)s, %(quantidadeproduzida)s, %(perdas_producao)s, %(ocorrencias)s, %(impressor_id)s, %(turno_id)s, %(motivo_perda_id)s)
                RETURNING id;
            """
            cur.execute(query, data)
            new_id = cur.fetchone()[0]
            conn.commit()
            logging.debug(f"Apontamento criado com ID: {new_id}")
            return new_id
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao criar apontamento: {e}")
        raise ServiceError(f"Erro ao criar apontamento: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def get_stops_for_appointment(appointment_id):
    """
    Busca todas as paradas associadas a um apontamento de produção.

    Retorna uma lista de todas as paradas registradas para um apontamento
    específico, incluindo a descrição do motivo da parada.

    Parâmetros:
        appointment_id (int): O ID do apontamento.

    Retorna:
        list: Uma lista de dicionários, cada um representando uma parada.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                SELECT ap.id, ap.hora_inicio_parada as horainicio, ap.hora_fim_parada as horafim, mp.descricao AS motivo
                FROM paradas ap
                JOIN motivos_parada_tipos mp ON ap.motivo_id = mp.id
                WHERE ap.apontamento_id = %s
                ORDER BY ap.hora_inicio_parada;
            """
            cur.execute(query, (appointment_id,))
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar paradas do apontamento {appointment_id}: {e}")
        raise ServiceError(f"Erro ao buscar paradas do apontamento {appointment_id}: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def create_stop(data):
    """
    Cria um novo registro de parada de produção.

    Insere uma nova parada na tabela `paradas`, associada a um apontamento.

    Parâmetros:
        data (dict): Dicionário contendo os dados da nova parada (apontamento_id,
                     horainicio, horafim, motivo_parada_id).

    Retorna:
        int: O ID da nova parada criada.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                INSERT INTO paradas (apontamento_id, hora_inicio_parada, hora_fim_parada, motivo_id)
                VALUES (%(apontamento_id)s, %(horainicio)s, %(horafim)s, %(motivo_parada_id)s)
                RETURNING id;
            """
            cur.execute(query, data)
            new_id = cur.fetchone()[0]
            conn.commit()
            logging.debug(f"Parada criada com ID: {new_id}")
            return new_id
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao criar parada: {e}")
        raise ServiceError(f"Erro ao criar parada: {e}")
    finally:
        if conn:
            release_db_connection(conn)


def update_stop(stop_id, data):
    """
    Atualiza uma parada de produção existente.

    Modifica os dados de uma parada (horários, motivo) com base no seu ID.

    Parâmetros:
        stop_id (int): O ID da parada a ser atualizada.
        data (dict): Dicionário com os novos dados da parada.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                UPDATE paradas
                SET hora_inicio_parada = %(horainicio)s, hora_fim_parada = %(horafim)s, motivo_id = %(motivo_parada_id)s
                WHERE id = %(id)s;
            """
            data['id'] = stop_id
            cur.execute(query, data)
            conn.commit()
            logging.debug(f"Parada atualizada com ID: {stop_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao atualizar parada: {e}")
        raise ServiceError(f"Erro ao atualizar parada: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def delete_stop(stop_id):
    """
    Deleta uma parada de produção.

    Remove um registro da tabela `paradas` com base no seu ID.

    Parâmetros:
        stop_id (int): O ID da parada a ser deletada.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a exclusão no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "DELETE FROM paradas WHERE id = %s;"
            cur.execute(query, (stop_id,))
            conn.commit()
            logging.debug(f"Parada deletada com ID: {stop_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao deletar parada: {e}")
        raise ServiceError(f"Erro ao deletar parada: {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- Setup Appointments Services ---
def get_setup_appointment_by_service_id(service_id):
    """
    Busca um apontamento de setup pelo ID do serviço associado.

    Retorna os dados do apontamento de setup vinculado a um serviço específico.

    Parâmetros:
        service_id (int): O ID do serviço.

    Retorna:
        dict: Um dicionário com os dados do apontamento de setup, ou None se
              não for encontrado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "SELECT * FROM apontamento_setup WHERE servico_id = %s;"
            cur.execute(query, (service_id,))
            columns = [col[0] for col in cur.description]
            result = cur.fetchone()
            if result:
                return dict(zip(columns, result))
            return None
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar apontamento de setup: {e}")
        raise ServiceError(f"Erro ao buscar apontamento de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def create_setup_appointment(data):
    """
    Cria um novo apontamento de setup.

    Insere um novo registro na tabela `apontamento_setup`.

    Parâmetros:
        data (dict): Dicionário contendo os dados do novo apontamento de setup.

    Retorna:
        int: O ID do novo apontamento de setup criado.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                INSERT INTO apontamento_setup (servico_id, data_apontamento, hora_inicio, hora_fim, perdas, malas, total_lavagens, numero_inspecao)
                VALUES (%(servico_id)s, %(data_apontamento)s, %(hora_inicio)s, %(hora_fim)s, %(perdas)s, %(malas)s, %(total_lavagens)s, %(numero_inspecao)s)
                RETURNING id;
            """
            cur.execute(query, data)
            new_id = cur.fetchone()[0]
            conn.commit()
            logging.debug(f"Apontamento de setup criado com ID: {new_id}")
            return new_id
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao criar apontamento de setup: {e}")
        raise ServiceError(f"Erro ao criar apontamento de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def update_setup_appointment(setup_id, data):
    """
    Atualiza um apontamento de setup existente.

    Modifica os dados de um apontamento de setup com base no seu ID.

    Parâmetros:
        setup_id (int): O ID do apontamento de setup a ser atualizado.
        data (dict): Dicionário com os novos dados do apontamento de setup.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                UPDATE apontamento_setup
                SET
                    data_apontamento = %(data_apontamento)s,
                    hora_inicio = %(hora_inicio)s,
                    hora_fim = %(hora_fim)s,
                    perdas = %(perdas)s,
                    malas = %(malas)s,
                    total_lavagens = %(total_lavagens)s,
                    numero_inspecao = %(numero_inspecao)s
                WHERE id = %(id)s;
            """
            data['id'] = setup_id
            cur.execute(query, data)
            conn.commit()
            logging.debug(f"Apontamento de setup atualizado com ID: {setup_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao atualizar apontamento de setup: {e}")
        raise ServiceError(f"Erro ao atualizar apontamento de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def delete_setup_appointment(setup_id):
    """
    Deleta um apontamento de setup.

    Remove um registro da tabela `apontamento_setup` com base no seu ID.

    Parâmetros:
        setup_id (int): O ID do apontamento de setup a ser deletado.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a exclusão no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "DELETE FROM apontamento_setup WHERE id = %s;"
            cur.execute(query, (setup_id,))
            conn.commit()
            logging.debug(f"Apontamento de setup deletado com ID: {setup_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao deletar apontamento de setup: {e}")
        raise ServiceError(f"Erro ao deletar apontamento de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)

# --- Setup Stops Services ---
def get_stops_for_setup_appointment(setup_id):
    """
    Busca todas as paradas associadas a um apontamento de setup.

    Retorna uma lista de todas as paradas registradas para um apontamento
    de setup específico, incluindo a descrição do motivo da parada.

    Parâmetros:
        setup_id (int): O ID do apontamento de setup.

    Retorna:
        list: Uma lista de dicionários, cada um representando uma parada de setup.

    Levanta:
        ServiceError: Se ocorrer um erro durante a consulta ao banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                SELECT ps.id, ps.hora_inicio_parada as horainicio, ps.hora_fim_parada as horafim, mpt.descricao AS motivo
                FROM paradas_setup ps
                JOIN motivos_parada_tipos mpt ON ps.motivo_id = mpt.id
                WHERE ps.setup_id = %s
                ORDER BY ps.hora_inicio_parada;
            """
            cur.execute(query, (setup_id,))
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except (Exception, psycopg2.Error) as e:
        logging.error(f"Erro ao buscar paradas do apontamento de setup {setup_id}: {e}")
        raise ServiceError(f"Erro ao buscar paradas do apontamento de setup {setup_id}: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def create_setup_stop(data):
    """
    Cria um novo registro de parada de setup.

    Insere uma nova parada na tabela `paradas_setup`, associada a um
    apontamento de setup.

    Parâmetros:
        data (dict): Dicionário contendo os dados da nova parada (setup_id,
                     horainicio, horafim, motivo_id).

    Retorna:
        int: O ID da nova parada de setup criada.

    Levanta:
        ServiceError: Se ocorrer um erro durante a inserção no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                INSERT INTO paradas_setup (setup_id, hora_inicio_parada, hora_fim_parada, motivo_id)
                VALUES (%(setup_id)s, %(horainicio)s, %(horafim)s, %(motivo_id)s)
                RETURNING id;
            """
            cur.execute(query, data)
            new_id = cur.fetchone()[0]
            conn.commit()
            logging.debug(f"Parada de setup criada com ID: {new_id}")
            return new_id
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao criar parada de setup: {e}")
        raise ServiceError(f"Erro ao criar parada de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def update_setup_stop(stop_id, data):
    """
    Atualiza uma parada de setup existente.

    Modifica os dados de uma parada de setup (horários, motivo) com base no seu ID.

    Parâmetros:
        stop_id (int): O ID da parada de setup a ser atualizada.
        data (dict): Dicionário com os novos dados da parada.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a atualização no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = """
                UPDATE paradas_setup
                SET hora_inicio_parada = %(horainicio)s, hora_fim_parada = %(horafim)s, motivo_id = %(motivo_id)s
                WHERE id = %(id)s;
            """
            data['id'] = stop_id
            cur.execute(query, data)
            conn.commit()
            logging.debug(f"Parada de setup atualizada com ID: {stop_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao atualizar parada de setup: {e}")
        raise ServiceError(f"Erro ao atualizar parada de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def delete_setup_stop(stop_id):
    """
    Deleta uma parada de setup.

    Remove um registro da tabela `paradas_setup` com base no seu ID.

    Parâmetros:
        stop_id (int): O ID da parada de setup a ser deletada.

    Retorna:
        Nenhum.

    Levanta:
        ServiceError: Se ocorrer um erro durante a exclusão no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            query = "DELETE FROM paradas_setup WHERE id = %s;"
            cur.execute(query, (stop_id,))
            conn.commit()
            logging.debug(f"Parada de setup deletada com ID: {stop_id}")
    except (Exception, psycopg2.Error) as e:
        if conn:
            conn.rollback()
        logging.error(f"Erro ao deletar parada de setup: {e}")
        raise ServiceError(f"Erro ao deletar parada de setup: {e}")
    finally:
        if conn:
            release_db_connection(conn)
