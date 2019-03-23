import requests
# These 2 lines and the last 2 wrap your web page, you put the rest between
from flask import Flask, request, render_template #make sure this is upper case
app = Flask(__name__)
# In essence you are developing web pages
# The name of the app will be run on the flask server

import json
import pandas as pd
from datetime import datetime

# All other variables are specified in the html, this one is fixed
# This is for showing results, not entirely sure how that works
partner = 'picky'

# Mafe a function for each part
# This is the location function

def get_locations_city(city_from):

    # Split string into list of variables
    loc = city_from.split(',')

    #Define variables
    city_from = loc[0]
    country = loc[1]

    # First get city info
    params_loc = {
        'term':city_from, #This is what will show in the search tab
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
    dt = datetime.datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%y')
    df = datetime.datetime.strptime(date_from, '%Y-%m-%d').strftime('%d/%m/%y')

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
def flight_output(flight1, flight2):
    flight_matches = {}

    for flight in flight1['data']:
        cityto = flight['cityTo']
        cityfrom = flight['cityFrom']
        price = flight['price']
        #print(cityfrom,cityto,price)
        try:
            if len(flight_matches[cityto]) > 1:
                pass
        except:
            flight_matches[cityto] = [price]

    for flight in flight2['data']:
        cityto = flight['cityTo']
        cityfrom = flight['cityFrom']
        price = flight['price']
        #print(cityfrom,cityto,price)
        try:
            if len(flight_matches[cityto]) == 1:
                flight_matches[cityto].append(price)
        except:
            pass

    return flight_matches

#Get link to flights
def get_links(city_from,min_price,date_from,date_to):
    # Parameters needed for deeplink
    params_loc = {'origin':city_from,
                  'destination':min_price,
                  'departure':date_from,
                  'return':date_to,
                  'affilid':'test',
                  'lang':'en'}

    # Extract links information
    resp=requests.get('http://www.kiwi.com/deep',params = params_loc)

    result = resp.url

    return result

# Return the result city and price
def get_itinerary(city1,city2,date_from,date_to):

    # Extract user defined info for input
    flight1=get_flights(city1,date_from,date_to)
    flight2=get_flights(city2,date_from,date_to)
    flight_matches = flight_output(flight1, flight2)
    # print(len(flight_matches))

    # Get the final output
    total_prices = {}

    for i in flight_matches:
        if len(flight_matches[i]) == 2:
            total_prices[i] = sum(flight_matches[i])

    min_price = min(total_prices, key=total_prices.get)

    #Links to actual flights
    link1 = get_links(city1,min_price,date_from,date_to)
    link2 = get_links(city2,min_price,date_from,date_to)

    return {'city': min_price, 'price': total_prices[min_price], 'Flight 1':link1, 'Flight 2':link2}

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
        results = get_itinerary(city1,city2,date_from,date_to)
        return str(results)


#This means you are running a program
if __name__ == "__main__":
    app.run(debug=True)

#runtime.txt
# Go back to virtual environment when using flask
