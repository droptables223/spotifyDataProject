from flask import Flask, json, jsonify, redirect, render_template, url_for, request
from pymongo import MongoClient

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

app = Flask(__name__)

connection_string = "mongodb+srv://lmgallo:TestTest123@cluster0.c5xci.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(connection_string)
#MONGO TSUFF
db = client['spotifyDatabase']
tracks = db['tracks']
genres = db['genres']
artists = db['artists']

#API - Initial Render

@app.route("/", methods=['GET', 'POST'])
def index():
    prediction = "Search for a Song"
    all_songs = tracks.find()
    return render_template('GUI.html', songs=all_songs, gen=prediction)

#API - Genre Prediction and Song Recomendation

@app.route("/predict", methods=['POST'])
def predict():
    try:
        song = request.form.get('song', '')  # Get from form data
        if not song:
            return jsonify({'error': 'No song provided'}), 400
        
        prediction = songsearch(song)
        cheems = f'Predicted Genre: {prediction}'
        if prediction:
           #recs = recommend_tracks(song)
           return jsonify({'data': cheems})

        return jsonify({'error': 'Prediction failed'}), 500
        
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#----------------------------------------------------------------------------------

#Training the model

# Fetch data from MongoDB
genre_data = list(genres.aggregate([
    {
        '$lookup': {
            'from': 'tracks',
            'localField': '_id',
            'foreignField': 'track_genre.$id',
            'as': 'tracks'
        }
    },
    {
        '$unwind': '$tracks'
    },
    {
        '$project': {
            '_id': 0,
            'genre': '$genre',
            'track_id': '$tracks.track_id',
            'popularity': '$tracks.popularity',
            'danceability': '$tracks.danceability',
            'energy': '$tracks.energy',
            'loudness': '$tracks.loudness',
            'speechiness': '$tracks.speechiness',
            'acousticness': '$tracks.acousticness',
            'instrumentalness': '$tracks.instrumentalness',
            'liveness': '$tracks.liveness',
            'valence': '$tracks.valence',
            'tempo': '$tracks.tempo',
        }
    }
]))

# Create a DataFrame from the retrieved data
df_genre_tracks = pd.DataFrame(genre_data)

# Prepare data for model training
X = df_genre_tracks[['danceability', 'energy', 'loudness', 'speechiness',
                     'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']]
y = df_genre_tracks['genre']

# Encode genre labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Train a Random Forest classifier
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=20,
    min_samples_split=10,
    min_samples_leaf=1,
    max_features='log2',
    random_state=42
)
model.fit(X_train, y_train)

# Make predictions on the test set
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print("Accuracy:", accuracy)


# Function to predict the genre of a track
def predict_track_genre(track_features):
    """Predicts the genre of a track given its features.

    Args:
      track_features: A dictionary of track features (e.g., popularity, danceability, etc.).

    Returns:
      The predicted genre of the track.
    """
    input_features = pd.DataFrame([track_features])
    prediction = model.predict(input_features)[0]
    predicted_genre = le.inverse_transform([prediction])[0]
    return predicted_genre

# Example usage:
track_features = {

    'danceability': 0.7,
    'energy': 0.8,
    'loudness': -5,
    'speechiness': 0.1,
    'acousticness': 0.2,
    'instrumentalness': 0.0,
    'liveness': 0.3,
    'valence': 0.9,
    'tempo': 120,
}

predicted_genre = predict_track_genre(track_features)
print("Predicted Genre:", predicted_genre)


#--------------------------------------------------------------

#Search Functions

#Enter a track and this will check the DB for the track, it it exists it will run the track
#data through our model

def get_track_info(track):
  if track:
    print("Song Name:", track['track_name'])

    artist_ref = track['artists'][0]
    artist = artists.find_one({'_id': artist_ref.id})
    if artist:
      print("Artist Name:", artist['artist'])
    else:
      print("Artist not found.")

    track_features = {
        'danceability': track['danceability'],
        'energy': track['energy'],
        'loudness': track['loudness'],
        'speechiness': track['speechiness'],
        'acousticness': track['acousticness'],
        'instrumentalness': track['instrumentalness'],
        'liveness': track['liveness'],
        'valence': track['valence'],
        'tempo': track['tempo'],
    }

    predicted_genre = predict_track_genre(track_features)
    print("Predicted Genre:", predicted_genre)
    return predicted_genre

    genre_ref = track['track_genre']
    genre = genres.find_one({'_id': genre_ref.id})
    if genre:
      print("Actual Genre:", genre['genre'])
    else:
      print("Genre not found.")

  else:
    print("Track not found.")


def songsearch(song):
    song_name = song
    track2 = tracks.find_one({'track_name': song_name})
    if track2:
        return get_track_info(track2)

    else:
        print("Track not found.")





#----------------------------------------------------------------

#TRack Recommendations

def recommend_tracks(track_name, num_recommendations=1):
  """Recommends tracks based on the inputted track name.

  Args:
    track_name: The name of the track to use as input.
    num_recommendations: The number of recommendations to return.

  Returns:
    A list of recommended track names.
  """

  # Find the track in the database based on the track name
  input_track = tracks.find_one({'track_name': track_name})

  if not input_track:
    print(f"Track '{track_name}' not found in the database.")
    return []

  # Extract the track's features
  input_track_features = {
      'danceability': input_track['danceability'],
      'energy': input_track['energy'],
      'loudness': input_track['loudness'],
      'speechiness': input_track['speechiness'],
      'acousticness': input_track['acousticness'],
      'instrumentalness': input_track['instrumentalness'],
      'liveness': input_track['liveness'],
      'valence': input_track['valence'],
      'tempo': input_track['tempo'],
  }

  # Predict the genre of the input track
  predicted_genre = predict_track_genre(input_track_features)

  # Find tracks with similar features and genre
  similar_tracks = list(tracks.find({
      'track_genre.$id': input_track['track_genre'].id,
      'track_name': {'$ne': track_name}  # Exclude the input track itself
  }))


  # Sort tracks by similarity (e.g., Euclidean distance of features)
  def calculate_similarity(track):
    track_features = {
        'danceability': track['danceability'],
        'energy': track['energy'],
        'loudness': track['loudness'],
        'speechiness': track['speechiness'],
        'acousticness': track['acousticness'],
        'instrumentalness': track['instrumentalness'],
        'liveness': track['liveness'],
        'valence': track['valence'],
        'tempo': track['tempo'],
    }
    similarity = 0  # Placeholder for a similarity calculation (e.g., Euclidean distance)
    for feature in input_track_features:
      similarity += abs(input_track_features[feature] - track_features[feature])
    return similarity

  similar_tracks.sort(key=calculate_similarity)

  return_list = []

  for track in similar_tracks[:num_recommendations]:
    track_artist_ref = track['artists'][0]
    artist = artists.find_one({'_id': track_artist_ref.id})
    if artist:
      return_list.append(track['track_name'] + ' - ' + artist['artist'])
    else:
      print("Artist not found.")

  return return_list



#---------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
