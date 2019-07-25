CREATE DATABASE phones;
CREATE USER lookup WITH password 'h3xwayp4ssw0rd'; --you can change it if you want

GRANT ALL ON DATABASE phones TO lookup;
\c phones


CREATE TABLE public.map (
    id integer NOT NULL,
    hash bytea,
    phone character varying(11)
);

ALTER TABLE public.map OWNER TO lookup;

CREATE SEQUENCE public.map_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
	
ALTER TABLE public.map_id_seq OWNER TO lookup;

ALTER SEQUENCE public.map_id_seq OWNED BY public.map.id;

ALTER TABLE ONLY public.map ALTER COLUMN id SET DEFAULT nextval('public.map_id_seq'::regclass);
ALTER TABLE ONLY public.map ADD CONSTRAINT map_pkey PRIMARY KEY (id);
CREATE INDEX hash_index_btree ON public.map USING btree (hash);
