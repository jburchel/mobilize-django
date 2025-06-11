# Supabase Database Schema

This document provides a comprehensive reference of the actual database schema from the Supabase production database as of June 5, 2025. This schema should be used as the source of truth when synchronizing Django models with the database.

## Table of Contents

- [Supabase Database Schema](#supabase-database-schema)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Core Tables](#core-tables)
    - [contacts](#contacts)
    - [people](#people)
    - [churches](#churches)
  - [Communication Tables](#communication-tables)
    - [communications](#communications)
    - [email-campaigns](#email-campaigns)
    - [email-settings](#email-settings)
    - [email-signatures](#email-signatures)
    - [email-templates](#email-templates)
    - [email-tracking](#email-tracking)
  - [Integration Tables](#integration-tables)
    - [google-tokens](#google-tokens)
    - [google-workspace-settings](#google-workspace-settings)
  - [Pipeline Management](#pipeline-management)
    - [pipelines](#pipelines)
    - [pipeline-stages](#pipeline-stages)
    - [pipeline-contacts](#pipeline-contacts)
    - [pipeline-stage-history](#pipeline-stage-history)
  - [User Management](#user-management)
    - [users](#users)
    - [roles](#roles)
    - [permissions](#permissions)
    - [role-permissions](#role-permissions)
    - [user-offices](#user-offices)
    - [user-tokens](#user-tokens)
  - [Organization Management](#organization-management)
    - [offices](#offices)
  - [Task Management](#task-management)
    - [tasks](#tasks)
  - [System Tables](#system-tables)
    - [alembic-version](#alembic-version)
    - [sync-history](#sync-history)

## Overview

The Mobilize CRM database contains multiple interconnected tables that store information about contacts, churches, people, communications, and system management. This document captures the exact schema as it exists in the production Supabase database.

## Core Tables

### contacts

Base table for contact information. Both people and churches inherit from this table.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('contacts_id_seq'::regclass) |
| church_name | character varying | YES | NULL |
| first_name | character varying | YES | NULL |
| last_name | character varying | YES | NULL |
| image | character varying | YES | NULL |
| preferred_contact_method | character varying | YES | NULL |
| phone | character varying | YES | NULL |
| email | character varying | YES | NULL |
| street_address | character varying | YES | NULL |
| city | character varying | YES | NULL |
| state | character varying | YES | NULL |
| zip_code | character varying | YES | NULL |
| initial_notes | text | YES | NULL |
| date_created | date | YES | NULL |
| date_modified | date | YES | NULL |
| google_resource_name | character varying | YES | NULL |
| type | character varying | YES | NULL |
| address | text | YES | NULL |
| country | text | YES | NULL |
| notes | text | YES | NULL |
| office_id | integer | YES | NULL |
| user_id | integer | YES | NULL |
| updated_at | date | YES | NULL |
| last_synced_at | date | YES | NULL |
| created_at | date | YES | NULL |
| conflict_data | jsonb | YES | NULL |
| google_contact_id | character varying | YES | NULL |
| has_conflict | boolean | YES | NULL |

### people

Table for individual contacts. Inherits from the contacts table.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | NULL |
| church_role | character varying | YES | NULL |
| church_id | integer | YES | NULL |
| spouse_first_name | character varying | YES | NULL |
| spouse_last_name | character varying | YES | NULL |
| virtuous | boolean | YES | NULL |
| title | character varying | YES | NULL |
| home_country | character varying | YES | NULL |
| marital_status | character varying | YES | NULL |
| people_pipeline | character varying | YES | NULL |
| priority | character varying | YES | NULL |
| assigned_to | character varying | YES | NULL |
| source | character varying | YES | NULL |
| referred_by | character varying | YES | NULL |
| info_given | text | YES | NULL |
| desired_service | text | YES | NULL |
| reason_closed | text | YES | NULL |
| date_closed | date | YES | NULL |
| user_id | character varying | YES | NULL |
| type | character varying | YES | NULL |
| occupation | character varying | YES | NULL |
| last_contact | date | YES | NULL |
| last_name | character varying | YES | NULL |
| website | character varying | YES | NULL |
| languages | text | YES | NULL |
| birthday | date | YES | NULL |
| is_primary_contact | boolean | YES | NULL |
| twitter | character varying | YES | NULL |
| anniversary | date | YES | NULL |
| first_name | character varying | YES | NULL |
| tags | text | YES | NULL |
| facebook | character varying | YES | NULL |
| next_contact | date | YES | NULL |
| linkedin | character varying | YES | NULL |
| google_contact_id | character varying | YES | NULL |
| employer | character varying | YES | NULL |
| status | character varying | YES | NULL |
| last_synced_at | date | YES | NULL |
| instagram | character varying | YES | NULL |
| skills | text | YES | NULL |
| interests | text | YES | NULL |
| pipeline_stage | character varying | YES | NULL |

### churches

Table for church contacts. Inherits from the contacts table.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | NULL |
| location | character varying | YES | NULL |
| main_contact_id | integer | YES | NULL |
| virtuous | boolean | YES | NULL |
| senior_pastor_first_name | character varying | YES | NULL |
| senior_pastor_last_name | character varying | YES | NULL |
| senior_pastor_phone | character varying | YES | NULL |
| senior_pastor_email | character varying | YES | NULL |
| missions_pastor_first_name | character varying | YES | NULL |
| missions_pastor_last_name | character varying | YES | NULL |
| mission_pastor_phone | character varying | YES | NULL |
| mission_pastor_email | character varying | YES | NULL |
| primary_contact_first_name | character varying | YES | NULL |
| primary_contact_last_name | character varying | YES | NULL |
| primary_contact_phone | character varying | YES | NULL |
| primary_contact_email | character varying | YES | NULL |
| website | character varying | YES | NULL |
| denomination | character varying | YES | NULL |
| congregation_size | integer | YES | NULL |
| church_pipeline | character varying | YES | NULL |
| priority | character varying | YES | NULL |
| assigned_to | character varying | YES | NULL |
| source | character varying | YES | NULL |
| referred_by | character varying | YES | NULL |
| info_given | text | YES | NULL |
| reason_closed | text | YES | NULL |
| year_founded | integer | YES | NULL |
| date_closed | date | YES | NULL |
| office_id | integer | YES | NULL |
| name | text | YES | NULL |
| senior_pastor_name | text | YES | NULL |
| weekly_attendance | integer | YES | NULL |
| owner_id | integer | YES | NULL |

## Communication Tables

### communications

Table for tracking all communications with contacts.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('communications_id_seq'::regclass) |
| type | character varying | YES | NULL |
| message | character varying | YES | NULL |
| date_sent | timestamp without time zone | YES | NULL |
| person_id | integer | YES | NULL |
| church_id | integer | YES | NULL |
| gmail_message_id | character varying | YES | NULL |
| gmail_thread_id | character varying | YES | NULL |
| email_status | character varying | YES | NULL |
| subject | character varying | YES | NULL |
| attachments | character varying | YES | NULL |
| last_synced_at | timestamp without time zone | YES | NULL |
| user_id | character varying | YES | NULL |
| sender | character varying | YES | NULL |
| owner_id | integer | YES | NULL |
| office_id | integer | YES | NULL |
| updated_at | date | YES | NULL |
| google_calendar_event_id | character varying | YES | NULL |
| created_at | date | YES | NULL |
| google_meet_link | character varying | YES | NULL |
| date | date | YES | NULL |
| direction | character varying | YES | NULL |

### email-campaigns

Table for managing email marketing campaigns.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('email_campaigns_id_seq'::regclass) |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| name | character varying | NO | NULL |
| description | text | YES | NULL |
| status | character varying | NO | NULL |
| subject | character varying | NO | NULL |
| content | text | NO | NULL |
| scheduled_at | timestamp without time zone | YES | NULL |
| sent_at | timestamp without time zone | YES | NULL |
| recipient_count | integer | YES | NULL |
| recipient_filter | text | YES | NULL |
| sent_count | integer | YES | NULL |
| open_count | integer | YES | NULL |
| click_count | integer | YES | NULL |
| bounce_count | integer | YES | NULL |
| template_id | integer | YES | NULL |
| created_by | integer | NO | NULL |
| office_id | integer | NO | NULL |

### email-settings

Table for email configuration settings.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| mail_default_sender | character varying | YES | NULL |
| email_signature | text | YES | NULL |
| smtp_enabled | boolean | NO | NULL |
| smtp_server | character varying | YES | NULL |
| smtp_port | integer | YES | NULL |
| smtp_username | character varying | YES | NULL |
| smtp_password | character varying | YES | NULL |
| smtp_use_tls | boolean | NO | NULL |
| sent_today | integer | NO | NULL |
| sent_week | integer | NO | NULL |
| bounced | integer | NO | NULL |
| failed | integer | NO | NULL |
| delivery_rate | double precision | NO | NULL |
| id | integer | NO | nextval('email_settings_id_seq'::regclass) |
| created_at | timestamp without time zone | NO | NULL |
| updated_at | timestamp without time zone | NO | NULL |

### email-signatures

Table for storing email signature templates.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('email_signatures_id_seq'::regclass) |
| user_id | character varying | NO | NULL |
| name | character varying | NO | NULL |
| content | text | NO | NULL |
| logo_url | character varying | YES | NULL |
| is_default | boolean | YES | NULL |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |

### email-templates

Table for storing reusable email templates.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('email_templates_id_seq'::regclass) |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| name | character varying | NO | NULL |
| subject | character varying | NO | NULL |
| content | text | NO | NULL |
| category | character varying | YES | NULL |
| variables | text | YES | NULL |
| is_active | boolean | YES | NULL |
| created_by | integer | NO | NULL |
| office_id | integer | NO | NULL |

### email-tracking

Table for tracking email engagement metrics.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('email_tracking_id_seq'::regclass) |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| email_subject | character varying | NO | NULL |
| recipient_email | character varying | NO | NULL |
| status | character varying | NO | NULL |
| sent_at | timestamp without time zone | NO | NULL |
| opened_at | timestamp without time zone | YES | NULL |
| open_count | integer | YES | NULL |
| last_opened_at | timestamp without time zone | YES | NULL |
| clicked_at | timestamp without time zone | YES | NULL |
| click_count | integer | YES | NULL |
| last_clicked_at | timestamp without time zone | YES | NULL |
| message_id | character varying | YES | NULL |
| tracking_pixel | character varying | YES | NULL |
| template_id | integer | YES | NULL |
| sender_id | integer | NO | NULL |
| person_id | integer | YES | NULL |
| office_id | integer | NO | NULL |
| bulk_send_id | character varying | YES | NULL |

## Integration Tables

### google-tokens

Table for storing Google API authentication tokens.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('google_tokens_id_seq'::regclass) |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| access_token | character varying | NO | NULL |
| refresh_token | character varying | YES | NULL |
| token_type | character varying | NO | NULL |
| expires_at | timestamp without time zone | NO | NULL |
| user_id | integer | NO | NULL |
| email | character varying | YES | NULL |
| scopes | text | YES | NULL |

### google-workspace-settings

Table for Google Workspace integration configuration.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| enabled | boolean | NO | NULL |
| domain | character varying | YES | NULL |
| client_id | character varying | YES | NULL |
| client_secret | character varying | YES | NULL |
| redirect_uri | character varying | YES | NULL |
| admin_email | character varying | YES | NULL |
| sync_frequency | character varying | NO | NULL |
| last_sync | timestamp without time zone | YES | NULL |
| scopes | text | YES | NULL |
| connected_users | integer | NO | NULL |
| synced_users | integer | NO | NULL |
| synced_groups | integer | NO | NULL |
| synced_events | integer | NO | NULL |
| id | integer | NO | nextval('google_workspace_settings_id_seq'::regclass) |
| created_at | timestamp without time zone | NO | NULL |
| updated_at | timestamp without time zone | NO | NULL |

## Pipeline Management

### pipelines

Table for defining sales or recruitment pipelines.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('pipelines_id_seq'::regclass) |
| name | character varying | NO | NULL |
| description | text | YES | NULL |
| pipeline_type | character varying | YES | NULL |
| office_id | integer | NO | NULL |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| is_main_pipeline | boolean | YES | NULL |
| parent_pipeline_stage | character varying | YES | NULL |

### pipeline-stages

Table for defining the stages within a pipeline.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('pipeline_stages_id_seq'::regclass) |
| name | character varying | NO | NULL |
| description | text | YES | NULL |
| order | integer | NO | NULL |
| color | character varying | YES | NULL |
| pipeline_id | integer | NO | NULL |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| auto_move_days | integer | YES | NULL |
| auto_reminder | boolean | YES | NULL |
| auto_task_template | text | YES | NULL |

### pipeline-contacts

Table for tracking contacts within pipelines.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('pipeline_contacts_id_seq'::regclass) |
| contact_id | integer | NO | NULL |
| pipeline_id | integer | NO | NULL |
| current_stage_id | integer | NO | NULL |
| entered_at | timestamp without time zone | YES | NULL |
| last_updated | timestamp without time zone | YES | NULL |

### pipeline-stage-history

Table for tracking contact movement through pipeline stages.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('pipeline_stage_history_id_seq'::regclass) |
| pipeline_contact_id | integer | NO | NULL |
| from_stage_id | integer | YES | NULL |
| to_stage_id | integer | NO | NULL |
| notes | text | YES | NULL |
| created_at | timestamp without time zone | YES | NULL |
| created_by_id | integer | YES | NULL |

## User Management

### users

Table for user accounts and authentication.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('users_id_seq'::regclass) |
| instance_id | uuid | YES | NULL |
| firebase_uid | character varying | YES | NULL |
| aud | character varying | YES | NULL |
| email | character varying | YES | NULL |
| created_at | timestamp without time zone | YES | NULL |
| role | character varying | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| encrypted_password | character varying | YES | NULL |
| username | character varying | YES | NULL |
| email_confirmed_at | timestamp with time zone | YES | NULL |
| password_hash | character varying | YES | NULL |
| invited_at | timestamp with time zone | YES | NULL |
| first_name | character varying | YES | NULL |
| last_name | character varying | YES | NULL |
| confirmation_token | character varying | YES | NULL |
| phone | character varying | YES | NULL |
| confirmation_sent_at | timestamp with time zone | YES | NULL |
| google_calendar_sync | boolean | YES | false |
| google_meet_enabled | boolean | YES | false |
| phone_confirmed_at | timestamp with time zone | YES | NULL |
| email_sync_contacts_only | boolean | YES | true |
| office_id | integer | YES | NULL |
| person_id | integer | YES | NULL |
| confirmed_at | timestamp with time zone | YES | NULL |
| is_sso_user | boolean | NO | false |
| deleted_at | timestamp with time zone | YES | NULL |
| is_anonymous | boolean | NO | false |

### roles

Table for defining user roles.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| name | character varying | NO | NULL |
| description | text | YES | NULL |
| id | integer | NO | nextval('roles_id_seq'::regclass) |
| created_at | timestamp without time zone | NO | NULL |
| updated_at | timestamp without time zone | NO | NULL |

### permissions

Table for defining system permissions.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('permissions_id_seq'::regclass) |
| name | character varying | NO | NULL |
| description | text | YES | NULL |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |

### role-permissions

Table for mapping permissions to roles.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| role_id | integer | NO | NULL |
| permission_id | integer | NO | NULL |
| id | integer | NO | nextval('role_permissions_id_seq'::regclass) |
| created_at | timestamp without time zone | NO | NULL |
| updated_at | timestamp without time zone | NO | NULL |

### user-offices

Table for mapping users to offices.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('user_offices_id_seq'::regclass) |
| user_id | character varying | NO | NULL |
| office_id | integer | NO | NULL |
| role | character varying | NO | NULL |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| assigned_at | date | YES | NULL |

### user-tokens

Table for storing user authentication tokens.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('user_tokens_id_seq'::regclass) |
| user_id | character varying | NO | NULL |
| token_data | text | NO | NULL |
| created_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |

## Organization Management

### offices

Table for organization offices or locations.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('offices_id_seq'::regclass) |
| name | character varying | NO | NULL |
| address | character varying | YES | NULL |
| city | character varying | YES | NULL |
| state | character varying | YES | NULL |
| zip_code | character varying | YES | NULL |
| phone | character varying | YES | NULL |
| email | character varying | YES | NULL |
| created_at | timestamp without time zone | YES | NULL |
| updated_at | timestamp without time zone | YES | NULL |
| country | character varying | YES | NULL |
| office_hours | character varying | YES | NULL |
| timezone | character varying | YES | 'America/New_York'::character varying |
| is_active | boolean | YES | true |
| settings | jsonb | YES | NULL |
| notification_settings | jsonb | YES | NULL |
| workspace_domain | character varying | YES | NULL::character varying |
| calendar_sync_enabled | boolean | YES | true |
| meet_integration_enabled | boolean | YES | true |
| drive_integration_enabled | boolean | YES | true |
| oauth_settings | jsonb | YES | NULL |

## Task Management

### tasks

Table for task tracking and management.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('tasks_id_seq'::regclass) |
| title | character varying | YES | NULL |
| description | character varying | YES | NULL |
| due_date | date | YES | NULL |
| due_time | character varying | YES | NULL |
| reminder_time | character varying | YES | NULL |
| priority | character varying | YES | NULL |
| status | character varying | YES | NULL |
| person_id | integer | YES | NULL |
| church_id | integer | YES | NULL |
| google_calendar_event_id | character varying | YES | NULL |
| google_calendar_sync_enabled | boolean | YES | NULL |
| last_synced_at | timestamp without time zone | YES | NULL |
| user_id | character varying | YES | NULL |
| created_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |
| due_time_details | text | YES | NULL |
| reminder_option | character varying | YES | 'none'::character varying |
| category | character varying | YES | NULL::character varying |
| assigned_to | character varying | YES | NULL::character varying |
| contact_id | integer | YES | NULL |
| created_by | integer | YES | NULL |
| owner_id | integer | YES | NULL |
| office_id | integer | YES | NULL |
| completed_date | timestamp without time zone | YES | NULL |
| completion_notes | text | YES | NULL |
| type | character varying | NO | 'general'::character varying |
| completed_at | timestamp with time zone | YES | NULL |
| reminder_sent | boolean | YES | false |

## System Tables

### alembic-version

Table for tracking database migration versions.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| version_num | character varying | NO | NULL |

### sync-history

Table for tracking data synchronization operations.

| Column Name | Data Type | Nullable | Default |
|-------------|-----------|----------|----------|
| id | integer | NO | nextval('sync_history_id_seq'::regclass) |
| user_id | integer | NO | NULL |
| sync_type | character varying | NO | NULL |
| status | character varying | YES | NULL |
| items_processed | integer | YES | NULL |
| items_created | integer | YES | NULL |
| items_updated | integer | YES | NULL |
| items_skipped | integer | YES | NULL |
| items_failed | integer | YES | NULL |
| error_message | text | YES | NULL |
| created_at | timestamp without time zone | YES | NULL |
| completed_at | timestamp without time zone | YES | NULL |
