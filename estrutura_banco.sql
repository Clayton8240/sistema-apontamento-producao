--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Criação da SEQUENCE para a sequencia_producao
CREATE SEQUENCE public.ordem_producao_sequencia_producao_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: acabamentos_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.acabamentos_tipos (
    id integer NOT NULL,
    descricao character varying(150) NOT NULL
);


ALTER TABLE public.acabamentos_tipos OWNER TO postgres;

--
-- Name: acabamentos_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.acabamentos_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.acabamentos_tipos_id_seq OWNER TO postgres;

--
-- Name: acabamentos_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.acabamentos_tipos_id_seq OWNED BY public.acabamentos_tipos.id;


--
-- Name: apontamento; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.apontamento (
    id integer NOT NULL,
    servico_id integer NOT NULL,
    data date NOT NULL,
    horainicio time without time zone,
    horafim time without time zone,
    giros_rodados integer,
    quantidadeproduzida integer,
    perdas_producao integer,
    ocorrencias text,
    impressor_id integer,
    turno_id integer,
    motivo_perda_id integer
);


ALTER TABLE public.apontamento OWNER TO postgres;

--
-- Name: apontamento_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.apontamento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.apontamento_id_seq OWNER TO postgres;

--
-- Name: apontamento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.apontamento_id_seq OWNED BY public.apontamento.id;


--
-- Name: apontamento_setup; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.apontamento_setup (
    id integer NOT NULL,
    servico_id integer NOT NULL,
    data_apontamento date NOT NULL,
    hora_inicio timestamp without time zone,
    hora_fim timestamp without time zone,
    perdas integer,
    malas integer,
    total_lavagens integer,
    numero_inspecao character varying(100)
);


ALTER TABLE public.apontamento_setup OWNER TO postgres;

--
-- Name: apontamento_setup_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.apontamento_setup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.apontamento_setup_id_seq OWNER TO postgres;

--
-- Name: apontamento_setup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.apontamento_setup_id_seq OWNED BY public.apontamento_setup.id;


--
-- Name: equipamentos_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipamentos_tipos (
    id integer NOT NULL,
    descricao character varying(100) NOT NULL,
    tempo_por_folha_ms integer DEFAULT 1
);


ALTER TABLE public.equipamentos_tipos OWNER TO postgres;

--
-- Name: COLUMN equipamentos_tipos.tempo_por_folha_ms; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.equipamentos_tipos.tempo_por_folha_ms IS 'Tempo médio de produção por folha, em milissegundos. Usado para calcular o tempo de produção previsto.';


--
-- Name: equipamentos_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipamentos_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipamentos_tipos_id_seq OWNER TO postgres;

--
-- Name: equipamentos_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipamentos_tipos_id_seq OWNED BY public.equipamentos_tipos.id;


--
-- Name: formatos_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.formatos_tipos (
    id integer NOT NULL,
    descricao character varying(50) NOT NULL
);


ALTER TABLE public.formatos_tipos OWNER TO postgres;

--
-- Name: formatos_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.formatos_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.formatos_tipos_id_seq OWNER TO postgres;

--
-- Name: formatos_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.formatos_tipos_id_seq OWNED BY public.formatos_tipos.id;


--
-- Name: fsc_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fsc_tipos (
    id integer NOT NULL,
    descricao character varying(100) NOT NULL
);


ALTER TABLE public.fsc_tipos OWNER TO postgres;

--
-- Name: fsc_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fsc_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fsc_tipos_id_seq OWNER TO postgres;

--
-- Name: fsc_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fsc_tipos_id_seq OWNED BY public.fsc_tipos.id;


--
-- Name: gramaturas_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.gramaturas_tipos (
    id integer NOT NULL,
    valor character varying(50) NOT NULL
);


ALTER TABLE public.gramaturas_tipos OWNER TO postgres;

--
-- Name: gramaturas_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.gramaturas_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gramaturas_tipos_id_seq OWNER TO postgres;

