#!/bin/python3

# ---- Imports
import sqlite3, folium, json, os, requests, urllib, random
import pandas as pd
import geopandas as gpd
from datetime import datetime

"""
BACK-END NOTES / HOW IT WORKS

* End user supplies address in HTML form
* Lat / Lon coordinates are calculated
* Datetime, Address, Lat, Lon pushed to database

* Base map generated
* For each location, marker dropped on map
* Map saved as HTML file 
"""

# ---- SQL helpers
def init_db():
      """
      Builds Outreach DB based on schema file (or resets the DB if it already exists)
      """

      connection = sqlite3.connect('./outreach.db')

      with open('schema.sql') as f:
            connection.executescript(f.read())

      connection.close()


def render_geo_data(address, precinct_data, outreach_type):
      """
      Translates address to lat / lon and pushes to database
      """

      try:
            lat, lon = get_coordinates(address)
      except:
            lat, lon = 'ERROR', 'ERROR'

      push_to_db(address, lat, lon, precinct_data, outreach_type)


def push_to_db(address, lat, lon, precinct_data, outreach_type):
      """
      Adds user data to database
      """

      with sqlite3.connect('./outreach.db') as connection:
            cur = connection.cursor()

            cur.execute("""
                        INSERT INTO outreach (address, latitude, longitude, precinct, outreach_type) 
                        VALUES (?, ?, ?, ?, ?)""", (address, lat, lon, precinct_data, outreach_type))


def db_to_dataframe():
      """
      Converts SQL table to Pandas DataFrame
      """

      with sqlite3.connect('./outreach.db') as connection:
            data = pd.read_sql('select * from outreach', connection)

            data['created'] = pd.to_datetime(data['created'])
            data['show_date'] = data['created'].apply(lambda x: datetime.strftime(x, '%m/%d/%Y'))
            
            return data


def get_all_precincts():
      """
      Aggregates precinct geography and counts from outreach.db
      """

      import warnings
      warnings.filterwarnings('ignore')

      # --- GeoData
      # Read shapefile as GeoPandas DataFrame
      geo_data = get_geo()

      # Add ID column
      geo_data['id'] = [0] * len(geo_data)
      
      # Isolate ID and Precinct columns
      geo_data = geo_data.loc[:, ['id', 'PRECINCT']]
      
      # Transpose all column names to lower
      geo_data.columns = [x.lower() for x in geo_data.columns]

      # --- Form data
      # All user input from form (ID and Precinct columns only)
      base_data = db_to_dataframe().loc[:, ['id', 'precinct']]

      # Aggregate by precinct number (simple count)
      base_data = base_data.groupby('precinct').count().reset_index()
      
      # Convert precinct values to strings (for merging)
      base_data['precinct'] = base_data['precinct'].astype(str)

      # Merge geo data and user input data
      all_data = base_data.merge(geo_data, on=['precinct', 'id'], how='outer')
      all_data = all_data.sort_values(by='id', ascending=False).reset_index(drop=True)

      return all_data


# ---- Mapping helpers
def get_geo():
      """
      Read in shapefile as Pandas DataFrame
      """

      shape = './shapes/ELECTION_PRECINCTS.shp'
      
      return gpd.read_file(shape)


def get_coordinates(address):
      """
      Address => String, e.g., `450 Jane Stanford Way, Stanford, CA 94305`
      """

      # Call to OpenStreetMap
      call = 'https://nominatim.openstreetmap.org/search/' + \
            urllib.parse.quote(address) + '?format=json'

      # Make request + pull JSON information
      r = requests.get(call).json()

      # Return latitude and longitude
      try:
            return r[0]['lat'], r[0]['lon']
      except:
            return "ERROR", "ERROR"


def get_precinct(lat, long):
      """
      
      """

      pass


def aggregate_data(dev=True, key=None):
      
      geo = get_geo()
      
      if dev:
            outreach_data = fake_data()
      else:
            outreach_data = get_all_precincts()

      outreach_data.columns = [x.upper() for x in outreach_data.columns]

      return geo.merge(outreach_data, on='PRECINCT')


def fake_data():
      """
      DEVELOPMENTAL FUNCTION
      """

      import warnings
      warnings.filterwarnings('ignore')

      real_data = get_all_precincts()

      for ix, val in enumerate(real_data['precinct']):

            new_val = random.randint(1, 1000)

            real_data['id'][ix] = new_val

      real_data = real_data.sort_values(by='id', ascending=False).reset_index(drop=True)
      
      return real_data


def map_function_all_outreach(dev=True):
      """
      Automated updating function ... this groups the outreach
      data by type, and pushes it to a Choropleth map of the city
      """

      print('\n** Data incoming from database **\n')

      if not dev:
            # Isolate data from SQLite database
            outreach_data = get_all_precincts()
      else:
            outreach_data = fake_data()

      # Read in GEOJson file as dictionary
      dh = get_geo()

      # Aggreagate data for hover functions
      toolkit = aggregate_data(dev)

      print('\n** Writing updated map **\n')

      # Instantiate map
      g_map = folium.Map(location=[37.5630, -122.3255], 
                         zoom_start=11)

      folium.Choropleth(geo_data=toolkit,
                        data=toolkit,
                        columns=['PRECINCT', 'ID'],
                        key_on='feature.properties.PRECINCT',
                        fill_color='YlGnBu',
                        fill_opacity=0.75,
                        line_color='grey',
                        line_opacity=0.5,
                        legend_name='Red Bridge Outreach').add_to(g_map)

      def style_function(x): return {'fillColor': '#ffffff',
                                     'color': '#000000',
                                     'fillOpacity': 0.1,
                                     'weight': 0.1}


      def highlight_function(x): return {'fillColor': '#000000',
                                          'color': '#000000',
                                          'fillOpacity': 0.50,
                                          'weight': 0.1}


      NIL = folium.features.GeoJson(toolkit,
                                    style_function=style_function,
                                    control=False,
                                    highlight_function=highlight_function,
            
      tooltip=folium.features.GeoJsonTooltip(fields=['PRECINCT', 'ID'],
                                             aliases=['Precinct: ', 'Value: '],
                                             style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
            )
            )

      g_map.add_child(NIL)
      g_map.keep_in_front(NIL)
      folium.LayerControl().add_to(g_map)

      # Save map in the templates folder
      g_map.save(outfile=os.path.join('templates/voter_outreach_map.html'))


def map_function_specific_outreach(dev, key):
      """
      
      """

      pass
