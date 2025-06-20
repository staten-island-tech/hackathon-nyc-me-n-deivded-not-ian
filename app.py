from flask import Flask, render_template, request, session, redirect
import folium
import requests
import os
import random

app = Flask(__name__)

app.secret_key = os.urandom(32)

@app.route('/')
def index():
    session.clear()
    return render_template("index.html")

@app.route('/game', methods=['GET', 'POST'])
def game():
    if "index" not in session:
        session["index"] = 0
        session["landmarks"] = {}
        session["correct_guess"] = False
        session["score"] = 0
        session["previous_landmark"] = {}
        session["current_landmark"] = {}
        session["offsets"] = []

    if session.get("index") >= 15:
        return redirect('/endscreen')
    else:
        if request.method == "POST":
            borough_guess = request.form.get("guess").strip().upper()
            if "borough" in session.get("current_landmark"):
                if borough_guess == session["current_landmark"]["borough"]:
                    session["correct_guess"] = True
                    session["score"] += 1
                else:
                    session["correct_guess"] = False
        
            session["landmarks"][session["current_landmark"]["objectid"]] = {
                "coords": [pair[::-1] for pair in session["current_landmark"]["the_geom"]["coordinates"][0][0]],
                "name": session["current_landmark"]["lpc_name"]
            }

            return redirect("/game")

        session["index"] += 1

        i = 0
        while True:
            offset = random.randint(0, 999)
            i += 1
            if offset not in session["offsets"]:
                session["offsets"].append(offset)
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
            try: 
                landmark = landmark[0]
                session["previous_landmark"] = session["current_landmark"]
                session["current_landmark"] = {
                  "objectid": landmark["objectid"],
                  "the_geom": {
                      "type": landmark["the_geom"]["type"],
                      "coordinates": landmark["the_geom"]["coordinates"]
                    },
                  "address": landmark["address"],
                  "lpc_name": landmark["lpc_name"],
                  "borough": landmark["borough"],
                  "url_report": landmark["url_report"]
                }
            except KeyError as error:
                return redirect('/game')
            else:
                nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

                if session["landmarks"]:
                    for recalled_landmark in session["landmarks"].values():
                        coords = recalled_landmark["coords"]
                        name = recalled_landmark["name"]

                        folium.Polygon(
                            locations=coords,
                            color='blue',
                            fill=True,
                            fill_color='lightblue',
                            popup=name
                        ).add_to(nyc_map)

                        marker_lat = sum([point[0] for point in coords]) / len(coords)
                        marker_lon = sum([point[1] for point in coords]) / len(coords)

                        folium.Marker(
                            location=[marker_lat, marker_lon],
                            popup=name
                        ).add_to(nyc_map)

                folium_html = nyc_map._repr_html_()
                return render_template("game.html", current_landmark=session.get("current_landmark"), folium_html=folium_html, previous_landmark=session.get("previous_landmark"), index=session.get("index"), correct_guess=session.get("correct_guess"), score=session.get("score"))
            
@app.route('/endscreen')
def endscreen():
    if "score" in session:
        return render_template("endscreen.html", score=session["score"])
    else:
        return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)