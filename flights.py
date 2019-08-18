import requests
# These 2 lines and the last 2 wrap your web page, you put the rest between
from flask import Flask, request, render_template, redirect
# Here we in essence are importing the database
from database import db_session
# Don't have this table now!
#from models import Location # Get the table schema

#make sure this is upper case
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
            'flyFrom':city_id, #Use the code from the location match above
            'dateFrom': df,
            'dateTo':df,
            'one_for_city':'1',
            'limit':limit
        }
    else:
        dt = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d/%m/%Y')
        params = {
            'flyFrom':city_id, #Use the code from the location match above
            'dateFrom': df,
            'dateTo':df,
            'return_from':dt,
            'return_to':dt,
            'flight_type':'round',
            'sort':'price'
        }

    # Get data
    resp=requests.get('https://kiwicom-prod.apigee.net/v2/search?', params = params, headers = headers)
    # Parse json into dictionary
    fl=resp.json()
    # Put into dataframe
    results = pd.DataFrame(fl['data'], columns=['cityFrom','cityTo','deep_link','price'])

    return results

# This actually extracts the flight prices for each desitnation city
# Step 2: Add the deeplink for the flight

#Make sure we get the cheapeast price per location

def flight_output_table(flight1, flight2):
    # 1. Get one price per location
    # 2. Ensure we remove any duplicates in the return results
    # 3. Combine data sets
    # 4. Get the total price for the journey
    # 5. Sort the results
    # N.B it appears like there are actually are duplicates

    # 1.
    min_price = flight1.groupby(['cityTo','cityFrom'], as_index=False)['price'].min()
    min_price2 = flight2.groupby(['cityTo','cityFrom'], as_index=False)['price'].min()

    # 2.
    filtered_f1 = flight1[flight1.price.isin(min_price['price'])].drop_duplicates()
    filtered_f2 = flight2[flight2.price.isin(min_price2['price'])].drop_duplicates()

    # 3.
    final = pd.merge(filtered_f1, filtered_f2[['cityFrom','cityTo','price','deep_link']], how='inner',on='cityTo', sort=False)
    # 4.
    final['total']=final['price_x'] + final['price_y']

    # 5.
    return final.sort_values(by='total')

# Return the result city and price
# Get full list of results and a pretty dataframe at the end!
def get_itinerary(flight_type,city1,city2,date_from,date_to=None):

    # Extract user defined info for input
    flight1=get_flights(flight_type,city1,date_from,date_to)
    flight2=get_flights(flight_type,city2,date_from,date_to)
    flight_matches = flight_output_table(flight1, flight2)

    #Rename columns in output table
    your_city = flight_matches.cityFrom_x.unique().tolist()
    their_city = flight_matches.cityFrom_y.unique().tolist()
    flight_matches.rename(columns={'deep_link_x':your_city[0],
                                   'deep_link_y':their_city[0],
                                   'cityTo':"City To",
                                   'total':"Total Price"},
                                    inplace=True)

    #Drop unnecessary columns
    clean = flight_matches.drop(['cityFrom_x', 'cityFrom_y','price_x','price_y'], axis=1)

    return clean

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
        dict = get_itinerary(flight_type,city1,city2,date_from,date_to)
        return render_template("results.html", column_names=dict.columns.values,
                        row_data=list(dict.values.tolist()),
                        link_column=["City To","Total Price"],
                        df=dict,
                        zip=zip)


#This means you are running a program
if __name__ == "__main__":
    app.run(debug=True)

#runtime.txt
# Go back to virtual environment when using flask
