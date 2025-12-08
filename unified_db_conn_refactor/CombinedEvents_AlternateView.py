SELECT
    -- Columns from the main data table (DATADD1_AT)
    d.VARID,
    d.DATESTAMP,
    d.CURVALUE,
    d.TEXTVALUE,
    d.STATUS AS DATA_STATUS,
    d.AUDITUSER AS DATA_AUDITUSER,

    -- Columns from the comments table (DATADD1_C)
    c.COMMENT,
    c.AUDITUSER AS COMMENT_AUDITUSER,

    -- Columns from the events table (EVENTS)
    e.NOTES AS EVENT_NOTES,
    e.EVENT_STATUS,
    e.EVENTTYPE_ID,
    e.DATESTAMP AS EVENT_STARTDATE,
    e.ENDDATE AS EVENT_ENDDATE,
    e.AUDITUSER AS EVENT_AUDITUSER

FROM 
    [OPSMOUNT].[dbo].[DATADD1_AT] AS d

-- JOIN 1: Add comments that match the exact VARID and DATESTAMP
LEFT JOIN 
    [OPSMOUNT].[dbo].[DATADD1_C] AS c ON d.VARID = c.VARID 
                                     AND d.DATESTAMP = c.DATESTAMP

-- JOIN 2: Add events where the data point's date falls within the event's time window
LEFT JOIN 
    [OPSMOUNT].[dbo].[EVENTS] AS e ON d.VARID = e.VARID 
                                  AND d.DATESTAMP BETWEEN e.DATESTAMP AND e.ENDDATE;
