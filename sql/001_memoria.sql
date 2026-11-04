-- Memoria conversacional. Ejecutar con un usuario con permisos de DDL.
CREATE SCHEMA IF NOT EXISTS agente_memoria;
 
CREATE TABLE IF NOT EXISTS agente_memoria.conversaciones (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT        NOT NULL,           -- chat_id de OpenWebUI
    user_id     TEXT,                           -- listo para memoria por usuario (fase futura)
    role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_conv_session ON agente_memoria.conversaciones (session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_conv_user    ON agente_memoria.conversaciones (user_id, created_at DESC);