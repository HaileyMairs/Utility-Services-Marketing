# Changes

## Overall codebase

 - Instead of database connection being dependent on each individual module, it is now handled in Main.py. A menu appears when you launch the program where you put all your information in. Click "Configure Database" in the top left to open this menu again.

## Statistical Summary

 - Still not working

## Table Info

 - Already working
 - Information should probably be formatted to remove parentheses and quotes and stuff
 - There were two other modules that did the exact same thing as Tables.py, so I deleted both of them

## Anomaly Detection

 - Still not working

## Device Health

 - Errors fixed
 - No data returned by queries, but note at top of script says this is intentional. Not sure if we should keep or remove.

## Alarms

 - Already working

## Data Freshness

 - Errors fixed
 - No data returned by queries
 - NOTE: This module uses the OPSTSBP database

## Signal Activity

 - Errors fixed
 - Uses data from the trend_data table in MCRWS-Telog. Maybe we should make a note of that.

## Correlation Analysis

 - Still not working
