from functions import calc_fifo_cost, make_purchase, make_sale, get_variant_id, reset_table
import sqlite3

# Create a connection to the database
con = sqlite3.connect('pokemon_tracker.db')

# Create a cursor object to execute SQL commands
cur = con.cursor()

# set up variables
card_id_a = 'bw1-2'
card_id_b = 'sm1-2'
finish = 'Normal'
source = 'eBay'

# Test Case 1
reset_table(cur, 'purchases')
reset_table(cur, 'sales')
make_purchase(cur, card_id_a, finish, 5, 'Near Mint', 10, '2026-01-01', source)
make_sale(cur, card_id_a, finish, 2, 'Near Mint', 20, '2026-01-02')
print(calc_fifo_cost(cur, get_variant_id(cur, 'bw1-2', 'Normal'), 'Near Mint'))

# Test Case 2
reset_table(cur, 'purchases')
reset_table(cur, 'sales')
make_purchase(cur, card_id_a, finish, 3, 'Near Mint', 10, '2026-01-01', source)
make_purchase(cur, card_id_a, finish, 5, 'Near Mint', 20, '2026-02-01', source)
make_sale(cur, card_id_a, finish, 4, 'Near Mint', 20, '2026-03-01')
print(calc_fifo_cost(cur, get_variant_id(cur, 'bw1-2', 'Normal'), 'Near Mint'))

# Test Case 3
reset_table(cur, 'purchases')
reset_table(cur, 'sales')
make_purchase(cur, card_id_a, finish, 4, 'Near Mint', 15, '2026-01-01', source)
make_sale(cur, card_id_a, finish, None, 'Near Mint', 20, '2026-01-02')
print(calc_fifo_cost(cur, get_variant_id(cur, 'bw1-2', 'Normal'), 'Near Mint'))

# Test Case 4
reset_table(cur, 'purchases')
reset_table(cur, 'sales')
make_purchase(cur, card_id_a, finish, 3, 'Near Mint', 10, '2026-01-01', source)
make_sale(cur, card_id_a, finish, 3, 'Near Mint', 20, '2026-01-02')
print(calc_fifo_cost(cur, get_variant_id(cur, 'bw1-2', 'Normal'), 'Near Mint'))

# Test Case 2
reset_table(cur, 'purchases')
reset_table(cur, 'sales')
make_purchase(cur, card_id_a, finish, 2, 'Near Mint', 5, '2026-01-01', source)
make_purchase(cur, card_id_a, finish, 2, 'Near Mint', 8, '2026-02-01', source)
make_sale(cur, card_id_a, finish, 1, 'Near Mint', 10, '2026-03-01')
make_sale(cur, card_id_a, finish, 2, 'Near Mint', 12, '2026-04-01')
print(calc_fifo_cost(cur, get_variant_id(cur, 'bw1-2', 'Normal'), 'Near Mint'))

# Test Case 2
reset_table(cur, 'purchases')
reset_table(cur, 'sales')
make_purchase(cur, card_id_a, finish, 4, 'Near Mint', 30, '2026-03-01', source)
make_purchase(cur, card_id_a, finish, 4, 'Near Mint', 10, '2026-01-01', source)
make_sale(cur, card_id_a, finish, 5, 'Near Mint', 20, '2026-04-01')
print(calc_fifo_cost(cur, get_variant_id(cur, 'bw1-2', 'Normal'), 'Near Mint'))