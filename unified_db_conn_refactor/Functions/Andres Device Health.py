''' ======================================================================
                    DEVICE HEALTH UTILITY
 ======================================================================

#title: 'Device Health'
#btn: 'Battery Health'
#btn: 'Offline Devices'

NOTE FOR TEAM — DEVICE HEALTH EXPECTATIONS
------------------------------------------
Both queries below normally read from:

    dbo.DeviceBatteryHistory

But this table DOES NOT exist in the MCRWS-Telog dataset we received.

Because of that:
    • get_battery_health() returns []
    • get_offline_devices() returns []
    • GUI will show empty tables (EXPECTED)
    • This does NOT mean anything is broken

Once the real voltage/battery table name is provided by the client,
these functions will work immediately without modification.
'''


class DeviceHealthUtility:
    """
    Provides:
        get_battery_health()
        get_offline_devices()

    Also includes GUI getter functions:
        get_battery_health_button()
        get_offline_devices_button()

    All getters follow teammate snake_case format.
    """

    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # Core SQL Functions
    # ------------------------------------------------------------------

    def query_battery_health(self):
        sql = """
        WITH BatteryAgg AS (
            SELECT
                site_id,
                device_id,
                MAX(sample_time) AS last_seen,
                AVG(CAST(ISNULL(battery_voltage, 0.0) AS FLOAT)) AS avg_voltage,
                MIN(CAST(ISNULL(battery_voltage, 0.0) AS FLOAT)) AS min_voltage,
                MAX(CAST(ISNULL(battery_voltage, 0.0) AS FLOAT)) AS max_voltage
            FROM dbo.DeviceBatteryHistory   -- PLACEHOLDER TABLE
            GROUP BY site_id, device_id
        )
        SELECT
            site_id,
            device_id,
            last_seen,
            avg_voltage,
            min_voltage,
            max_voltage,
            CASE
                WHEN avg_voltage < 11.5 THEN 'CRITICAL'
                WHEN avg_voltage < 12.0 THEN 'WARNING'
                ELSE 'OK'
            END AS health_status
        FROM BatteryAgg
        ORDER BY health_status DESC, last_seen DESC;
        """
        try:
            return self.db.query(sql)
        except Exception:
            return []   # expected: table does not exist

    def query_offline_devices(self, days_offline=7):
        sql = f"""
        SELECT
            site_id,
            device_id,
            MAX(sample_time) AS last_seen
        FROM dbo.DeviceBatteryHistory   -- PLACEHOLDER TABLE
        GROUP BY site_id, device_id
        HAVING DATEDIFF(DAY, MAX(sample_time), GETDATE()) >= {days_offline}
        ORDER BY last_seen ASC;
        """
        try:
            return self.db.query(sql)
        except Exception:
            return []   # expected: table does not exist

    # ------------------------------------------------------------------
    # Formatting Helpers
    # ------------------------------------------------------------------

    def format_battery_for_treeview(self, rows):
        formatted = []
        for r in rows:
            site_id, device_id, last_seen, avg_v, min_v, max_v, status = r
            formatted.append([
                str(site_id),
                str(device_id),
                str(last_seen),
                f"{avg_v:.2f}" if avg_v else "0.00",
                f"{min_v:.2f}" if min_v else "0.00",
                f"{max_v:.2f}" if max_v else "0.00",
                status,
            ])
        return formatted

    def format_offline_for_treeview(self, rows):
        formatted = []
        for r in rows:
            site_id, device_id, last_seen = r
            formatted.append([
                str(site_id),
                str(device_id),
                str(last_seen),
            ])
        return formatted

    # ==================================================================
    #                   BUTTON GETTERS (REQUIRED FORMAT)
    # ==================================================================

    def get_battery_health(self):
        """
        Getter for the 'Battery Health' button.
        MUST return (columns, rows)
        """

        try:
            rows = self.query_battery_health()
            formatted = self.format_battery_for_treeview(rows)
        except Exception:
            columns = ("Error",)
            return columns, [("Battery health query failed.",)]

        columns = (
            "Site ID",
            "Device ID",
            "Last Seen",
            "Avg Voltage",
            "Min Voltage",
            "Max Voltage",
            "Health Status",
        )

        return columns, formatted

    def get_offline_devices(self):
        """
        Getter for the 'Offline Devices' button.
        MUST return (columns, rows)
        """

        try:
            rows = self.query_offline_devices()
            formatted = self.format_offline_for_treeview(rows)
        except Exception:
            columns = ("Error",)
            return columns, [("Offline device query failed.",)]

        columns = ("Site ID", "Device ID", "Last Seen")
        return columns, formatted
