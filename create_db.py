import sqlite3

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()

# Delete the tables if they already exist
cur.execute("DROP TABLE IF EXISTS allCards")
cur.execute("DROP TABLE IF EXISTS cardVariants")
cur.execute("DROP TABLE IF EXISTS inventory")
cur.execute("DROP TABLE IF EXISTS priceHistory")
cur.execute("DROP TABLE IF EXISTS sales")
cur.execute("DROP TABLE IF EXISTS purchases")

# Create the six tables
cur.execute("CREATE TABLE allCards (id STRING PRIMARY KEY, cardName STRING, setName STRING, setNumber STRING, url STRING, rarity STRING)")
cur.execute("CREATE TABLE cardVariants (id INTEGER PRIMARY KEY, cardID STRING, finish STRING, FOREIGN KEY (cardID) REFERENCES allCards(id))")
cur.execute("CREATE TABLE inventory (id INTEGER PRIMARY KEY, variantID INTEGER, quantity INTEGER, listPrice REAL, condition STRING, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE priceHistory (id INTEGER PRIMARY KEY, variantID INTEGER, averageSellPrice REAL, trendPrice REAL, capturedAt DATETIME,FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, variantID INTEGER, saleQuantity INTEGER, saleCondition STRING, salePrice REAL, saleDate DATETIME, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")
cur.execute("CREATE TABLE purchases (id INTEGER PRIMARY KEY, variantID INTEGER, purchaseQuantity INTEGER, purchaseCondition STRING, purchasePrice REAL, purchaseDate DATETIME, purchaseSource STRING, FOREIGN KEY (variantID) REFERENCES cardVariants(id))")