-- ============================================================================
-- PostgreSQL trigger: notify external agents when a new lead is inserted.
-- Run once as DBA (database owner):
--   psql -U titovtech -d titovtech -f add_lead_notify_trigger.sql
-- ============================================================================

-- 1. Function: sends the new row as JSON via pg_notify on channel 'new_lead'
CREATE OR REPLACE FUNCTION notify_new_lead()
RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('new_lead', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger: fires AFTER INSERT on leads table
DROP TRIGGER IF EXISTS lead_insert_trigger ON leads_lead;
CREATE TRIGGER lead_insert_trigger
AFTER INSERT ON leads_lead
FOR EACH ROW EXECUTE FUNCTION notify_new_lead();
