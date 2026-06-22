import sqlite3

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()


# Delete the tables if they already exist
cur.execute("DROP TABLE allCards")
cur.execute("DROP TABLE cardVariants")
cur.execute("DROP TABLE listedPrices")
cur.execute("DROP TABLE priceHistory")
cur.execute("DROP TABLE sales")
cur.execute("DROP TABLE purchases")
cur.execute("DROP TABLE IF EXISTS importedSets")

# Create the tables
cur.execute("CREATE TABLE allCards (id STRING PRIMARY KEY, cardName STRING, setName STRING, setNumber STRING, url STRING, rarity STRING, imageURL STRING)")
cur.execute("CREATE TABLE cardVariants (id INTEGER PRIMARY KEY, cardID STRING, finish STRING, FOREIGN KEY (cardID) REFERENCES allCards(id))")
cur.execute("CREATE TABLE listedPrices (id INTEGER PRIMARY KEY, variantID INTEGER, listPrice REAL, condition STRING, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE priceHistory (id INTEGER PRIMARY KEY, variantID INTEGER, averageSellPrice REAL, trendPrice REAL, updatedAt DATETIME, capturedAt DATETIME, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, variantID INTEGER, saleQuantity INTEGER, saleCondition STRING, salePrice REAL, saleDate DATETIME, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE purchases (id INTEGER PRIMARY KEY, variantID INTEGER, purchaseQuantity INTEGER, purchaseCondition STRING, purchasePrice REAL, purchaseDate DATETIME, purchaseSource STRING, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
# tracks which sets have been fully imported so load_inventory can resume after a failure
cur.execute("CREATE TABLE importedSets (setName STRING PRIMARY KEY)")