--
-- Name: gramaturas_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.gramaturas_tipos_id_seq OWNED BY public.gramaturas_tipos.id;


--
-- Name: impressores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.impressores (
    id integer NOT NULL,
    nome character varying(100) NOT NULL
);


ALTER TABLE public.impressores OWNER TO postgres;

--
-- Name: impressores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.impressores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.impressores_id_seq OWNER TO postgres;

--
-- Name: impressores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.impressores_id_seq OWNED BY public.impressores.id;


--
-- Name: motivos_parada_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.motivos_parada_tipos (
    id integer NOT NULL,
    codigo integer,
    descricao character varying(255) NOT NULL
);


ALTER TABLE public.motivos_parada_tipos OWNER TO postgres;

--
-- Name: motivos_parada_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.motivos_parada_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.motivos_parada_tipos_id_seq OWNER TO postgres;

--
-- Name: motivos_parada_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.motivos_parada_tipos_id_seq OWNED BY public.motivos_parada_tipos.id;


--
-- Name: motivos_perda_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.motivos_perda_tipos (
    id integer NOT NULL,
    descricao character varying(255) NOT NULL
);


ALTER TABLE public.motivos_perda_tipos OWNER TO postgres;

--
-- Name: motivos_perda_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.motivos_perda_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.motivos_perda_tipos_id_seq OWNER TO postgres;

--
-- Name: motivos_perda_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.motivos_perda_tipos_id_seq OWNED BY public.motivos_perda_tipos.id;


--
-- Name: ordem_producao; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordem_producao (
    id integer NOT NULL,
    numero_wo character varying(50) NOT NULL,
    pn character varying(100),
    pn_partnumber character varying(100),
    cliente character varying(255),
    data_previsao_entrega date,
    acabamento text,
    status character varying(50) DEFAULT 'Em Aberto'::character varying,
    data_cadastro_pcp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    sequencia_producao integer DEFAULT nextval('public.ordem_producao_sequencia_producao_seq'::regclass),
    tipo_papel_id integer,
    gramatura_id integer,
    formato_id integer,
    fsc_id integer
);


ALTER TABLE public.ordem_producao OWNER TO postgres;

--
-- Name: ordem_producao_acabamentos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordem_producao_acabamentos (
    ordem_id integer NOT NULL,
    acabamento_id integer NOT NULL
);


ALTER TABLE public.ordem_producao_acabamentos OWNER TO postgres;

--
-- Name: ordem_producao_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ordem_producao_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ordem_producao_id_seq OWNER TO postgres;

--
-- Name: ordem_producao_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ordem_producao_id_seq OWNED BY public.ordem_producao.id;


--
-- Name: ordem_producao_maquinas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordem_producao_maquinas (
    id integer NOT NULL,
    ordem_id integer NOT NULL,
    equipamento_id integer NOT NULL,
    tiragem_em_folhas integer,
    tempo_producao_previsto_ms bigint,
    sequencia_producao integer
);


ALTER TABLE public.ordem_producao_maquinas OWNER TO postgres;

--
-- Name: TABLE ordem_producao_maquinas; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.ordem_producao_maquinas IS 'Associa uma Ordem de Produção a uma ou mais máquinas, com metas específicas para cada uma.';


--
-- Name: COLUMN ordem_producao_maquinas.tempo_producao_previsto_ms; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.ordem_producao_maquinas.tempo_producao_previsto_ms IS 'Tempo de produção previsto, calculado como 1 milissegundo por folha.';


--
-- Name: ordem_producao_maquinas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ordem_producao_maquinas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ordem_producao_maquinas_id_seq OWNER TO postgres;

--
-- Name: ordem_producao_maquinas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ordem_producao_maquinas_id_seq OWNED BY public.ordem_producao_maquinas.id;


--
-- Name: ordem_servicos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordem_servicos (
    id integer NOT NULL,
    ordem_id integer NOT NULL,
    descricao character varying(255) NOT NULL,
    status character varying(50) DEFAULT 'Pendente'::character varying NOT NULL,
    sequencia integer,
    maquina_id integer
);


