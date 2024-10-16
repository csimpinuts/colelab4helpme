from flask import Flask, request, redirect, url_for
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

@app.route('/')
def index():
    # Spotify login
    auth_url = (
        f"https://accounts.spotify.com/authorize?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope=user-read-playback-state,user-modify-playback-state"
    )
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        return f"Error: {response.json().get('error_description')}"
    
    access_token = response.json().get('access_token')

    # Use the access token to get the user's playback state
    playback_url = 'https://api.spotify.com/v1/me/player/currently-playing'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    playback_response = requests.get(playback_url, headers=headers)

    if playback_response.status_code == 200:
        current_playback = playback_response.json()
        song_name = current_playback['item']['name']
        artist_name = current_playback['item']['artists'][0]['name']
        album_name = current_playback['item']['album']['name']
        album_cover = current_playback['item']['album']['images'][0]['url']

        return f"""
        <h1>Now Playing</h1>
        <p>Song: {song_name}</p>
        <p>Artist: {artist_name}</p>
        <p>Album: {album_name}</p>
        <img src="{album_cover}" alt="Album Cover" style="width:200px;height:auto;">
        <br>
        <a href="/play/{current_playback['item']['id']}?access_token={access_token}">Play this track again</a>
        """
    else:
        return f"Error retrieving playback state: {playback_response.json().get('error_description')}"

@app.route('/play/<track_id>')
def play_track(track_id):
    access_token = request.args.get('access_token')  # Retrieve the access token properly

    play_url = 'https://api.spotify.com/v1/me/player/play'
    headers = {
        'Authorization': f'Bearer {access_token}',  # Use the stored access token
        'Content-Type': 'application/json'
    }
    data = {
        'uris': [f'spotify:track:{track_id}']  # Track ID to play
    }
    play_response = requests.put(play_url, headers=headers, json=data)

    if play_response.status_code == 204:
        return 'Playback started!'
    else:
        return f"Error: {play_response.json().get('error_description')}"

if __name__ == '__main__':
    app.run(port=8888)
