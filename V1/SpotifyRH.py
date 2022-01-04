import spotipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix
import joblib

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
username = os.environ['USER_NAME']
redirect_uri = os.environ['REDIRECT_URI']

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)

sp = spotipy.Spotify(client_credentials_manager = auth_manager)

## Initiate SGDClassifier using the songs input initially at the start of the rabbit hole
def start(new_labelled, labelled_df, unlabelled_df):
	X = np.array(fetch_audio_features(new_labelled))
	y = new_labelled["rating"].to_list()

	## Retrieve the scaler and model, partial fit to the new labelled data, and dump it
	scaler = joblib.load("scaler.pkl")
	X = scaler.transform(X)
	
	if unlabelled_df.empty:
		model = SGDClassifier(loss='log')
		model.partial_fit(X, y, classes=np.unique(y))
	else:
		model = joblib.load("SGDClassifier.pkl")
		model.partial_fit(X, y)
		
	joblib.dump(model, "SGDClassifier.pkl")
	
	return get_recs(new_labelled["track_id"].to_list(), labelled_df, unlabelled_df)

## Searches for the songs input initially at the start of the rabbit hole
def search(tracks, artists):
	ids, titles, singers = [], [], []
	for track, artist in zip(tracks, artists):
		try: 
			result = sp.search(q='track: ' + track + ' artist: ' + artist, type='track')['tracks']['items'][0]
		except:
			print("Song not found.")
			return 1
		ids.append(result['id'])
		titles.append(result['name'])
		singers.append(result['artists'][0]['name'])
	
	return ids, titles, singers

## Converts the Spotify API's response to a dataframe
def convert_df(sp_result):
	track_name, track_id, artist, album, duration, popularity = ([] for i in range(6))

	for i, items in enumerate(sp_result):
		track_name.append(items['name'])
		track_id.append(items['id'])
		artist.append(items["artists"][0]["name"])
		duration.append(items["duration_ms"])
		album.append(items["album"]["name"])
		popularity.append(items["popularity"])

	df = pd.DataFrame({
		"track_name": track_name, 
		"album": album, 
		"track_id": track_id,
		"artist": artist,
		"popularity": popularity})
	
	return df

## Requests audio features for tracks from Spotify's API
def fetch_audio_features(df):
	track_ids = df['track_id'].to_list()
	audio_features = []

	## Search for the audio features
	for track_id in track_ids:
		audio_features += sp.audio_features(track_id)

	## Make a list of lists of audio features of each song to turn into a 2D array
	features_list = []
	for features in audio_features:
		features_list.append([
			features['acousticness'],
			features['danceability'],
			features['energy'],
			features['instrumentalness'],
			features['liveness'],
			features['loudness'],
			features['speechiness'],
			features['tempo'],
			features['valence'],
		])
		
	return features_list

## Request songs from Spotify's API, predict how much the user will like them, and return the top 5 along with all other unlabelled songs
def get_recs(track_ids, labelled_df, unlabelled_df):
	model = joblib.load("SGDClassifier.pkl")
	sp_list = (sp.recommendations(seed_tracks=[track_ids[0]], limit=100)['tracks'])
	
	## Remove duplicates and songs the user has already labelled
	df = convert_df(sp_list).merge(unlabelled_df, how='outer', indicator=False).drop_duplicates()
	common_df = df.merge(labelled_df, how='inner', indicator=False)
	df = pd.concat([df, common_df]).drop_duplicates(subset=['track_id'], keep=False)
	
	## Predict on the new songs' audio features using the SGDClassifier
	features = np.array(fetch_audio_features(df))
	scaler = joblib.load("scaler.pkl")
	features = scaler.transform(features)
	
	predictions = model.predict(features)
	
	recs_df = pd.DataFrame({
		"track_id": df['track_id'],
		"title": df['track_name'],
		"artist": df['artist'],
		"predicted rating": predictions.tolist()
	})
	recs_df.sort_values(by=["predicted rating"], ascending=False, inplace=True)
	unlabelled_df = recs_df[:len(recs_df) // 2]["track_id"]
	recs_df = recs_df.head(5)
	
	return recs_df, unlabelled_df

## Returns the accuracy score of the classifier predictions on the set of tracks labelled by the user
def accuracy(labelled):
	model = joblib.load("SGDClassifier.pkl")
	scaler = joblib.load("scaler.pkl")
	
	audio_features = np.array(fetch_audio_features(labelled))
	X = scaler.transform(audio_features)
	
	y_true = labelled['rating'].to_list()
	y_pred = model.predict(X)
	
	score = model.score(X, y_true)
	print('Confusion matrix:\n', confusion_matrix(y_true=y_true, y_pred=y_pred))
	return score