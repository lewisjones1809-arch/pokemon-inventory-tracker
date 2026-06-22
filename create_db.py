import sqlite3

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()


# Delete the tables if they already exist
cur.execute("DROP TABLE IF EXISTS allCards")
cur.execute("DROP TABLE IF EXISTS cardVariants")
cur.execute("DROP TABLE IF EXISTS listedPrices")
cur.execute("DROP TABLE IF EXISTS priceHistory")
cur.execute("DROP TABLE IF EXISTS sales")
cur.execute("DROP TABLE IF EXISTS purchases")
cur.execute("DROP TABLE IF EXISTS importedSets")

# Create the tables
cur.execute("CREATE TABLE allCards (id TEXT PRIMARY KEY, cardName TEXT, setName TEXT, setNumber TEXT, url TEXT, rarity TEXT, imageURL TEXT)")
cur.execute("CREATE TABLE cardVariants (id INTEGER PRIMARY KEY, cardID TEXT, finish TEXT, FOREIGN KEY (cardID) REFERENCES allCards(id))")
cur.execute("CREATE TABLE listedPrices (id INTEGER PRIMARY KEY, variantID INTEGER, listPrice REAL, condition TEXT, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE priceHistory (id INTEGER PRIMARY KEY, variantID INTEGER, averageSellPrice REAL, trendPrice REAL, updatedAt DATETIME, capturedAt DATETIME, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, variantID INTEGER, saleQuantity INTEGER, saleCondition TEXT, salePrice REAL, saleDate DATETIME, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE purchases (id INTEGER PRIMARY KEY, variantID INTEGER, purchaseQuantity INTEGER, purchaseCondition TEXT, purchasePrice REAL, purchaseDate DATETIME, purchaseSource TEXT, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
# tracks which sets have been fully imported so load_inventory can resume after a failure
cur.execute("CREATE TABLE importedSets (setName TEXT PRIMARY KEY)")

# persist the changes and close the connection
con.commit()
con.close()