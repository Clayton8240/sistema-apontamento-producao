-- Inserindo dados na tabela de Motivos de Parada
INSERT INTO public.motivos_parada_tipos (codigo, descricao) VALUES
(1, 'Falta de energia'), (2, 'Problema eletrônico'), (3, 'Problema mecânico'), (4, 'Problema com Ar'),
(5, 'Falta de papel'), (6, 'Falta de chapa'), (7, 'Reunião'), (8, 'Treinamento'), (9, 'Sem trabalho'),
(10, 'Aguardando programação'), (11, 'Limpeza'), (12, 'Lubrificação'), (13, 'Falta de modelo de cores'),
(14, 'Troca de blanqueta'), (15, 'Troca de calço'), (16, 'Problema com geladeira'), (17, 'Auditoria'),
(18, 'Falta de pasta de trabalho'), (19, 'Não chega nas cores'), (20, 'Falta de tinta'),
(21, 'Falta de solventes'), (22, 'Falta de pano'), (23, 'Aguardando aprovação'), (24, 'Problema com arquivo'),
(25, 'Falta equipe'), (26, 'Manutenção interna'), (27, 'Manutenção externa'), (28, 'Outros');

-- Inserindo dados na tabela de Tipos de Papel
INSERT INTO public.tipos_papel (descricao) VALUES
('Reciclato'), ('Offset'), ('Couche Brilho'), ('Couche Fosco'), ('Triplex'), ('Duplex'), ('Ningbo');

-- Inserindo dados na tabela de Impressores
INSERT INTO public.impressores (nome) VALUES
('Samuel'), ('Daniel'), ('Fernando'), ('Edson');

-- Inserindo dados na tabela de Formatos
INSERT INTO public.formatos_tipos (descricao) VALUES
('64x88'), ('64x44'), ('66x96'), ('66x48'), ('32x44'), ('33x48'), ('Outros Digitar');

-- Inserindo dados na tabela de Gramatura do Papel
INSERT INTO public.gramaturas_tipos (valor) VALUES
('56'), ('63'), ('75'), ('90'), ('115'), ('120'), ('250'), ('300'), ('350'), ('400'), ('450');

-- Inserindo dados na tabela de Turnos
INSERT INTO public.turnos_tipos (descricao) VALUES ('1º Turno');

-- Inserindo dados na tabela de Tipos de FSC
INSERT INTO public.fsc_tipos (descricao) VALUES ('Sim'), ('Não');

-- Inserindo dados na tabela de Equipamentos (Máquinas)
INSERT INTO public.equipamentos_tipos (descricao) VALUES ('4 Cores'), ('Reversão');

-- Inserindo dados na tabela de Quantidade de Cores
INSERT INTO public.qtde_cores_tipos (descricao) VALUES
('1x0'), ('1x1'), ('2x0'), ('2x1'), ('2x2'), ('3x0'), ('3x1'), ('3x2'), ('3x3'),
('4x0'), ('4x1'), ('4x2'), ('4x3'), ('4x4'), ('5x0'), ('5x1'), ('5x2'), ('5x3'),
('5x4'), ('5x5'), ('6x0'), ('6x1'), ('6x2'), ('6x3'), ('6x4'), ('6x5'), ('6x6');