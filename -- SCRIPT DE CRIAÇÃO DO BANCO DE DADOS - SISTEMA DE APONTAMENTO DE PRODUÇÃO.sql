-- =============================================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS - SISTEMA DE APONTAMENTO DE PRODUÇÃO
-- =============================================================================
-- Este script irá apagar as tabelas existentes (se houverem) e recriar
-- toda a estrutura do banco de dados do zero.

-- Remove as tabelas antigas na ordem inversa de dependência para evitar erros.
DROP TABLE IF EXISTS paradas CASCADE;
DROP TABLE IF EXISTS paradas_setup CASCADE;
DROP TABLE IF EXISTS apontamento CASCADE;
DROP TABLE IF EXISTS apontamento_setup CASCADE;
DROP TABLE IF EXISTS ordem_servicos CASCADE;
DROP TABLE IF EXISTS ordem_producao CASCADE;
DROP TABLE IF EXISTS equipamentos_tipos CASCADE;
DROP TABLE IF EXISTS impressores CASCADE;
DROP TABLE IF EXISTS motivos_parada_tipos CASCADE;
DROP TABLE IF EXISTS motivos_perda_tipos CASCADE; -- Tabela Adicionada
DROP TABLE IF EXISTS turnos_tipos CASCADE;
DROP TABLE IF EXISTS tipos_papel CASCADE;
DROP TABLE IF EXISTS qtde_cores_tipos CASCADE;
DROP TABLE IF EXISTS formatos_tipos CASCADE;
DROP TABLE IF EXISTS gramaturas_tipos CASCADE;
DROP TABLE IF EXISTS fsc_tipos CASCADE;

-- =============================================================================
-- 1. TABELAS DE APOIO (LOOKUP TABLES)
-- Estas tabelas armazenam opções para os menus suspensos da aplicação.
-- =============================================================================

CREATE TABLE equipamentos_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL
);

CREATE TABLE impressores (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE motivos_parada_tipos (
    id SERIAL PRIMARY KEY,
    codigo INTEGER,
    descricao VARCHAR(255) NOT NULL
);

-- NOVA TABELA PARA MOTIVOS DE PERDA
CREATE TABLE motivos_perda_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL
);

CREATE TABLE turnos_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(50) NOT NULL
);

CREATE TABLE tipos_papel (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL
);

CREATE TABLE qtde_cores_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(50) NOT NULL
);

CREATE TABLE formatos_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(50) NOT NULL
);

CREATE TABLE gramaturas_tipos (
    id SERIAL PRIMARY KEY,
    valor INTEGER NOT NULL
);

CREATE TABLE fsc_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL
);

-- =============================================================================
-- 2. TABELAS DO PROCESSO PRINCIPAL
-- Estrutura central que armazena os dados do fluxo de produção.
-- =============================================================================

