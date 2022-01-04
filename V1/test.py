import spotipy
from sqlite3 import connect
import numpy as np
from spotipy.oauth2 import SpotifyClientCredentials
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
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

conn = connect(DATABASE)

model = SGDClassifier(loss="log")
scaler = joblib.load("scaler.pkl")

labelled_df = pd.read_sql('SELECT track_id, rating FROM labelled', conn)

X = scaler.transform(np.array(fetch_audio_features(labelled_df)))
y = labelled_df['rating'].to_list()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)

for i in range(0, len(X_train), 5):
	classes = np.unique(y_train) if i == 0 else None
	model.partial_fit(X_train[i:i+4], y_train[i:i+4], classes=classes)

y_pred = model.predict(X_test)

print('Confusion matrix:\n', confusion_matrix(y_true=y_test, y_pred=y_pred))
print(accuracy_score(y_test, y_pred))