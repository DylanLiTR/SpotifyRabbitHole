from flask import Flask, g, render_template, request, make_response
from SpotifyRH import start, search, accuracy
import sqlite3
import pandas as pd

DATABASE = 'database.db'

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
	cur = get_db().cursor()
	
	#cur.execute("DROP TABLE IF EXISTS labelled")
	#cur.execute("DROP TABLE IF EXISTS unlabelled")
	cur.execute("DROP TABLE IF EXISTS accuracy")
	
	cur.execute('''
	CREATE TABLE IF NOT EXISTS labelled(
		track_id VARCHAR(64) UNIQUE,
		rating INT
	)
	''')
	cur.execute('''
	CREATE TABLE IF NOT EXISTS unlabelled(
		track_id VARCHAR(64) UNIQUE,
		track_name VARCHAR(128),
		artist VARCHAR(64)
	)
	''')
	cur.execute('''
	CREATE TABLE IF NOT EXISTS accuracy(
		score FLOAT
	)
	''')
	
	return render_template("index.html")

@app.route("/confirm", methods=["GET", "POST"])
def confirm():
	if request.method == "POST":
		title = request.form.get("title")
		artist = request.form.get("artist")
		
		track_id, title, artist = search(title, artist)
		
	return render_template("confirm.html", track_id=track_id, title=title, artist=artist)

@app.route("/rabbithole", methods=["GET", "POST"])
def rabbithole():
	if request.method == "POST":
		db = get_db()
		cur = db.cursor()
		
		## Retrieve the form input data and append it to the labelled SQLite table
		track_id = request.form.get("track_id")
		rating = int(request.form["option"])
		
		## Store new labelled track in the SQLite table
		try:
			cur.execute("INSERT INTO labelled (track_id, rating) VALUES (?, ?)", (track_id, rating))
		except:
			pass
		
		## Retrieve all labelled and unlabelled tracks in the form of a dataframe
		labelled = pd.read_sql('SELECT track_id, rating FROM labelled', db)
		unlabelled = pd.read_sql('SELECT track_id, track_name, artist FROM unlabelled', db)
		
		## Find recommendations, new dataframe of unlabelled tracks, and updated model
		rec, unlabelled = start(track_id, rating, labelled['track_id'], unlabelled)
		
		## Update the unlabelled tracks in the SQlite table
		unlabelled.to_sql(name='unlabelled', con=db, if_exists='replace', index=False)
		
		## Insert the current accuracy score of the classifier
		cur.execute("INSERT INTO accuracy (score) VALUES (?)", (accuracy(labelled),))
		
		track_id = rec['track_id'].values[0]
		title = rec['track_name'].values[0]
		artist = rec['artist'].values[0]
		
	return render_template("rabbithole.html", track_id=track_id, title=title, artist=artist)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()