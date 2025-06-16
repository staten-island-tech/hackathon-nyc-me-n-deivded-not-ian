from flask import Flask, render_template, request, session, redirect, url_for
import folium
import requests
import os
import random

app = Flask(__name__)

app.secret_key = os.urandom(32)


@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get("index") == None:
        session["index"] = 0
        session["landmarks"] = []
        session["correct_guess"] = False
        session["score"] = 0
        session["previous_landmark"] = {}

    if session["index"] >= 25:
        print("just doing this to avoid the error lol") #handle game end condition
    else:
        if request.method == "POST":
            borough_guess = request.form.get("guess").strip()
            if borough_guess == landmark["borough"]:
                session["correct_guess"] = True
                session["score"] += 1
            else:
                session["correct_guess"] = False
        
            session["index"] += 1
            session["landmarks"].append(landmark["objectid"])
            session["previous_landmark"] = session["current_landmark"]
            session["current_landmark"] = {}

            return redirect("/")

        while True:
            offset = random.randint(0, 999)
            if (offset + 1) not in session["landmarks"]:
                break
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
            session["current_landmark"] = landmark
            #folium to load EVERY landmark
            return render_template("index.html", landmark=landmark, folium_html=folium_html, previous_landmark=session.get("previous_landmark"))
            

if __name__ == "__main__":
    app.run(debug=True)