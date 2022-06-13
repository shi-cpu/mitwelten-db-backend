BEGIN;

CREATE SCHEMA IF NOT EXISTS dev
    AUTHORIZATION mitwelten_admin;

CREATE TABLE IF NOT EXISTS dev.birdnet_configs
(
    config_id serial,
    config jsonb NOT NULL,
    comment text,
    created_at timestamptz NOT NULL DEFAULT current_timestamp,
    updated_at timestamptz NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (config_id),
    UNIQUE (config)
);

CREATE TABLE IF NOT EXISTS dev.files_audio
(
    file_id serial,
    object_name text NOT NULL,
    sha256 character varying(64) NOT NULL,
    time timestamptz NOT NULL,
    node_id integer NOT NULL,
    location_id integer,
    duration double precision NOT NULL,
    serial_number character varying(32),
    format character varying(64),
    file_size integer NOT NULL,
    sample_rate integer NOT NULL,
    bit_depth smallint,
    channels smallint,
    battery real,
    temperature real,
    gain character varying(32),
    filter character varying(64),
    source character varying(32),
    rec_end_status character varying(32),
    comment character varying(64),
    class character varying(32),
    created_at timestamptz NOT NULL DEFAULT current_timestamp,
    updated_at timestamptz NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (file_id),
    UNIQUE (object_name),
    UNIQUE (sha256)
);

CREATE TABLE IF NOT EXISTS dev.files_image
(
    file_id serial,
    object_name text NOT NULL,
    sha256 character varying(64) NOT NULL,
    time timestamptz NOT NULL,
    node_id integer NOT NULL,
    location_id integer,
    file_size integer NOT NULL,
    resolution integer[] NOT NULL,
    created_at timestamptz NOT NULL DEFAULT current_timestamp,
    updated_at timestamptz NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (file_id),
    UNIQUE (object_name),
    UNIQUE (sha256)
);

CREATE TABLE IF NOT EXISTS dev.birdnet_results
(
    result_id serial,
    task_id integer NOT NULL,
    file_id integer NOT NULL,
    object_name text NOT NULL, -- remove?
    time_start real NOT NULL,
    time_end real NOT NULL,
    confidence real NOT NULL,
    species character varying(255) NOT NULL,
    PRIMARY KEY (result_id)
);

CREATE TABLE IF NOT EXISTS dev.species_occurrence
(
    id serial,
    species character varying(255) NOT NULL,
    occurence integer,
    unlikely boolean,
    comment text,
    created_at timestamptz NOT NULL DEFAULT current_timestamp,
    updated_at timestamptz NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (id),
    UNIQUE (species)
);

CREATE TABLE IF NOT EXISTS dev.birdnet_tasks
(
    task_id serial,
    file_id integer NOT NULL,
    config_id integer NOT NULL,
    state integer NOT NULL,
    scheduled_on timestamptz NOT NULL,
    pickup_on timestamptz,
    end_on timestamptz,
    PRIMARY KEY (task_id),
    CONSTRAINT unique_task_in_batch UNIQUE (file_id, config_id, batch_id)
);

CREATE TABLE IF NOT EXISTS dev.locations
(
    location_id serial,
    location point NOT NULL,
    type character varying(128),
    name character varying(128),
    description text,
    PRIMARY KEY (location_id),
    UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS dev.nodes
(
    node_id serial,
    node_label character varying(32) NOT NULL,
    type character varying(128) NOT NULL,
    serial_number character varying(128),
    description text,
    PRIMARY KEY (node_id),
    UNIQUE (node_label)
);

CREATE TABLE IF NOT EXISTS dev.sensordata_env
(
    time timestamptz NOT NULL,
    node_id integer NOT NULL,
    location_id integer NOT NULL,
    temperature double precision NOT NULL,
    humidity double precision NOT NULL,
    moisture double precision NOT NULL,
    voltage real
);

CREATE TABLE IF NOT EXISTS dev.sensordata_pax
(
    time timestamptz NOT NULL,
    node_id integer NOT NULL,
    location_id integer NOT NULL,
    pax integer NOT NULL,
    voltage real
);

ALTER TABLE IF EXISTS dev.files_audio
    ADD FOREIGN KEY (location_id)
    REFERENCES dev.locations (location_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.files_audio
    ADD FOREIGN KEY (node_id)
    REFERENCES dev.nodes (node_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.files_image
    ADD FOREIGN KEY (location_id)
    REFERENCES dev.locations (location_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.files_image
    ADD FOREIGN KEY (node_id)
    REFERENCES dev.nodes (node_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.birdnet_results
    ADD FOREIGN KEY (file_id)
    REFERENCES dev.files_audio (file_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.birdnet_results
    ADD FOREIGN KEY (task_id)
    REFERENCES dev.birdnet_tasks (task_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.birdnet_tasks
    ADD FOREIGN KEY (config_id)
    REFERENCES dev.birdnet_configs (config_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;

ALTER TABLE IF EXISTS dev.birdnet_tasks
    ADD FOREIGN KEY (file_id)
    REFERENCES dev.files_audio (file_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;

ALTER TABLE IF EXISTS dev.sensordata_env
    ADD FOREIGN KEY (node_id)
    REFERENCES dev.nodes (node_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.sensordata_env
    ADD FOREIGN KEY (location_id)
    REFERENCES dev.locations (location_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.sensordata_pax
    ADD FOREIGN KEY (node_id)
    REFERENCES dev.nodes (node_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS dev.sensordata_pax
    ADD FOREIGN KEY (location_id)
    REFERENCES dev.locations (location_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

-- fast delete queries in birdnet_tasks
CREATE INDEX IF NOT EXISTS birdnet_results_tasks_fk_index
    ON dev.birdnet_results USING btree
    (task_id ASC NULLS LAST);

-- fast lookup of duplicates
CREATE INDEX IF NOT EXISTS files_audio_object_name_idx
    ON dev.files_audio USING btree
    (object_name ASC NULLS LAST);

-- fast lookup of duplicates
CREATE INDEX IF NOT EXISTS files_audio_sha256_idx
    ON dev.files_audio USING btree
    (sha256 ASC NULLS LAST);

-- fast lookup of duplicates
CREATE INDEX IF NOT EXISTS files_image_object_name_idx
    ON dev.files_image USING btree
    (object_name ASC NULLS LAST);

-- fast lookup of duplicates
CREATE INDEX IF NOT EXISTS files_image_sha256_idx
    ON dev.files_image USING btree
    (sha256 ASC NULLS LAST);

END;

GRANT ALL ON ALL TABLES IN SCHEMA dev TO mitwelten_internal;
GRANT UPDATE ON ALL SEQUENCES IN SCHEMA dev TO mitwelten_internal;

GRANT ALL ON dev.files_audio, dev.files_image, dev.nodes TO mitwelten_upload;
GRANT UPDATE ON dev.files_audio_file_id_seq, dev.files_image_file_id_seq, dev.nodes_node_id_seq TO mitwelten_upload;

GRANT SELECT ON ALL TABLES IN SCHEMA dev TO mitwelten_public;
