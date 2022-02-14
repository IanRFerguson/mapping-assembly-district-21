#!/bin/python3

"""
About this App

This web app allows the end user to track locations
in which voter outreach has occurred. This example uses
fake outreach data for demonstrative purposes.

Ian Richard Ferguson
"""


# ---- Imports
from flask import Flask, render_template, redirect, url_for, request
from helper import *
import os


print('\n ** App running **\n')
app = Flask(__name__)

DEV = True

if DEV:
      print('\n** RUNNING IN DEV MODE **\n')

if not os.path.exists('./outreach.db'):
      print('\n=== Initializing Database ===\n')
      init_db()


# --- Application architecture
@app.route('/', methods=['GET', 'POST'])
def index():      
      return render_template('index.html')


@app.route('/outreach', methods=['GET', 'POST'])
def outreach():

      # If form submitted, render longitude/latitude and push to database
      if request.method == 'POST':

            # Information from form
            address = request.form['address']
            city = request.form['city']
            zipcode = request.form['zipcode']
            precincts = request.form['precincts']
            outreach_type = request.form['outreach_type']

            # E.g., 450 Jane Stanford Way, Stanford, CA 94305
            clean = f'{address}, {city}, CA {zipcode}'

            # Get coordinates and push to database
            render_geo_data(clean, precincts, outreach_type)

            # Add marker to Folium HTML map
            try:
                  map_function_all_outreach(DEV)
            except Exception as e:
                  print(f'\n** {e} ** \n')

            if address == '':
                  clean = f'{outreach_type} @ {precincts}'

            return redirect(url_for('success', value=clean))

      return render_template('outreach.html')


@app.route('/success/<value>', methods=['GET'])
def success(value): 
      return render_template('success.html', value=value)


# ---- Maps
@app.route('/maps', methods=['GET', 'POST'])
def maps():
    return render_template('maps.html')


@app.route('/locations', methods=['GET', 'POST'])
def voter_outreach():
    return render_template('voter_outreach_map.html')


# --- Developer functions (these should be more hidden in production)
@app.route('/dev', methods=['GET', 'POST'])
def dev():

      data = db_to_dataframe()

      return render_template('dev.html', data=data.to_html())


@app.route('/reset_db', methods=['POST'])
def reset_db():

      print('\n ** DEVELOPER FUNCTION TRIGGERED **\n')
      print('\n === Resetting database ===\n')

      init_db()
      map_function_all_outreach(DEV)

      return render_template('dev.html')


@app.route('/reset_all_maps', methods=['POST'])
def reset_all_maps():

      map_function_all_outreach(DEV)

      return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
