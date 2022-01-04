import spotipy
from sqlite3 import connect
import numpy as np
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.metrics import confusion_matrix
from river import metrics
import pandas as pd
import os
import joblib

DATABASE = 'SavedDatabase.db'

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
username = os.environ['USER_NAME']
redirect_uri = os.environ['REDIRECT_URI']

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)

sp = spotipy.Spotify(client_credentials_manager = auth_manager)

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

conn = connect(DATABASE)

model = joblib.load("model.pkl")

labelled_df = pd.read_sql('SELECT track_id, rating FROM labelled', conn)

X = pd.DataFrame(fetch_audio_features(labelled_df))
y_true = labelled_df['rating'].to_list()

y_pred = list(map(str, model.predict_many(X).to_list()))

metric = metrics.Accuracy()
for yt, yp in zip(y_true, y_pred):
	score = metric.update(yt, yp)

print('Confusion matrix:\n', confusion_matrix(y_true=y_true, y_pred=y_pred))
print(score)