ALTER TABLE public.ordem_servicos OWNER TO postgres;

--
-- Name: ordem_servicos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ordem_servicos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ordem_servicos_id_seq OWNER TO postgres;

--
-- Name: ordem_servicos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ordem_servicos_id_seq OWNED BY public.ordem_servicos.id;


--
-- Name: paradas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.paradas (
    id integer NOT NULL,
    apontamento_id integer NOT NULL,
    motivo_id integer,
    hora_inicio_parada time without time zone,
    hora_fim_parada time without time zone,
    motivo_extra_detail text
);


ALTER TABLE public.paradas OWNER TO postgres;

--
-- Name: paradas_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.paradas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.paradas_id_seq OWNER TO postgres;

--
-- Name: paradas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.paradas_id_seq OWNED BY public.paradas.id;


--
-- Name: paradas_setup; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.paradas_setup (
    id integer NOT NULL,
    setup_id integer NOT NULL,
    motivo_id integer,
    hora_inicio_parada time without time zone,
    hora_fim_parada time without time zone,
    motivo_extra_detail text
);


ALTER TABLE public.paradas_setup OWNER TO postgres;

--
-- Name: paradas_setup_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.paradas_setup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.paradas_setup_id_seq OWNER TO postgres;

--
-- Name: paradas_setup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.paradas_setup_id_seq OWNED BY public.paradas_setup.id;


--
-- Name: qtde_cores_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.qtde_cores_tipos (
    id integer NOT NULL,
    descricao character varying(50) NOT NULL,
    giros integer DEFAULT 1
);


ALTER TABLE public.qtde_cores_tipos OWNER TO postgres;

--
-- Name: qtde_cores_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.qtde_cores_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.qtde_cores_tipos_id_seq OWNER TO postgres;

--
-- Name: qtde_cores_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.qtde_cores_tipos_id_seq OWNED BY public.qtde_cores_tipos.id;


--
-- Name: tipos_papel; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipos_papel (
    id integer NOT NULL,
    descricao character varying(100) NOT NULL
);


ALTER TABLE public.tipos_papel OWNER TO postgres;

--
-- Name: tipos_papel_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tipos_papel_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_papel_id_seq OWNER TO postgres;

--
-- Name: tipos_papel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tipos_papel_id_seq OWNED BY public.tipos_papel.id;


--
-- Name: turnos_tipos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.turnos_tipos (
    id integer NOT NULL,
    descricao character varying(50) NOT NULL
);


ALTER TABLE public.turnos_tipos OWNER TO postgres;

--
-- Name: turnos_tipos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.turnos_tipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.turnos_tipos_id_seq OWNER TO postgres;

--
-- Name: turnos_tipos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.turnos_tipos_id_seq OWNED BY public.turnos_tipos.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome_usuario character varying(50) NOT NULL,
    senha_hash character varying(100) NOT NULL,
    permissao character varying(50) NOT NULL,
    ativo boolean DEFAULT true
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: acabamentos_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acabamentos_tipos ALTER COLUMN id SET DEFAULT nextval('public.acabamentos_tipos_id_seq'::regclass);


--
-- Name: apontamento id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento ALTER COLUMN id SET DEFAULT nextval('public.apontamento_id_seq'::regclass);


--
-- Name: apontamento_setup id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento_setup ALTER COLUMN id SET DEFAULT nextval('public.apontamento_setup_id_seq'::regclass);


--
-- Name: equipamentos_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamentos_tipos ALTER COLUMN id SET DEFAULT nextval('public.equipamentos_tipos_id_seq'::regclass);


--
-- Name: formatos_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.formatos_tipos ALTER COLUMN id SET DEFAULT nextval('public.formatos_tipos_id_seq'::regclass);


--
-- Name: fsc_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsc_tipos ALTER COLUMN id SET DEFAULT nextval('public.fsc_tipos_id_seq'::regclass);


