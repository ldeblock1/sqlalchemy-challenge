# Import the dependencies.
from flask import Flask, jsonify
import selenium
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
import pandas as pd
import numpy as np
#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:////Users/lucasdeblock/Desktop/BootCampActivities/Module_10_Challenge/Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
# Home page
@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/2010-01-01"
        f"/api/v1.0/2010-01-01/2010-01-31"
    )

recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

one_year_ago = dt.datetime.strptime(recent_date[0], '%Y-%m-%d') - dt.timedelta(days=365)

@app.route("/api/v1.0/precipitation")
def precipitation():

    # Starting from the most recent data point in the database. 
    sel = [Measurement.date, Measurement.prcp]
    query_result = session.query(*sel).filter(Measurement.date >= one_year_ago).all()

    # Calculate the date one year from the last date in data set.
    precipitation_df = pd.DataFrame(query_result, columns=['Date', 'Precipitation'])
    precipitation_df.set_index('Date', inplace=True)

    # Perform a query to retrieve the data and precipitation scores
    precipitation_df = precipitation_df.sort_index()

    precipitation_dict = precipitation_df.to_dict(orient='records')


    return jsonify(precipitation_dict)

# Stations Route
@app.route("/api/v1.0/stations")
def stations():
    stations_data = session.query(Station).all()
    stations_list = []
    for station in stations_data:
        station_dict = {
            "station": station.station,
            "name": station.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "elevation": station.elevation
        }
        stations_list.append(station_dict)
    return jsonify(stations_list)




@app.route("/api/v1.0/tobs")
def tobs():
    most_active_stations = session.query(Measurement.station, func.count(Measurement.station))\
                              .group_by(Measurement.station)\
                              .order_by(func.count(Measurement.station).desc())\
                              .all()
                              
    most_active_station_id = most_active_stations[0][0]

    temperature_data = session.query(Measurement.date, Measurement.tobs)\
                              .filter(Measurement.station == most_active_station_id)\
                              .filter(Measurement.date >= one_year_ago).all()

    temperature_dict = {}
    for date, tobs in temperature_data:
        temperature_dict[date] = tobs

    return jsonify(temperature_dict)

def format_date(date_str):
    """Convert 'YYYY-MM-DD' to 'M/D/YY' to get past error"""
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.strftime('%-m/%-d/%y') if date_obj.day > 9 else date_obj.strftime('%-m/%d/%y')

    
from datetime import datetime
# Start Route
@app.route("/api/v1.0/<start>")
def start(start):

    start_date_obj = datetime.strptime(start, '%Y-%m-%d')
    formatted_start = start_date_obj.strftime('%m/%d/%y')


    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    results = session.query(*sel).filter(Measurement.date >= formatted_start).all()

    # Create a dictionary for TMIN, TAVG, TMAX
    temps = {'TMIN': results[0][0], 'TAVG': results[0][1], 'TMAX': results[0][2]}

    return jsonify(temps)

# Start/End Route
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    start_date_obj = datetime.strptime(start, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end, '%Y-%m-%d')
    formatted_start = start_date_obj.strftime('%m/%d/%y')
    formatted_end = end_date_obj.strftime('%m/%d/%y')

        # Create the selection list
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    # Create the query
    results = session.query(*sel).filter(Measurement.date >= formatted_start, Measurement.date <= formatted_end)
    
    # Create a dictionary for TMIN, TAVG, TMAX
    temps = {'TMIN': results[0][0], 'TAVG': results[0][1], 'TMAX': results[0][2]}

    return jsonify(temps)


if __name__ == '__main__':
    app.run(debug=True)
