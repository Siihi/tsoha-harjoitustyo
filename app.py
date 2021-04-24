from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv, urandom
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
db = SQLAlchemy(app)

@app.route('/')
def index():
    try:
        ids = session["user_id"]
    except:
        return render_template("index.html")
    flights = db.session.execute("SELECT date, duration, start_location, end_location, altitude_difference, distance, max_altitude, max_sink, max_raise, weather, notes FROM flights WHERE user_id =:ids AND visible =:visible ORDER BY date DESC LIMIT 3", {"ids": ids, "visible":1}).fetchall()
    if len(flights) < 1:
        info = "Ei lentoja"
    else:
        info = "Viimeisimmät lennot:"
    return render_template("index.html", flights=flights, info=info)

@app.route("/login", methods=["POST"])
def login():
    app.secret_key = getenv("SECRET_KEY")
    session["csrf_token"] = urandom(16).hex()
    username = request.form["username"]
    password = request.form["password"]
    result = db.session.execute("SELECT users.password, users.id FROM users WHERE username=:username", {"username":username})
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
    if len(username) < 5:
        return render_template("error.html", message="Käyttäjänimi on liian lyhyt")
    password = request.form["password"]
    if len(password) < 5:
        return render_template("error.html", message="Salasana on liian lyhyt")
    check = request.form["check"]
    if password == check:
        overlap = db.session.execute("SELECT 1 FROM users WHERE username=:username", {"username":username})
        if overlap.fetchone() == None:
            hash_value = generate_password_hash(password)
            db.session.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":username, "password":hash_value})
            db.session.commit()
            ids = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":username}).fetchone()
            db.session.execute("INSERT INTO userinfo (user_id, name, wing, level) VALUES (:user_id, :n, :n, :n)", {"user_id":ids[0], "n":"Ei löydy"})
            db.session.commit()
            return redirect("/")
        else:
            return render_template("error.html", message="Käyttäjä on jo olemassa")
    else:
        return render_template("error.html", message="Salasanat eivät täsmää")

@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    del session["csrf_token"]
    return redirect("/")

@app.route("/newflight")
def newflight():
    return render_template("addflight.html")

@app.route("/addflight", methods=["POST"])
def addflight():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    user = session["user_id"]
    date = request.form["date"]
    if date == '':
        return render_template("error.html", message="Päivämäärä puuttuu")
    time = request.form["time"]
    if time == '':
        return render_template("error.html", message="Alkuaika puuttuu")
    date = date + " " + time
    unend = request.form["duration"]
    if unend == '':
        return render_template("error.html", message="Lopetusaika puuttuu")
    timeforcalc = datetime.strptime(time, "%H:%M")
    endforcalc = datetime.strptime(unend, "%H:%M")
    duration = endforcalc - timeforcalc
    start_location = request.form["startlocation"]
    if start_location == '':
        return render_template("error.html", message="Lähtöpaikka puuttuu")
    end_location = request.form["endlocation"]
    if end_location == '':
        return render_template("error.html", message="Laskupaikka puuttuu")
    altitude_difference = request.form["altitudedifference"]
    if altitude_difference == '':
        altitude_difference = 0
    distance = request.form["distance"]
    if distance == '':
        distance = 0
    max_altitude = request.form["maxaltitude"]
    if max_altitude == '':
        max_altitude = 0
    max_sink = request.form["maxsink"]
    if max_sink == '':
        max_sink = 0
    max_raise = request.form["maxraise"]
    if max_raise == '':
        max_raise = 0
    weather = request.form["weather"]
    notes = request.form["notes"]
    share = request.form["share"]
    if share == '':
        return render_template("error.html", message="Jakamistiedot puuttuvat")
    db.session.execute("INSERT INTO flights (user_id, date, start_location, end_location, duration, altitude_difference, distance, max_altitude, max_sink, max_raise, weather, notes, share, visible) VALUES (:user_id, :date, :start_location, :end_location, :duration, :altitude_difference, :distance, :max_altitude, :max_sink, :max_raise, :weather, :notes, :share, :visible)", {"user_id":user, "date":date, "start_location":start_location, "end_location":end_location, "duration":duration, "altitude_difference":altitude_difference, "distance":distance, "max_altitude":max_altitude, "max_sink":max_sink, "max_raise":max_raise, "weather":weather, "notes":notes, "share":share, "visible":1})
    db.session.commit()
    return redirect("/")

@app.route("/removeflight")
def removeflight():
    return render_template("removeflight.html")

