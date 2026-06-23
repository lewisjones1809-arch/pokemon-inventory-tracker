import sqlite3
from functions import create_tables

con = sqlite3.connect('pokemon_tracker.db')

cur = con.cursor()

# Delete the tables if they already exist (destructive: full rebuild)
cur.execute("DROP TABLE IF EXISTS allCards")
cur.execute("DROP TABLE IF EXISTS cardVariants")
cur.execute("DROP TABLE IF EXISTS listedPrices")
cur.execute("DROP TABLE IF EXISTS priceHistory")
cur.execute("DROP TABLE IF EXISTS sales")
cur.execute("DROP TABLE IF EXISTS purchases")
cur.execute("DROP TABLE IF EXISTS importedSets")

# Recreate the tables from the single source of truth in functions.py
create_tables(con)

# persist the changes and close the connection
con.commit()
con.close()
