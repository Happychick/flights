import requests
# These 2 lines and the last 2 wrap your web page, you put the rest between
from flask import Flask, request, render_template, redirect,jsonify
# Here we in essence are importing the database
from database import db_session
from werkzeug.exceptions import HTTPException
# Don't have this table now!
#from models import Location # Get the table schema

#make sure this is upper case
app = Flask(__name__)
# In essence you are developing web pages
# The name of the app will be run on the flask server

import json
import pandas as pd
from datetime import datetime
import time
from collections import defaultdict

# Set the variable for the API Key that allows us to tie to YOSO
apikey = '3Ahc4gcDjDjrHBJyHBm0cRzAC1LAxBAT'
# Set the limit otherwise the search won't work!
limit = '200'

# Mafe a function for each part
# This is the location function, that gets the airport code

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

# Add the new parameters here
def get_flights(flight_type,loc_params,date_from,date_to=None,currency=None,stop_over=None,dtime_from=None,
                dtime_to=None,atime_from=None,atime_to=None):

    fl_id= get_locations_city(loc_params)

    headers={'accept':'application/json','apikey':apikey}

    #Change the date format
    date_f = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d/%m/%Y')


    if flight_type =="One-way":
        # Use the code to get the flights
        params = {
            'fly_from':fl_id, #Use the code from the location match above
            'date_from': date_f,
            'date_to':date_f,
            'one_for_city':'1',
            'limit':limit,
            'curr':currency,
            #filters
            'max_stopovers':stop_over,
            'dtime_from':dtime_from,
            'dtime_to':dtime_to,
            'atime_from':atime_from,
            'atime_to':atime_to
        }
    else:
        date_t = datetime.strptime(date_to,'%Y-%m-%d').strftime('%d/%m/%Y')
        params = {
            'fly_from':fl_id, #Use the code from the location match above
            'date_from': date_f,
            'date_to':date_f,
            'return_from':date_t,
            'return_to':date_t,
            'flight_type':'round',
            #'limit':limit,
            'sort':'price',
            'curr':currency,
            #filters
            'max_stopovers':stop_over,
            'dtime_from':dtime_from,
            'dtime_to':dtime_to,
            'atime_from':atime_from,
            'atime_to':atime_to
        }

    # Get data, new API with correct data
    resp=requests.get('https://tequila-api.kiwi.com/v2/search?', params=params,headers=headers)

    # Parse json into dictionary
    fl=resp.json()

    results = pd.DataFrame(fl['data'], columns=['cityFrom','cityTo','deep_link','price'])

    #Adding total duration to the dataframe
    total_duration = []

    for i in range(len(fl['data'])):
        total = fl['data'][i]['duration']['total']
        total_duration.append(total)

    results['duration'] = total_duration


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

def time_output_table(flight1, flight2):
    # 1. Get one time per location
    # 2. Ensure we remove any duplicates in the return results
    # 3. Combine data sets
    # 4. Get the total time for the journey and convert it to a legible format
    # 5. Sort the results
    # N.B it appears like there are actually are duplicates

    # 1.
    min_time = flight1.groupby(['cityTo','cityFrom'], as_index=False)['duration'].min()
    min_time2 = flight2.groupby(['cityTo','cityFrom'], as_index=False)['duration'].min()

    # 2.
    filtered_f1 = flight1[flight1.duration.isin(min_time['duration'])].drop_duplicates()
    filtered_f2 = flight2[flight2.duration.isin(min_time2['duration'])].drop_duplicates()

    # 3.
    final = pd.merge(filtered_f1, filtered_f2[['cityFrom','cityTo','duration','deep_link']], how='inner',on='cityTo', sort=False)
    # 4.
    final['total_duration']=final['duration_x'] + final['duration_y']
    final['total_duration_time'] = [time.strftime("%H:%M", time.gmtime(i)) for i in final['total_duration']]

    # 5.
    return final.sort_values(by='total_duration')

