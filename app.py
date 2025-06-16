from flask import Flask, render_template, request, session, redirect
import folium
import requests
import os
import random

app = Flask(__name__)

app.secret_key = os.urandom(32)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/game', methods=['GET', 'POST'])
def game():
    if "index" not in session:
        session["index"] = 0
        session["landmarks"] = []
        session["correct_guess"] = False
        session["score"] = 0
        session["previous_landmark"] = {}
        session["current_landmark"] = {}

    if session.get("index") >= 25:
        return redirect('/endscreen')
    else:
        if request.method == "POST":
            borough_guess = request.form.get("guess").strip().upper()
            if borough_guess == session["current_landmark"]["borough"]:
                session["correct_guess"] = True
                session["score"] += 1
            else:
                session["correct_guess"] = False
        
            session["index"] += 1
            session["landmarks"].append(session["current_landmark"]["objectid"])
            session["previous_landmark"] = session["current_landmark"]
            session["current_landmark"] = {}

            return redirect("/game")

        i = 0
        while True:
            offset = random.randint(0, 999)
            i += 1
            if (offset + 1) not in session.get("landmarks"):
                break
            if i > 100:
                return render_template("error.html", error = "Could not generate random landmark.")
        try:
            response = requests.get(f"https://data.cityofnewyork.us/resource/buis-pvji.json?$limit=1&$offset={offset}&$select=objectid,the_geom,address,lpc_name,borough,url_report", timeout = 10)
            response.raise_for_status()       
            landmark = response.json()
        except requests.exceptions.HTTPError as http_error:
            return render_template("error.html", error = f"HTTP Error: {http_error}")
        except requests.exceptions.RequestException as request_error:
            return render_template("error.html", error = f"Request Error: {request_error}")
        except ValueError as json_error:
            return render_template("error.html", error = f"Invalid JSON: {json_error}")
        else:
            session["current_landmark"] = landmark[0]

            nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=13)
            #loading every previous location on a map
            for landmark_id in session["landmarks"]:
                try:
                    response = requests.get(f"https://data.cityofnewyork.us/resource/buis-pvji.json?$limit=1&$offset={landmark_id - 1}&$select=the_geom,lpc_name", timeout = 10)
                    response.raise_for_status()       
                    recalled_landmark = response.json()
                except requests.exceptions.HTTPError as http_error:
                    return render_template("error.html", error = f"HTTP Error: {http_error}")
                except requests.exceptions.RequestException as request_error:
                    return render_template("error.html", error = f"Request Error: {request_error}")
                except ValueError as json_error:
                    return render_template("error.html", error = f"Invalid JSON: {json_error}")
                else:
                    coords = [pair[::-1] for pair in recalled_landmark[0]["the_geom"]["coordinates"][0][0]]
                    name = recalled_landmark[0]["lpc_name"]

                    folium.Polygon(
                        locations=coords,
                        color='blue',
                        fill=True,
                        fill_color='lightblue',
                        popup=name
                    ).add_to(nyc_map)

                    lat = sum([point[0] for point in coords]) / len(coords)
                    lon = sum([point[1] for point in coords]) / len(coords)

                    folium.Marker(
                        location=[lat, lon],
                        popup=name
                    ).add_to(nyc_map)

            folium_html = nyc_map._repr_html_()
            return render_template("game.html", landmark=landmark, folium_html=folium_html, previous_landmark=session.get("previous_landmark"))
            
@app.route('/endscreen')
def endscreen():
    if "score" in session:
        return render_template("endscreen.html", score=session["score"])
    else:
        return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)