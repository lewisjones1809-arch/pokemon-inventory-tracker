import sqlite3
import pandas as pd
from functions import create_inventory, get_variant_id, call_api, show_latest_prices, calc_fifo_cost, calc_current_value

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()

# Create the inventory and get current value
inventory = create_inventory(con)
current_value = calc_current_value(inventory)
print(f"Current Inventory value is £{current_value}")

# Initalise running totals
total_remaining_cost = 0
total_realised_basis = 0

# Compute realised cost and remaining cost
for index, card in inventory.iterrows():
    total_remaining_cost += calc_fifo_cost(cur, card['variantID'], card['condition_x'])[1]
    total_realised_basis += calc_fifo_cost(cur, card['variantID'], card['condition_x'])[0]

# Compute unrealised margin
unrealised_margin = round(current_value - total_remaining_cost, 2)
print(f"Unrealised margin is £{unrealised_margin}")

# Compute total sales
total_sales = cur.execute("SELECT SUM(salePrice * saleQuantity) FROM sales").fetchone()[0]
print(f"Total lifetime sales are £{total_sales}")

# Compute profit
realised_p_l = round(total_sales - total_realised_basis,2)
print(f"Profit is £{realised_p_l}")

# Close connection
con.close()