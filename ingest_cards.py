import sqlite3
from functions import update_prices, create_new_cards, call_api

# create a connection to the database and create cursor
con = sqlite3.connect('pokemon_tracker.db')
cur = con.cursor()

'''
looping using call_api test
for i in range(1,6):
    params={"select": "id,name,set,number,cardmarket,rarity", "page": i}
    response_json = call_api(params)

    # insert the data
    for item in response_json['data']:
        create_new_card(cur, item)
        update_prices(cur, item)
'''
        
# define the parameters for the API call and make the call
params={"select": "id,name,set,number,cardmarket,rarity"}
response_json = call_api(params).json()

# insert the data
create_new_cards(cur, response_json['data'])
update_prices(cur, response_json['data'])


# commit the changes and close the connection
con.commit()
con.close()
