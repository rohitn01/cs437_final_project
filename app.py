from flask import Flask, render_template, request, url_for, redirect
import requests
import json
import python_weather
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, timedelta

matplotlib.use('Agg')
plt.gcf().subplots_adjust(bottom=0.2)

zip_code = None
mile_goal = None
total_distance = 0
polylines = 0


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
async def home():
    global zip_code
    global mile_goal
    global total_distance

    if request.method == 'POST':
        zip = str(request.form['zip'])
        zip_code = zip
        client = python_weather.Client(format=python_weather.IMPERIAL)

        # fetch a weather forecast from a city
        weather = await client.find(zip)

        forecasts = []
        for f in weather.forecasts[2:]:
            dic = {}
            dic['date'] = f.date.strftime("%B %d, %Y")
            dic['sky_text'] = f.sky_text
            dic['temperature'] = f.temperature

            forecasts.append(dic)

        await client.close()

        if mile_goal is not None:
            return render_template('general.html', need_input=False, current_temp=weather.current.temperature, forecasts=forecasts, need_miles=False, miles=mile_goal,  met_goal=total_distance >= float(mile_goal), total_distance=total_distance, polyline=polylines)
        else:
            return render_template('general.html', need_input=False, current_temp=weather.current.temperature, forecasts=forecasts, need_miles=True, polyline=polylines)
    else:
        zip_code = None
        if mile_goal is not None:
            return render_template('general.html', need_input=True, need_miles=False, miles=mile_goal,  met_goal=total_distance >= float(mile_goal), total_distance=total_distance, polyline=polylines)
        else:
            return render_template('general.html', need_input=True, need_miles=True, polyline=polylines)


@app.route('/goal', methods=['GET', 'POST'])
async def goal():
    global zip_code
    global mile_goal

    if request.method == 'POST':
        miles = str(request.form['miles'])
        mile_goal = miles

        if zip_code is not None:
            client = python_weather.Client(format=python_weather.IMPERIAL)

            # fetch a weather forecast from a city
            weather = await client.find(zip_code)

            forecasts = []
            for f in weather.forecasts[2:]:
                dic = {}
                dic['date'] = f.date.strftime("%B %d, %Y")
                dic['sky_text'] = f.sky_text
                dic['temperature'] = f.temperature

                forecasts.append(dic)

            await client.close()

            return render_template('general.html', need_input=False, current_temp=weather.current.temperature, forecasts=forecasts, miles=miles, need_miles=False, met_goal=total_distance >= float(miles), total_distance=total_distance, polyline=polylines)
        else:
            return render_template('general.html', need_input=True, miles=miles, need_miles=False,  met_goal=total_distance >= float(miles), total_distance=total_distance, polyline=polylines)
    else:
        mile_goal = None
        if zip_code is not None:
            client = python_weather.Client(format=python_weather.IMPERIAL)

            # fetch a weather forecast from a city
            weather = await client.find(zip_code)

            forecasts = []
            for f in weather.forecasts[2:]:
                dic = {}
                dic['date'] = f.date.strftime("%B %d, %Y")
                dic['sky_text'] = f.sky_text
                dic['temperature'] = f.temperature

                forecasts.append(dic)

            await client.close()

            return render_template('general.html', need_input=False, current_temp=weather.current.temperature, forecasts=forecasts, need_miles=True, polyline=polylines)
        else:
            return render_template('general.html', need_input=True, need_miles=True, polyline=polylines)


def get_seven_days_date():
    date = datetime.today() - timedelta(days=7)

    return date.timestamp()


def get_df():
    col_names = ['id', 'type']
    activities = pd.DataFrame(columns=col_names)
    page = 1

    after = get_seven_days_date()
    global total_distance
    total_distance = 0
    while True:
        url = 'https://www.strava.com/api/v3/athlete/activities'
        headers = {'Authorization': 'Bearer 1891167db71be155c9baeac38e36e9b2a77f4e29'}
        params = {'page': page, 'after': after}

        r = requests.get(url, headers=headers, params=params)
        r = r.json()

        if (not r):
            break

        for x in range(len(r)):
            activities.loc[x + (page-1)*30, 'id'] = r[x]['id']
            activities.loc[x + (page-1)*30, 'type'] = r[x]['type']
            total_distance += r[x]['distance']
        page += 1
    total_distance /= 1609
    return activities


def activity_graph():
    df = get_df()
    x = df['type'].value_counts().plot(kind='bar', color=['blue', 'red', 'orange', 'green', 'purple', 'yellow'])
    plt.xticks(rotation=0)

    plt.savefig('static/plot.png')


def set_polyline():
    url = 'https://www.strava.com/api/v3/athlete/activities'
    headers = {'Authorization': 'Bearer 1891167db71be155c9baeac38e36e9b2a77f4e29'}

    r = requests.get(url, headers=headers)
    r = r.json()
    global polylines
    print(len(r))
    polylines = r[0]['map']['summary_polyline']


if __name__ == '__main__':
    activity_graph()
    set_polyline()
    app.run(debug=True, port='8888')
