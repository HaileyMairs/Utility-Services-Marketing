IF OBJECT_ID(N'dbo.vw_EventUnified', N'V') IS NOT NULL
    DROP VIEW dbo.vw_EventUnified;
GO

CREATE VIEW [dbo].[vw_EventUnified]
AS
SELECT
    e.ID                      AS event_id,
    e.DATESTAMP               AS event_datetime,
    CAST(e.DATESTAMP AS date) AS event_date,
    e.ENDDATE                 AS event_end_datetime,

    e.EVENTTYPE_ID            AS event_type_id,
    et.EVENTTYPE              AS event_type_name,
    et.DESCRIPTION            AS event_type_description,
    et.SYSTEM_CLASS           AS event_system_class,

    et.UD1CAPTION             AS event_ud1_caption,
    e.UD1TEXT                 AS event_ud1_value,
    et.UD2CAPTION             AS event_ud2_caption,
    e.UD2TEXT                 AS event_ud2_value,

    e.EVENT_STATUS            AS event_status_code,   -- 'NORMAL' (text) in your dump; adjust join below if numeric
    es.NAME                   AS event_status_name,

    -- keep IDs for later enrichment in Python if needed
    e.LOCID                   AS loc_id,
    e.VARID                   AS var_id,

    e.NOTES                   AS event_notes,
    e.STATUS                  AS event_rec_status,
    e.AUDITUSER               AS event_audit_user,
    e.AUDITTIMESTAMP          AS event_audit_ts
FROM [dbo].[EVENTS] AS e
LEFT JOIN [dbo].[EVENTTYPE]   AS et
    ON e.EVENTTYPE_ID = et.ID
LEFT JOIN [dbo].[EVENTSTATUS] AS es
    -- If EVENTS.EVENT_STATUS stores *text*, this works. If it stores numeric FK, switch to the TRY_CAST line below.
    ON e.EVENT_STATUS = es.NAME
    -- ON TRY_CAST(e.EVENT_STATUS AS int) = es.ID
;
GO