# Return the result city and price
# Get full list of results and a pretty dataframe at the end!
def get_itinerary(flight_type,city1,city2,date_from,date_to=None,currency=None,stop_over=None,dtime_from=None,
                dtime_to=None,atime_from=None,atime_to=None,stop_over2=None,dtime_from2=None,
                dtime_to2=None,atime_from2=None,atime_to2=None):

    # Extract user defined info for input
    flight1=get_flights(flight_type,city1,date_from,date_to,currency,stop_over,dtime_from,
                    dtime_to,atime_from,atime_to)
    flight2=get_flights(flight_type,city2,date_from,date_to,currency,stop_over2,dtime_from2,
                    dtime_to2,atime_from2,atime_to2)
    flight_matches = flight_output_table(flight1, flight2)

    #Rename columns in output table
    your_city = flight_matches.cityFrom_x.unique().tolist()
    their_city = flight_matches.cityFrom_y.unique().tolist()
    flight_matches.rename(columns={'deep_link_x':your_city[0],
                                   'deep_link_y':their_city[0],
                                   'cityTo':"City To",
                                   'total':"Total Price"},
                                    inplace=True)

    # Drop unnecessary columns
    # For now I have put duration here, but we can put it back in by using the link column
    clean = flight_matches.drop(['cityFrom_x', 'cityFrom_y','price_x','price_y','duration'], axis=1)

    return clean

def get_shortest(flight_type,city1,city2,date_from,date_to=None,currency=None,stop_over=None,dtime_from=None,
                dtime_to=None,atime_from=None,atime_to=None,stop_over2=None,dtime_from2=None,
                                dtime_to2=None,atime_from2=None,atime_to2=None):

    # Extract user defined info for input
    flight1=get_flights(flight_type,city1,date_from,date_to,currency,stop_over,dtime_from,
                    dtime_to,atime_from,atime_to)
    flight2=get_flights(flight_type,city2,date_from,date_to,currency,stop_over2,dtime_from2,
                    dtime_to2,atime_from2,atime_to2)
    flight_matches = time_output_table(flight1, flight2)

    #Rename columns in output table
    your_city = flight_matches.cityFrom_x.unique().tolist()
    their_city = flight_matches.cityFrom_y.unique().tolist()
    flight_matches.rename(columns={'deep_link_x':your_city[0],
                                   'deep_link_y':their_city[0],
                                   'cityTo':"City To",
                                   'total_duration_time':"Total Duration"},
                                    inplace=True)

    #Drop unnecessary columns
    clean = flight_matches.drop(['cityFrom_x', 'cityFrom_y','duration_x','duration_y','price','total_duration'], axis=1)

    return clean

def get_closest(flight_type,city1,city2,date_from,date_to=None,currency=None,stop_over=None,dtime_from=None,
                dtime_to=None,atime_from=None,atime_to=None):

    # Extract user defined info for input
    flight1=get_flights(flight_type,city1,date_from,date_to,currency,stop_over,dtime_from,
                    dtime_to,atime_from,atime_to)
    flight2=get_flights(flight_type,city2,date_from,date_to,currency,stop_over,dtime_from,
                    dtime_to,atime_from,atime_to)
    flight_matches = flight_output_table(flight1, flight2)

    #Rename columns in output table
    your_city = flight_matches.cityFrom_x.unique().tolist()
    their_city = flight_matches.cityFrom_y.unique().tolist()
    flight_matches.rename(columns={'deep_link_x':your_city[0],
                                   'deep_link_y':their_city[0],
                                   'cityTo':"City To",
                                   'total':"Total Time"},
                                    inplace=True)

    #Drop unnecessary columns
    clean = flight_matches.drop(['cityFrom_x', 'cityFrom_y','price_x','price_y'], axis=1)

    return clean

# Register the error functions
# You just need to register the error handler, not create a class
@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # now you're handling non-HTTP exceptions only
    return render_template("500_generic.html", e=e), 500

# One call is to collect data, the other one posts it
# First time we say methods, next only method, order doesn't matter
@app.route('/', methods=['GET','POST'])
def index():
    template = request.args.get('type')
    if request.method == 'GET':
        #template = request.args.get('type')
        return render_template("selector.html")
    else:
        flight_type = request.form['flight_type']
        city1 = request.form['city1']
        city2 = request.form['city2']
        date_from = request.form['date_from']
        date_to = request.form['date_to']
        currency = request.form['currency']
        operation = request.form.get("operation")
        if operation == 'Cheapest':
            dict = get_itinerary(flight_type,city1,city2,date_from,date_to,currency)
        elif operation == 'Shortest':
            # Do function for calulcating shortest one
            dict = get_shortest(flight_type,city1,city2,date_from,date_to,currency)
        else:
            dict = get_closest(flight_type,city1,city2,date_from,date_to,currency)
        results = dict
        # We have to add a template for error handling
        return render_template("results.html", column_names=dict.columns.values,
        row_data=list(dict.values.tolist()),
        link_column=["City To","Total Price","Total Duration"],
        df=results,
        zip=zip)


# This means you are running a program
# Tells you were you are running it from
if __name__ == "__main__":
    app.run(debug=True)

#runtime.txt
# Go back to virtual environment when using flask