-- Tabela principal de Ordens de Serviço
CREATE TABLE ordem_producao (
    id SERIAL PRIMARY KEY,
    numero_wo VARCHAR(50) UNIQUE NOT NULL,
    cliente VARCHAR(255),
    data_previsao_entrega DATE,
    tiragem_em_folhas INTEGER,
    equipamento VARCHAR(100),
    qtde_cores VARCHAR(50),
    tipo_papel VARCHAR(100),
    gramatura VARCHAR(50),
    formato VARCHAR(50),
    fsc VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Em Aberto',
    data_cadastro_pcp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para as etapas/serviços de cada Ordem de Serviço
CREATE TABLE ordem_servicos (
    id SERIAL PRIMARY KEY,
    ordem_id INTEGER NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pendente',
    sequencia INTEGER,
    CONSTRAINT fk_ordem
        FOREIGN KEY(ordem_id) 
        REFERENCES ordem_producao(id)
        ON DELETE CASCADE
);

-- Tabela para os apontamentos de SETUP
CREATE TABLE apontamento_setup (
    id SERIAL PRIMARY KEY,
    servico_id INTEGER NOT NULL UNIQUE,
    data_apontamento DATE NOT NULL,
    hora_inicio TIMESTAMP WITHOUT TIME ZONE,
    hora_fim TIMESTAMP WITHOUT TIME ZONE,
    perdas INTEGER,
    malas INTEGER,
    total_lavagens INTEGER,
    numero_inspecao VARCHAR(100),
    CONSTRAINT fk_servico_setup
        FOREIGN KEY(servico_id)
        REFERENCES ordem_servicos(id)
        ON DELETE CASCADE
);

-- Tabela para os apontamentos de PRODUÇÃO (COM NOVAS COLUNAS)
CREATE TABLE apontamento (
    id SERIAL PRIMARY KEY,
    servico_id INTEGER NOT NULL,
    ordem_id INTEGER,
    data DATE NOT NULL,
    horainicio TIME WITHOUT TIME ZONE,
    horafim TIME WITHOUT TIME ZONE,
    impressor VARCHAR(100),
    turno VARCHAR(50),
    wo VARCHAR(50),
    cliente VARCHAR(255),
    equipamento VARCHAR(100),
    qtde_cores VARCHAR(50),
    tipo_papel VARCHAR(100),
    formato VARCHAR(50),
    gramatura VARCHAR(50),
    fsc VARCHAR(100),
    giros_rodados INTEGER,
    quantidadeproduzida INTEGER,
    perdas_producao INTEGER,                      -- NOVA COLUNA
    motivo_perda_id INTEGER,                      -- NOVA COLUNA
    ocorrencias TEXT,
    CONSTRAINT fk_servico_apontamento
        FOREIGN KEY(servico_id)
        REFERENCES ordem_servicos(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_motivo_perda                      -- NOVA RESTRIÇÃO
        FOREIGN KEY(motivo_perda_id)
        REFERENCES motivos_perda_tipos(id)
        ON DELETE SET NULL
);

-- Tabela para as PARADAS ocorridas durante o SETUP
CREATE TABLE paradas_setup (
    id SERIAL PRIMARY KEY,
    setup_id INTEGER NOT NULL,
    motivo_id INTEGER,
    hora_inicio_parada TIME WITHOUT TIME ZONE,
    hora_fim_parada TIME WITHOUT TIME ZONE,
    motivo_extra_detail TEXT,
    CONSTRAINT fk_setup_parada
        FOREIGN KEY(setup_id)
        REFERENCES apontamento_setup(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_motivo_parada_setup
        FOREIGN KEY(motivo_id)
        REFERENCES motivos_parada_tipos(id)
        ON DELETE SET NULL
);

-- Tabela para as PARADAS ocorridas durante a PRODUÇÃO
CREATE TABLE paradas (
    id SERIAL PRIMARY KEY,
    apontamento_id INTEGER NOT NULL,
    motivo_id INTEGER,
    hora_inicio_parada TIME WITHOUT TIME ZONE,
    hora_fim_parada TIME WITHOUT TIME ZONE,
    motivo_extra_detail TEXT,
    CONSTRAINT fk_apontamento_parada
        FOREIGN KEY(apontamento_id)
        REFERENCES apontamento(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_motivo_parada_producao
        FOREIGN KEY(motivo_id)
        REFERENCES motivos_parada_tipos(id)
        ON DELETE SET NULL
);

-- =============================================================================
-- INSERÇÃO DE DADOS INICIAIS (OPCIONAL)
-- Adiciona algumas opções padrão para as tabelas de apoio.
-- =============================================================================

INSERT INTO turnos_tipos (descricao) VALUES ('1º Turno'), ('2º Turno'), ('3º Turno'), ('Turno Comercial');
INSERT INTO motivos_parada_tipos (descricao) VALUES ('Falta de Material'), ('Manutenção Mecânica'), ('Manutenção Elétrica'), ('Limpeza da Máquina'), ('Troca de Ferramenta'), ('Intervalo/Refeição');
INSERT INTO motivos_perda_tipos (descricao) VALUES ('Erro de Impressão'), ('Papel Amassado'), ('Mancha de Tinta'), ('Corte Incorreto'), ('Problema de Acabamento');

-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================