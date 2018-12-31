import requests
# These 2 lines and the last 2 wrap your web page, you put the rest between
from flask import Flask, request, render_template #make sure this is upper case
app = Flask(__name__)
# In essence you are developing web pages
# The name of the app will be run on the flask server

# In essence here I just want the user to type in something for SFO

# Get data
def get_flights(city_from, date_from,date_to):
    params = {
    'flyFrom': city_from,
    'dateFrom': date_from,
    'dateTo':date_to
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

    return {'city': min_price, 'price': total_prices[min_price]}

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
