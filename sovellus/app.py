from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

@app.route('/')
def index():
    #add so that a user can only see their own flights, user_id = session_id?
    #use this "WHERE user_id =:ids", {"ids": ids}).fetchall()"
    try:
        ids = session["user_id"]
    except:
        return render_template("index.html")
    flights = db.session.execute("SELECT date, duration, start_location, end_location, altitude_difference, distance, max_altitude, max_sink, max_raise, weather, notes FROM flights WHERE user_id =:ids", {"ids": ids}).fetchall()
    return render_template("index.html", flights=flights)

@app.route("/login", methods=["POST"])
def login():
    app.secret_key = getenv("SECRET_KEY")
    username = request.form["username"]
    password = request.form["password"]
    result = db.session.execute("SELECT password, id FROM users WHERE username=:username", {"username":username})
    user = result.fetchone()
    if user == None:
        return render_template("error.html", message="Käyttäjää ei löytynyt")
    else:
        hash_value = user[0]
        if check_password_hash(hash_value, password):
            session["user_id"] = user[1]
            session["username"] = username
            return redirect("/")
        else:
            return render_template("error.html", message="Salasana väärin")

@app.route("/newuser")
def newuser():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    overlap = db.session.execute("SELECT 1 FROM users WHERE username=:username", {"username":username})
    if overlap.fetchone() == None:
        hash_value = generate_password_hash(password)
        db.session.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":username, "password":hash_value})
        db.session.commit()
        return redirect("/")
    else:
        return render_template("error.html", message="Käyttäjä on jo olemassa")

@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/")

@app.route("/newflight")
def newflight():
    return render_template("addflight.html")

@app.route("/addflight", methods=["POST"])
def addflight():
    user = session["user_id"]
    date = request.form["date"]
    time = request.form["time"]
    date = date + " " + time
    unend = request.form["duration"]
    timeforcalc = datetime.strptime(time, "%H:%M")
    endforcalc = datetime.strptime(unend, "%H:%M")
    duration = endforcalc - timeforcalc
    start_location = request.form["startlocation"]
    end_location = request.form["endlocation"]
    altitude_difference = request.form["altitudedifference"]
    distance = request.form["distance"]
    max_altitude = request.form["maxaltitude"]
    max_sink = request.form["maxsink"]
    max_raise = request.form["maxraise"]
    weather = request.form["weather"]
    notes = request.form["notes"]
    share = request.form["share"]
    db.session.execute("INSERT INTO flights (user_id, date, start_location, end_location, duration, altitude_difference, distance, max_altitude, max_sink, max_raise, weather, notes, share) VALUES (:user_id, :date, :start_location, :end_location, :duration, :altitude_difference, :distance, :max_altitude, :max_sink, :max_raise, :weather, :notes, :share)", {"user_id":user, "date":date, "start_location":start_location, "end_location":end_location, "duration":duration, "altitude_difference":altitude_difference, "distance":distance, "max_altitude":max_altitude, "max_sink":max_sink, "max_raise":max_raise, "weather":weather, "notes":notes, "share":share})
    db.session.commit()
    return redirect("/")