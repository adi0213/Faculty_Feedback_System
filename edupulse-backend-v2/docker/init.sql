-- Docker initialization: create PostgreSQL schemas and extensions
CREATE SCHEMA IF NOT EXISTS registry;
CREATE SCHEMA IF NOT EXISTS feedback;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
