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

# All other variables are specified in the html, this one is fixed
# This is for showing results, not entirely sure how that works
partner = 'picky'

# Mafe a function for each part
# This is the location function

def get_locations_city(city_from):

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
    resp=requests.get('https://api.skypicker.com/locations', params = params_loc)
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
    resp=requests.get('https://api.skypicker.com/locations', params = params_loc)

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
def get_flights(city_from, date_from,date_to):

    city_id = get_locations_city(city_from)
    one_for_city = '1'

    #Ensure that date is captured in good formate
    #dt = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%y')
    df = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d/%m/%Y')
    dt = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%Y')

    # Use the code to get the flights
    params = {
    'flyFrom': city_id, #Use the code from the location match above
    'dateFrom': df,
    'dateTo':dt,
    'partner': partner,
    'one_for_city':one_for_city
    }
    # Get data
    resp=requests.get('https://api.skypicker.com/flights', params = params)
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
def get_itinerary(city1,city2,date_from,date_to):

    # Extract user defined info for input
    flight1=get_flights(city1,date_from,date_to)
    flight2=get_flights(city2,date_from,date_to)
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
@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template("index.html")
    else:
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
