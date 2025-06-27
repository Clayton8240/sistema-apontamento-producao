-- =============================================================================
-- SCRIPT DE ATUALIZAÇÃO DO BANCO DE DADOS - SISTEMA DE APONTAMENTO DE PRODUÇÃO
-- =============================================================================
-- Este script irá ADICIONAR novas colunas e tabelas e ATUALIZAR
-- a estrutura existente para incluir as novas funcionalidades de PCP.

-- Garanta que o script seja executado em um ambiente de teste primeiro.
-- Considere fazer um backup do seu banco de dados antes de executar.

-- =============================================================================
-- 1. ALTERAÇÕES NA TABELA 'ordem_producao'
-- =============================================================================

-- Adiciona a coluna para Part Number (PN) se ela não existir
ALTER TABLE ordem_producao ADD COLUMN IF NOT EXISTS pn VARCHAR(100);

-- Renomeia a coluna de tiragem se ela ainda existir com o nome antigo
ALTER TABLE ordem_producao RENAME COLUMN tiragem_em_folhas TO tiragem_para_impressao;


-- =============================================================================
-- 2. ALTERAÇÕES NA TABELA 'qtde_cores_tipos'
-- =============================================================================

-- Adiciona a coluna para os giros se ela não existir
ALTER TABLE qtde_cores_tipos ADD COLUMN IF NOT EXISTS giros INTEGER;

-- Limpa a tabela para inserir os novos valores com os giros corretos
TRUNCATE TABLE qtde_cores_tipos RESTART IDENTITY;

-- Insere os novos dados de cores com os respectivos giros
INSERT INTO qtde_cores_tipos (descricao, giros) VALUES
('5x5', 4),
('5x4', 3),
('5x0', 2),
('4x4', 2),
('4x3', 2),
('4x2', 2),
('4x1', 2),
('4x0', 1),
('3x3', 2),
('3x0', 1),
('2x2', 1),
('2x1', 1),
('2x0', 1),
('1x1', 1),
('1x0', 1),
('0x0', 1);


-- =============================================================================
-- 3. CRIAÇÃO DAS TABELAS DE APOIO PARA 'Acabamento'
-- =============================================================================

-- Tabela para armazenar os tipos de acabamento disponíveis
CREATE TABLE IF NOT EXISTS acabamentos_tipos (
    id SERIAL PRIMARY KEY,
    descricao VARCHAR(150) NOT NULL UNIQUE
);

-- Tabela de ligação (muitos-para-muitos) entre ordens de produção e acabamentos
CREATE TABLE IF NOT EXISTS ordem_producao_acabamentos (
    ordem_id INTEGER NOT NULL,
    acabamento_id INTEGER NOT NULL,
    PRIMARY KEY (ordem_id, acabamento_id),
    CONSTRAINT fk_ordem_acabamento_ordem
        FOREIGN KEY(ordem_id)
        REFERENCES ordem_producao(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ordem_acabamento_acabamento
        FOREIGN KEY(acabamento_id)
        REFERENCES acabamentos_tipos(id)
        ON DELETE RESTRICT
);


-- =============================================================================
-- 4. DADOS INICIAIS (EXEMPLO)
-- =============================================================================

-- Adiciona alguns exemplos de acabamentos (opcional)
INSERT INTO acabamentos_tipos (descricao) VALUES
('REFILE'),
('DOBRA'),

ON CONFLICT (descricao) DO NOTHING;


-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================