@app.route("/removeflightaction", methods=["POST"])
def removeflightaction():
    ids = session["user_id"]
    date = request.form["date"]
    if date == '':
        return render_template("error.html", message="Päivämäärä puuttuu")
    time = request.form["time"]
    if time == '':
        return render_template("error.html", message="Aika puuttuu")
    date = date + " " + time
    check = db.session.execute("SELECT 1 FROM flights WHERE date=:date", {"date":date})
    if check.fetchone() == None:
        return render_template("error.html", message="Lentoa ei löytynyt")
    else:
        db.session.execute("UPDATE flights SET visible=0 WHERE date=:date", {"date":date})
        db.session.commit()
        return redirect("/")

@app.route("/othersflights")
def othersflights():
    ids = session["user_id"]
    othersflights = db.session.execute("SELECT date, duration, start_location, end_location, altitude_difference, distance, max_altitude, max_sink, max_raise, weather, notes FROM flights WHERE share = :yes AND visible=:visible AND NOT user_id=:ids", {"yes":"yes", "visible":1, "ids":ids}).fetchall()
    return render_template("othersflights.html", flights=othersflights)

@app.route("/allflights")
def allflights():
    ids = session["user_id"]
    allflights = db.session.execute("SELECT date, duration, start_location, end_location, altitude_difference, distance, max_altitude, max_sink, max_raise, weather, notes FROM flights WHERE user_id =:ids AND visible=:visible", {"ids": ids, "visible":1}).fetchall()
    return render_template("othersflights.html", flights=allflights)

@app.route("/maintenance")
def maintenances():
    ids = session["user_id"]
    lastmaintenance = db.session.execute("SELECT date, name FROM maintenances WHERE user_id=:ids ORDER BY date DESC", {"ids":ids}).fetchone()
    notes = lastmaintenance[1]
    currentdate = datetime.now().date()
    try:
        calc = currentdate - lastmaintenance[0]
    except:
        return render_template("maintenance.html", need="Huoltoja ei löytynyt")
    comp = ""
    for i in str(calc):
        if i not in ["1","2","3","4","5","6","7","8","9","0"]:
            break
        else:
            comp += i
    comp = int(comp)
    if comp > 180:
        numberofdays = int(comp)
        need = f"Uusi huolto tarvitaan, {numberofdays} päivää viime huollosta"
    else:
        numberofdays = 180 - int(comp)
        need = f"Huoltoa ei tarvita, seuraava {numberofdays} päivän päästä"
    return render_template("maintenance.html", need=need, notes=notes)

@app.route("/addmaintenance")
def addmaintenance():
    return render_template("addmaintenance.html")

@app.route("/addmaintenancetodb", methods=["POST"])
def addmaintenancetodb():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    ids = session["user_id"]
    date = request.form["date"]
    if date is None:
        return render_template("error.html", message="Päivämäärä puuttuu")
    text = request.form["notes"]
    db.session.execute("INSERT INTO maintenances (user_id, date, name) values (:ids, :date, :name)", {"ids":ids, "date":date, "name":text})
    db.session.commit()
    return redirect("/maintenance")

@app.route("/userinfo")
def userinfo():
    ids = session["user_id"]
    info = db.session.execute("SELECT name, wing, level FROM userinfo WHERE user_id=:ids", {"ids":ids}).fetchone()
    return render_template("userinfo.html", info=info)
    
@app.route("/editinfo")
def editinfo():
    return render_template("editinfo.html")

@app.route("/addeditinfo", methods=["POST"])
def addeditinfo():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    ids = session["user_id"]
    name = request.form["name"]
    wing = request.form["wing"]
    level = request.form["level"]
    if name == '' and wing == '' and level == '':
        return render_template("error.html", message="Muutettavia tietoja ei ollut")
    elif name == '' and wing == '':
        db.session.execute("UPDATE userinfo SET level=:level WHERE user_id=:ids", {"level":level, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")
    elif wing == '' and level == '':
        db.session.execute("UPDATE userinfo SET name=:name WHERE user_id=:ids", {"name":name, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")
    elif name == '' and level == '':
        db.session.execute("UPDATE userinfo SET wing=:wing WHERE user_id=:ids", {"wing":wing, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")
    elif name == '':
        db.session.execute("UPDATE userinfo SET wing=:wing, level=:level WHERE user_id=:ids", {"wing":wing, "level":level, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")
    elif wing == '':
        db.session.execute("UPDATE userinfo SET name=:name, level=:level WHERE user_id=:ids", {"name":name, "level":level, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")
    elif level == '':
        db.session.execute("UPDATE userinfo SET name=:name, wing=:wing WHERE user_id=:ids", {"name":name, "wing":wing, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")
    else:
        db.session.execute("UPDATE userinfo SET name=:name, wing=:wing, level=:level WHERE user_id=:ids", {"name":name, "wing":wing, "level":level, "ids":ids})
        db.session.commit()
        return redirect("/userinfo")