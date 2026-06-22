import sqlite3
from functions import update_prices, create_new_cards, call_api

# create a connection to the database and create cursor
con = sqlite3.connect('pokemon_tracker.db')
cur = con.cursor()
        
# define the parameters for the API call and make the call
params={"select": "id,name,set,number,cardmarket,rarity,images"}
response_json = call_api(params).json()
print(response_json)

# insert the data
create_new_cards(cur, response_json['data'])
update_prices(cur, response_json['data'])


# commit the changes and close the connection
con.commit()
con.close()
