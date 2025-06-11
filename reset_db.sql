-- Drop existing tables in reverse order of dependencies
DROP TABLE IF EXISTS church_contacts CASCADE;
DROP TABLE IF EXISTS churches CASCADE;
DROP TABLE IF EXISTS people CASCADE;
DROP TABLE IF EXISTS communications CASCADE;
DROP TABLE IF EXISTS contact_interactions CASCADE;
DROP TABLE IF EXISTS church_interactions CASCADE;
DROP TABLE IF EXISTS django_session CASCADE;
DROP TABLE IF EXISTS django_email_attachments CASCADE;
DROP TABLE IF EXISTS communications_emailsignature CASCADE;
DROP TABLE IF EXISTS communications_emailtemplate CASCADE;
DROP TABLE IF EXISTS communications_communication CASCADE;
DROP TABLE IF EXISTS user_offices CASCADE;
DROP TABLE IF EXISTS offices CASCADE;
DROP TABLE IF EXISTS django_admin_log CASCADE;
DROP TABLE IF EXISTS google_tokens CASCADE;
DROP TABLE IF EXISTS users_user_permissions CASCADE;
DROP TABLE IF EXISTS users_groups CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS auth_group_permissions CASCADE;
DROP TABLE IF EXISTS auth_group CASCADE;
DROP TABLE IF EXISTS auth_permission CASCADE;
DROP TABLE IF EXISTS django_content_type CASCADE;
DROP TABLE IF EXISTS django_migrations CASCADE;

-- Reset sequences
ALTER SEQUENCE IF EXISTS django_migrations_id_seq RESTART WITH 1;
