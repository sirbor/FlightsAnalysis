import os
import requests
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# aviationstack API access key
api_key = os.getenv("API_KEY")

# Function to get flight details
def get_flight_details(airport_code, flight_type, start_date, end_date):
    """
    Fetch flight details for a specific airport and flight type within a date range.

    :param airport_code: The IATA code of the airport (e.g., "ADD" for Bole International Airport).
    :param flight_type: The type of flight ("departure" or "arrival").
    :param start_date: The start date of the date range in YYYY-MM-DD format.
    :param end_date: The end date of the date range in YYYY-MM-DD format.
    :return: JSON data containing flight details.
    """
    url = f"http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": api_key,
        "arr_iata": airport_code,
        "type": flight_type,
        "flight_date": f"{start_date},{end_date}",
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data

# Function to get flight details for both airports
def get_airport_flight_details(airport_codes, flight_type, start_date, end_date):
    """
    Fetch flight details for multiple airports and a flight type within a date range.

    :param airport_codes: A list of airport IATA codes.
    :param flight_type: The type of flight ("departure" or "arrival").
    :param start_date: The start date of the date range in YYYY-MM-DD format.
    :param end_date: The end date of the date range in YYYY-MM-DD format.
    :return: A dictionary containing flight details for each airport.
    """
    airport_data = {}
    for airport_code in airport_codes:
        data = get_flight_details(airport_code, flight_type, start_date, end_date)
        airport_data[airport_code] = data
    return airport_data

# Function to fetch continent information for a country
def get_continent(country_code):
    """
    Fetch the continent information for a given country code using a REST API.

    :param country_code: The ISO 3166-1 alpha-3 country code.
    :return: The continent name.
    """
    url = f"https://restcountries.com/v3.1/alpha/{country_code}"
    response = requests.get(url)
    data = response.json()
    continent = data['continent'] if 'continent' in data else 'Unknown'
    return continent

# Function to categorize destinations by continent
def categorize_destinations_by_continent(data):
    """
    Categorize destinations of flights by continent.

    :param data: Flight data for multiple airports.
    :return: A defaultdict containing flight details categorized by airport and continent.
    """
    continents = defaultdict(list)
    for airport, airport_data in data.items():
        flights = airport_data.get('data', [])
        for flight in flights:
            arrival_info = flight.get('arrival', {})
            destination_country = arrival_info.get('iso_country')
            if destination_country:
                destination_continent = get_continent(destination_country)
                continents[(airport, destination_continent)].append(flight)
            else:
                continents[(airport, 'Unknown')].append(flight)
    return continents

try:
    # Define start and end dates for fetching flights (365 days from today)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Get flight details for both airports
    airport_codes = ["ADD", "NBO"]
    departure_data = get_airport_flight_details(airport_codes, "departure", start_date_str, end_date_str)
    arrival_data = get_airport_flight_details(airport_codes, "arrival", start_date_str, end_date_str)

    if departure_data and arrival_data:
        # Categorize destinations by continent
        destination_continents = categorize_destinations_by_continent(arrival_data)

        # Count flights to each continent for each airport
        continent_counts = defaultdict(int)
        for key, flights in destination_continents.items():
            airport, continent = key
            continent_counts[(airport, continent)] += len(flights)

        # Create DataFrame with proper columns
        continent_table = pd.DataFrame(list(continent_counts.items()), columns=['Airport_Continent', 'Number_of_Flights'])
        continent_table[['Airport', 'Continent']] = pd.DataFrame(continent_table['Airport_Continent'].tolist(), index=continent_table.index)
        del continent_table['Airport_Continent']

        # Pivot the DataFrame
        continent_table = continent_table.pivot_table(index='Airport', columns='Continent', values='Number_of_Flights', aggfunc='sum', fill_value=0)
        
        # Print the table
        print("Flights per Continent for each Airport:")
        print(continent_table)
    else:
        print("No data available for one or both airports.")
except Exception as e:
    print("An error occurred:", e)
