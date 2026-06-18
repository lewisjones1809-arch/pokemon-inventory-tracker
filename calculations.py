import sqlite3
import pandas as pd

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()

cur.execute("SELECT * FROM purchases")
purchases = pd.DataFrame(cur.fetchall(), columns=['id', 'variantID', 'purchaseQuantity', 'purchaseCondition', 'purchasePrice', 'purchaseDate', 'purchaseSource']).set_index('id')

cur.execute("SELECT * FROM sales")
sales = pd.DataFrame(cur.fetchall(), columns=['id', 'variantID', 'saleQuantity', 'saleCondition', 'salePrice', 'saleDate']).set_index('id')

price_history = pd.read_sql_query("SELECT * FROM priceHistory", con).set_index('id')

print(purchases)
print(sales)
print(price_history)