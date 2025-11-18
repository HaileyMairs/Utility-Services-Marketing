# SQL loader port of main program

## Purpose

This version of the main program loads .sql files contained within the sql_data/ directory instead of a local SQL server, which the main version uses. This gives the program compatibility on any machine regardless of whether a Microsoft SQL server is set up. It also always you to specify which databases you want to include--based on which databases are included in sql_data/

## Usage (in contrast to HaileyGUI)

1. Export any databases you want to use as .sql files and drop them in sql_data/
2. Run main.py. The first run will take a while depending on how large the .sql files are. Don't interrupt it as it's creating caches that it will use on subsequent runs instead of the .sql files.
3. Any subsequent runs should be instantaneous.
