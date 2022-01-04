import spotipy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import confusion_matrix
from river import linear_model
from river import compose
from river import compat
from river import preprocessing
from river import multiclass
from river import optim
from river import metrics
import joblib

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
username = os.environ['USER_NAME']
redirect_uri = os.environ['REDIRECT_URI']

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)

sp = spotipy.Spotify(client_credentials_manager = auth_manager)

## Initiate model using the song input initially at the start of the rabbit hole
def start(track_id, rating, labelled_df, unlabelled_df):
	df = pd.DataFrame({"track_id": [track_id]})
	X = fetch_audio_features(df)

	## Retrieve the model, learn the new labelled data, and dump it
	if unlabelled_df.empty:
		scaler = preprocessing.StandardScaler()
		regression = multiclass.OneVsRestClassifier(linear_model.LogisticRegression(loss=optim.losses.BinaryFocalLoss()))
		model = scaler | regression
	else:
		model = joblib.load("model.pkl")
	
	pred = model.predict_one(X[0])
	model.learn_one(X[0], rating)
	print("Prediction:", pred)
	
	joblib.dump(model, "model.pkl")
	
	return get_recs(track_id, rating, labelled_df, unlabelled_df)

## Searches for the songs input initially at the start of the rabbit hole
def search(title, artist):
	try: 
		result = sp.search(q='track: ' + title + ' artist: ' + artist, type='track')['tracks']['items'][0]
	except:
		print("Song not found.")
		return 1
	
	return result['id'], result['name'], result['artists'][0]['name']

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
		audio_features.append(sp.audio_features(track_id))

	## Make a list of dictionaries of audio features of each song
	features_list = []
	wanted_features = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']
	for features in audio_features:
		features_list.append({key:features[0][key] for key in wanted_features})
		
	return features_list

## Request songs from Spotify's API, predict how much the user will like them, and return the top 5 along with all other unlabelled songs
def get_recs(track_id, rating, labelled_df, unlabelled_df):
	model = joblib.load("model.pkl")
	if rating > 3:
		sp_list = sp.recommendations(seed_tracks=[track_id], limit=100)['tracks']
	
		## Remove duplicates and songs the user has already labelled
		df = convert_df(sp_list).merge(unlabelled_df, how='outer', indicator=False).drop_duplicates()
		common_df = df.merge(labelled_df, how='inner', indicator=False)
		df = pd.concat([df, common_df]).drop_duplicates(subset=['track_id'], keep=False)
	else:
		df = unlabelled_df
	
	## Predict on the new songs' audio features using the SGDClassifier
	features = pd.DataFrame(fetch_audio_features(df))
	predictions = model.predict_many(features).to_list()
	
	rec_df = pd.DataFrame({
		"track_id": df['track_id'],
		"track_name": df['track_name'],
		"artist": df['artist'],
		"predicted rating": predictions
	})
	rec_df.sort_values(by=["predicted rating"], ascending=False, inplace=True)
	unlabelled_df = rec_df[["track_id", "track_name", "artist"]].iloc[1:]
	rec_df = rec_df.head(1)
	
	return rec_df, unlabelled_df

## Returns the accuracy score of the classifier predictions on the set of tracks labelled by the user
def accuracy(labelled):
	metric = metrics.Accuracy()
	model = joblib.load("model.pkl")
	
	X = pd.DataFrame(fetch_audio_features(labelled))
	print(X)
	
	y_true = labelled['rating'].to_list()
	y_pred = model.predict_many(X).to_list()
	
	print("True", y_true)
	print("Predicted", y_pred)
	for yt, yp in zip(y_true, y_pred):
		score = metric.update(yt, yp)
	
	print(confusion_matrix(y_true=y_true, y_pred=y_pred))
	
	return score.get()