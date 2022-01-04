import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler

data = pd.read_csv("SpotifyFeatures.csv")
audio_features = data[['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']]

scaler = StandardScaler()
scaler.fit(audio_features)

joblib.dump(scaler, "scaler.pkl")
print("Scaler has been fit!")