--
-- Name: gramaturas_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gramaturas_tipos ALTER COLUMN id SET DEFAULT nextval('public.gramaturas_tipos_id_seq'::regclass);


--
-- Name: impressores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impressores ALTER COLUMN id SET DEFAULT nextval('public.impressores_id_seq'::regclass);


--
-- Name: motivos_parada_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.motivos_parada_tipos ALTER COLUMN id SET DEFAULT nextval('public.motivos_parada_tipos_id_seq'::regclass);


--
-- Name: motivos_perda_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.motivos_perda_tipos ALTER COLUMN id SET DEFAULT nextval('public.motivos_perda_tipos_id_seq'::regclass);


--
-- Name: ordem_producao id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao ALTER COLUMN id SET DEFAULT nextval('public.ordem_producao_id_seq'::regclass);


--
-- Name: ordem_producao_maquinas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas ALTER COLUMN id SET DEFAULT nextval('public.ordem_producao_maquinas_id_seq'::regclass);


--
-- Name: ordem_servicos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_servicos ALTER COLUMN id SET DEFAULT nextval('public.ordem_servicos_id_seq'::regclass);


--
-- Name: paradas id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas ALTER COLUMN id SET DEFAULT nextval('public.paradas_id_seq'::regclass);


--
-- Name: paradas_setup id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas_setup ALTER COLUMN id SET DEFAULT nextval('public.paradas_setup_id_seq'::regclass);


--
-- Name: qtde_cores_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qtde_cores_tipos ALTER COLUMN id SET DEFAULT nextval('public.qtde_cores_tipos_id_seq'::regclass);


--
-- Name: tipos_papel id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_papel ALTER COLUMN id SET DEFAULT nextval('public.tipos_papel_id_seq'::regclass);


