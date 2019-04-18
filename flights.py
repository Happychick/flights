import requests
# These 2 lines and the last 2 wrap your web page, you put the rest between
from flask import Flask, request, render_template #make sure this is upper case
app = Flask(__name__)
# In essence you are developing web pages
# The name of the app will be run on the flask server

import json
import pandas as pd
from datetime import datetime
from collections import defaultdict

# Set the variable for the API Key that allows us to tie to YOSO
apikey = '3Ahc4gcDjDjrHBJyHBm0cRzAC1LAxBAT'
# Set the limit otherwise the search won't work!
limit = '200'

# Mafe a function for each part
# This is the location function

def get_locations_city(city_from):

    # Add headers for requests
    headers = {'accept':'application/json', 'apikey':apikey}

    # Split string into list of variables
    loc = city_from.split(',')

    #Define variables
    city = loc[0]
    country = loc[1]

    # First get city info
    params_loc = {
        'term':city, #This is what will show in the search tab
        'locale':'en-US', #Language of search no_results
        'location_types':'city',
        'limit':1
        }

    # Extract location infromation out using location API
    resp=requests.get('https://kiwicom-prod.apigee.net/locations/query', params = params_loc, headers = headers)
    # Parse json into dictionary
    results= resp.json()

    # What fields from the json do I want returned, It's both but for different purposes
    location_code_city = pd.DataFrame(results['locations'], columns=['code','country'])


    # First get city info
    params_loc = {
        'term':country, #This is what will show in the search tab
        'locale':'en-US', #Language of search no_results
        'location_types':'country',
        'limit':1
    }

    # Extract location infromation out using location API
    resp=requests.get('https://kiwicom-prod.apigee.net/locations/query', params = params_loc, headers = headers)

    # Parse json into dictionary
    results= resp.json()

    # What fields from the json do I want returned, It's both but for different purposes
    location_code_country = pd.DataFrame(results['locations'], columns=['code'])


    for i in range(len(location_code_city)):
        if location_code_city['country'][i]['code'] == location_code_country['code'][0]:
            code_id = location_code_city['code'][i]
        else: pass

    return code_id


# Get data
def get_flights(flight_type,city_from,date_from,date_to=None):

    city_id = get_locations_city(city_from)
    headers={'accept':'application/json','apikey':apikey}
    one_for_city = '1'

    #Ensure that date is captured in good formate
    #dt = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%y')
    df = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d/%m/%Y')

    if flight_type =="One-way":
        # Use the code to get the flights
        params = {
            'flyFrom':fl_id, #Use the code from the location match above
            'dateFrom': df,
            'dateTo':df,
            'one_for_city':'1',
            'limit':limit
        }
    else:
        dt = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
        params = {
            'flyFrom':fl_id, #Use the code from the location match above
            'dateFrom': df,
            'dateTo':df,
            'return_from':dt,
            'return_to':dt,
            'flight_type':'round',
            'limit':limit
        }

    # Get data
    resp=requests.get('https://kiwicom-prod.apigee.net/v2/search?', params = params, headers = headers)
    # Parse json into dictionary
    flights=resp.json()

    return flights

# This actually extracts the flight prices for each desitnation city
# Step 2: Add the deeplink for the flight

def flight_output(flight1, flight2):
    flight_matches = defaultdict(dict)

    for flight in flight1['data']:
        cityto = flight['cityTo']
        cityfrom = flight['cityFrom']
        price = flight['price']
        link = flight['deep_link']
        # Check if we already have the city - if yes, skip, if not add
        # To nested dictionary
        if cityto in flight_matches == True:
            pass
        else:
            flight_matches[cityto]['price'] = [price]
            flight_matches[cityto]['flight'] = [link]

    for flight in flight2['data']:
        cityto = flight['cityTo']
        cityfrom = flight['cityFrom']
        price = flight['price']
        link = flight['deep_link']
        # If you ask for a key that isn't in the dictionary you get an error
        try:
            if len(flight_matches[cityto]['price']) == 1:
                flight_matches[cityto]['price'].append(price)
                flight_matches[cityto]['flight'].append(link)
        except:
            pass

    return flight_matches


# Return the result city and price
def get_itinerary(flight_type,city1,city2,date_from,date_to=None):

    # Extract user defined info for input
    flight1=get_flights(flight_type,city1,date_from,date_to=None)
    flight2=get_flights(flight_type,city2,date_from,date_to=None)
    flight_matches = flight_output(flight1, flight2)
    # print(len(flight_matches))

    # Get the final output
    total_prices = {}

    for city, f_info in flight_matches.items():
        for key in f_info:
            if len(f_info[key]) == 2 and key == 'price':
                total = sum(f_info[key])
                total_prices[city] = total

    min_price = min(total_prices, key=total_prices.get)

    #Links to actual flights
    link1 = flight_matches[min_price]['flight'][0]
    link2 = flight_matches[min_price]['flight'][1]

    return {'City': min_price, 'Price': total_prices[min_price], city1 :link1, city2:link2}

# One call is to collect data, the other one posts it
# First time we say methods, next only method, order doesn't matter
@app.route('/', methods=['GET'])
def home():
    return render_template("selector.html")

@app.route('/trip', methods=['GET','POST'])
def index():
    if request.method == 'GET':
        template = request.args.get('type')
        return render_template(f"{template}.html")
    else:
        flight_type = request.form['flight_type']
        city1 = request.form['city1']
        city2 = request.form['city2']
        date_from = request.form['date_from']
        date_to = request.form['date_to']
        dict = get_itinerary(city1,city2,date_from,date_to)
        return render_template("results.html", result = dict)


#This means you are running a program
if __name__ == "__main__":
    app.run(debug=True)

#runtime.txt
# Go back to virtual environment when using flask
