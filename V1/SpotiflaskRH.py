from flask import Flask, g, render_template, request, make_response
from SpotifyRH import start, search, accuracy
import sqlite3
import pandas as pd

DATABASE = 'database.db'

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
	cur = get_db().cursor()
	cur.execute("DROP TABLE IF EXISTS labelled")
	cur.execute("DROP TABLE IF EXISTS unlabelled")
	cur.execute("DROP TABLE IF EXISTS accuracy")
	
	cur.execute('''
	CREATE TABLE IF NOT EXISTS labelled(
		track_id VARCHAR(64) UNIQUE,
		rating CHAR
	)
	''')
	cur.execute('''
	CREATE TABLE IF NOT EXISTS unlabelled(
		track_id VARCHAR(64) UNIQUE
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
		titles, artists = [], []
		for key, val in request.form.items():
			if key.startswith("track_name"):
				titles.append(val)
			elif key.startswith("artist"):
				artists.append(val)
		
		track_ids, titles, artists = search(titles, artists)
		
	return render_template("confirm.html", track_ids=track_ids, titles=titles, artists=artists, zip=zip)

@app.route("/rabbithole", methods=["GET", "POST"])
def rabbithole():
	if request.method == "POST":
		db = get_db()
		cur = db.cursor()
		
		## Retrieve the form input data and append it to the labelled SQLite table
		track_ids = request.form.getlist("track_ids")
		ratings = []
		for i in range(len(track_ids)):
			ratings.append(request.form['option' + str(i)])
		
		## Create a dataframe of the new labelled tracks and store it in the SQLite table
		new_labelled = pd.DataFrame({
			"track_id": track_ids,
			"rating": ratings
		}).sort_values(by=["rating"], ascending=False)
		try:
			new_labelled.to_sql(name='labelled', con=db, if_exists='append', index=False)
		except:
			pass
		
		## Retrieve all labelled and unlabelled tracks in the form of a dataframe
		labelled_df = pd.read_sql('SELECT track_id, rating FROM labelled', db)
		unlabelled_df = pd.read_sql('SELECT track_id FROM unlabelled', db)
		
		## Find recommendations, new dataframe of unlabelled tracks, and updated model
		recs_df, unlabelled_df = start(new_labelled, labelled_df['track_id'], unlabelled_df)
		
		## Update the unlabelled tracks in the SQlite table
		unlabelled_df.to_sql(name='unlabelled', con=db, if_exists='replace', index=False)
		
		## Insert the current accuracy score of the classifier
		cur.execute("INSERT INTO accuracy (score) VALUES (?)", (accuracy(labelled_df),))
		
		track_ids = recs_df['track_id'].to_list()
		titles = recs_df['title'].to_list()
		artists = recs_df['artist'].to_list()
		
	return render_template("rabbithole.html", track_ids=track_ids, titles=titles, artists=artists, zip=zip)

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