--
-- Name: turnos_tipos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turnos_tipos ALTER COLUMN id SET DEFAULT nextval('public.turnos_tipos_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Name: acabamentos_tipos acabamentos_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acabamentos_tipos
    ADD CONSTRAINT acabamentos_tipos_descricao_key UNIQUE (descricao);


--
-- Name: acabamentos_tipos acabamentos_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acabamentos_tipos
    ADD CONSTRAINT acabamentos_tipos_pkey PRIMARY KEY (id);


--
-- Name: apontamento apontamento_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento
    ADD CONSTRAINT apontamento_pkey PRIMARY KEY (id);


--
-- Name: apontamento_setup apontamento_setup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento_setup
    ADD CONSTRAINT apontamento_setup_pkey PRIMARY KEY (id);


--
-- Name: apontamento_setup apontamento_setup_servico_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento_setup
    ADD CONSTRAINT apontamento_setup_servico_id_key UNIQUE (servico_id);


--
-- Name: equipamentos_tipos equipamentos_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamentos_tipos
    ADD CONSTRAINT equipamentos_tipos_descricao_key UNIQUE (descricao);


--
-- Name: equipamentos_tipos equipamentos_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamentos_tipos
    ADD CONSTRAINT equipamentos_tipos_pkey PRIMARY KEY (id);


--
-- Name: formatos_tipos formatos_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.formatos_tipos
    ADD CONSTRAINT formatos_tipos_descricao_key UNIQUE (descricao);


--
-- Name: formatos_tipos formatos_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.formatos_tipos
    ADD CONSTRAINT formatos_tipos_pkey PRIMARY KEY (id);


--
-- Name: fsc_tipos fsc_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsc_tipos
    ADD CONSTRAINT fsc_tipos_descricao_key UNIQUE (descricao);


--
-- Name: fsc_tipos fsc_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fsc_tipos
    ADD CONSTRAINT fsc_tipos_pkey PRIMARY KEY (id);


--
-- Name: gramaturas_tipos gramaturas_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gramaturas_tipos
    ADD CONSTRAINT gramaturas_tipos_pkey PRIMARY KEY (id);


--
-- Name: gramaturas_tipos gramaturas_tipos_valor_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gramaturas_tipos
    ADD CONSTRAINT gramaturas_tipos_valor_key UNIQUE (valor);


--
-- Name: impressores impressores_nome_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impressores
    ADD CONSTRAINT impressores_nome_key UNIQUE (nome);


--
-- Name: impressores impressores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.impressores
    ADD CONSTRAINT impressores_pkey PRIMARY KEY (id);


--
-- Name: motivos_parada_tipos motivos_parada_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.motivos_parada_tipos
    ADD CONSTRAINT motivos_parada_tipos_descricao_key UNIQUE (descricao);


--
-- Name: motivos_parada_tipos motivos_parada_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.motivos_parada_tipos
    ADD CONSTRAINT motivos_parada_tipos_pkey PRIMARY KEY (id);


--
-- Name: motivos_perda_tipos motivos_perda_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.motivos_perda_tipos
    ADD CONSTRAINT motivos_perda_tipos_descricao_key UNIQUE (descricao);


--
-- Name: motivos_perda_tipos motivos_perda_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.motivos_perda_tipos
    ADD CONSTRAINT motivos_perda_tipos_pkey PRIMARY KEY (id);


--
-- Name: ordem_producao_acabamentos ordem_producao_acabamentos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_acabamentos
    ADD CONSTRAINT ordem_producao_acabamentos_pkey PRIMARY KEY (ordem_id, acabamento_id);


--
-- Name: ordem_producao_maquinas ordem_producao_maquinas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas
    ADD CONSTRAINT ordem_producao_maquinas_pkey PRIMARY KEY (id);


--
-- Name: ordem_producao ordem_producao_numero_wo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao
    ADD CONSTRAINT ordem_producao_numero_wo_key UNIQUE (numero_wo);


--
-- Name: ordem_producao ordem_producao_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao
    ADD CONSTRAINT ordem_producao_pkey PRIMARY KEY (id);


--
-- Name: ordem_servicos ordem_servicos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_servicos
    ADD CONSTRAINT ordem_servicos_pkey PRIMARY KEY (id);


--
-- Name: paradas paradas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas
    ADD CONSTRAINT paradas_pkey PRIMARY KEY (id);


--
-- Name: paradas_setup paradas_setup_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas_setup
    ADD CONSTRAINT paradas_setup_pkey PRIMARY KEY (id);


--
-- Name: qtde_cores_tipos qtde_cores_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qtde_cores_tipos
    ADD CONSTRAINT qtde_cores_tipos_descricao_key UNIQUE (descricao);


--
-- Name: qtde_cores_tipos qtde_cores_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.qtde_cores_tipos
    ADD CONSTRAINT qtde_cores_tipos_pkey PRIMARY KEY (id);


--
-- Name: tipos_papel tipos_papel_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_papel
    ADD CONSTRAINT tipos_papel_descricao_key UNIQUE (descricao);


--
-- Name: tipos_papel tipos_papel_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipos_papel
    ADD CONSTRAINT tipos_papel_pkey PRIMARY KEY (id);


--
-- Name: turnos_tipos turnos_tipos_descricao_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turnos_tipos
    ADD CONSTRAINT turnos_tipos_descricao_key UNIQUE (descricao);


--
-- Name: turnos_tipos turnos_tipos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.turnos_tipos
    ADD CONSTRAINT turnos_tipos_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_nome_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_nome_usuario_key UNIQUE (nome_usuario);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: paradas fk_apontamento_parada; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas
    ADD CONSTRAINT fk_apontamento_parada FOREIGN KEY (apontamento_id) REFERENCES public.apontamento(id) ON DELETE CASCADE;


--
-- Name: apontamento fk_impressor; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento
    ADD CONSTRAINT fk_impressor FOREIGN KEY (impressor_id) REFERENCES public.impressores(id) ON DELETE SET NULL;


--
-- Name: paradas fk_motivo_parada_producao; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas
    ADD CONSTRAINT fk_motivo_parada_producao FOREIGN KEY (motivo_id) REFERENCES public.motivos_parada_tipos(id) ON DELETE SET NULL;


--
-- Name: paradas_setup fk_motivo_parada_setup; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas_setup
    ADD CONSTRAINT fk_motivo_parada_setup FOREIGN KEY (motivo_id) REFERENCES public.motivos_parada_tipos(id) ON DELETE SET NULL;


--
-- Name: apontamento fk_motivo_perda; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento
    ADD CONSTRAINT fk_motivo_perda FOREIGN KEY (motivo_perda_id) REFERENCES public.motivos_perda_tipos(id) ON DELETE SET NULL;


--
-- Name: ordem_producao_maquinas fk_opm_equipamento; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas
    ADD CONSTRAINT fk_opm_equipamento FOREIGN KEY (equipamento_id) REFERENCES public.equipamentos_tipos(id) ON DELETE RESTRICT;


--
-- Name: ordem_producao_maquinas fk_opm_ordem; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas
    ADD CONSTRAINT fk_opm_ordem FOREIGN KEY (ordem_id) REFERENCES public.ordem_producao(id) ON DELETE CASCADE;


--
-- Name: ordem_servicos fk_ordem; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_servicos
    ADD CONSTRAINT fk_ordem FOREIGN KEY (ordem_id) REFERENCES public.ordem_producao(id) ON DELETE CASCADE;


--
-- Name: ordem_producao_acabamentos fk_ordem_acabamento_acabamento; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_acabamentos
    ADD CONSTRAINT fk_ordem_acabamento_acabamento FOREIGN KEY (acabamento_id) REFERENCES public.acabamentos_tipos(id) ON DELETE RESTRICT;


--
-- Name: ordem_producao_acabamentos fk_ordem_acabamento_ordem; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_acabamentos
    ADD CONSTRAINT fk_ordem_acabamento_ordem FOREIGN KEY (ordem_id) REFERENCES public.ordem_producao(id) ON DELETE CASCADE;


--
-- Name: apontamento fk_servico_apontamento; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento
    ADD CONSTRAINT fk_servico_apontamento FOREIGN KEY (servico_id) REFERENCES public.ordem_servicos(id) ON DELETE CASCADE;


--
-- Name: ordem_servicos fk_servico_maquina; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_servicos
    ADD CONSTRAINT fk_servico_maquina FOREIGN KEY (maquina_id) REFERENCES public.ordem_producao_maquinas(id) ON DELETE SET NULL;


--
-- Name: apontamento_setup fk_servico_setup; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento_setup
    ADD CONSTRAINT fk_servico_setup FOREIGN KEY (servico_id) REFERENCES public.ordem_servicos(id) ON DELETE CASCADE;


--
-- Name: paradas_setup fk_setup_parada; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.paradas_setup
    ADD CONSTRAINT fk_setup_parada FOREIGN KEY (setup_id) REFERENCES public.apontamento_setup(id) ON DELETE CASCADE;


--
-- Name: apontamento fk_turno; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.apontamento
    ADD CONSTRAINT fk_turno FOREIGN KEY (turno_id) REFERENCES public.turnos_tipos(id) ON DELETE SET NULL;


--
-- Name: equipamento_campos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipamento_campos (
    id integer NOT NULL,
    nome_campo character varying(100) NOT NULL,
    label_traducao character varying(100) NOT NULL,
    tipo_dado character varying(50) NOT NULL,
    widget_type character varying(50),
    lookup_table character varying(100)
);


ALTER TABLE public.equipamento_campos OWNER TO postgres;

--
-- Name: equipamento_campos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipamento_campos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipamento_campos_id_seq OWNER TO postgres;

--
-- Name: equipamento_campos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipamento_campos_id_seq OWNED BY public.equipamento_campos.id;


--
-- Name: equipamentos_tipos_campos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipamentos_tipos_campos (
    equipamento_tipo_id integer NOT NULL,
    equipamento_campo_id integer NOT NULL,
    ordem_exibicao integer
);


ALTER TABLE public.equipamentos_tipos_campos OWNER TO postgres;

--
-- Name: ordem_producao_maquinas_valores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ordem_producao_maquinas_valores (
    id integer NOT NULL,
    ordem_producao_maquinas_id integer NOT NULL,
    equipamento_campo_id integer NOT NULL,
    valor text
);


ALTER TABLE public.ordem_producao_maquinas_valores OWNER TO postgres;

--
-- Name: ordem_producao_maquinas_valores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ordem_producao_maquinas_valores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ordem_producao_maquinas_valores_id_seq OWNER TO postgres;
--
-- Name: ordem_producao_maquinas_valores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ordem_producao_maquinas_valores_id_seq OWNED BY public.ordem_producao_maquinas_valores.id;


--
-- Name: equipamento_campos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamento_campos ALTER COLUMN id SET DEFAULT nextval('public.equipamento_campos_id_seq'::regclass);


--
-- Name: ordem_producao_maquinas_valores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas_valores ALTER COLUMN id SET DEFAULT nextval('public.ordem_producao_maquinas_valores_id_seq'::regclass);


--
-- Name: equipamento_campos equipamento_campos_nome_campo_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamento_campos
    ADD CONSTRAINT equipamento_campos_nome_campo_key UNIQUE (nome_campo);


--
-- Name: equipamento_campos equipamento_campos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamento_campos
    ADD CONSTRAINT equipamento_campos_pkey PRIMARY KEY (id);


--
-- Name: equipamentos_tipos_campos equipamentos_tipos_campos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamentos_tipos_campos
    ADD CONSTRAINT equipamentos_tipos_campos_pkey PRIMARY KEY (equipamento_tipo_id, equipamento_campo_id);


--
-- Name: ordem_producao_maquinas_valores ordem_producao_maquinas_valores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas_valores
    ADD CONSTRAINT ordem_producao_maquinas_valores_pkey PRIMARY KEY (id);


--
-- Name: ordem_producao fk_op_formato; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao
    ADD CONSTRAINT fk_op_formato FOREIGN KEY (formato_id) REFERENCES public.formatos_tipos(id);


--
-- Name: ordem_producao fk_op_fsc; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao
    ADD CONSTRAINT fk_op_fsc FOREIGN KEY (fsc_id) REFERENCES public.fsc_tipos(id);


--
-- Name: ordem_producao fk_op_gramatura; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao
    ADD CONSTRAINT fk_op_gramatura FOREIGN KEY (gramatura_id) REFERENCES public.gramaturas_tipos(id);


--
-- Name: ordem_producao fk_op_tipo_papel; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao
    ADD CONSTRAINT fk_op_tipo_papel FOREIGN KEY (tipo_papel_id) REFERENCES public.tipos_papel(id);


--
-- Name: equipamentos_tipos_campos fk_etc_campo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamentos_tipos_campos
    ADD CONSTRAINT fk_etc_campo FOREIGN KEY (equipamento_campo_id) REFERENCES public.equipamento_campos(id) ON DELETE CASCADE;


--
-- Name: equipamentos_tipos_campos fk_etc_equipamento_tipo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipamentos_tipos_campos
    ADD CONSTRAINT fk_etc_equipamento_tipo FOREIGN KEY (equipamento_tipo_id) REFERENCES public.equipamentos_tipos(id) ON DELETE CASCADE;


--
-- Name: ordem_producao_maquinas_valores fk_opmv_campo; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas_valores
    ADD CONSTRAINT fk_opmv_campo FOREIGN KEY (equipamento_campo_id) REFERENCES public.equipamento_campos(id) ON DELETE CASCADE;


--
-- Name: ordem_producao_maquinas_valores fk_opmv_opm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ordem_producao_maquinas_valores
    ADD CONSTRAINT fk_opmv_opm FOREIGN KEY (ordem_producao_maquinas_id) REFERENCES public.ordem_producao_maquinas(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--