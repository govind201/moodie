from flask import Flask, flash, redirect, render_template, request, session, abort, make_response, jsonify

import sys
import spotipy
import spotipy.util as util
from spotipy import oauth2
import random
import time

from moodify import authenticate_spotify, aggregate_top_artists, aggregate_top_tracks, select_tracks, create_playlist

client_id = "68d0c9e07d2d4f4dae29f3b00f6f1805"
client_secret = "365612d96a524d63ae3de9311f130432"
redirect_uri = "http://localhost:8000"
scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

access_token = ""
username = ""
sp_oauth = None


app = Flask(__name__)

# render username page


@app.route('/')
def my_form():
    return render_template('username.html')

# sends auth request


@app.route('/', methods=['POST'])
def index():
    global username
    username = request.form['username']
    cache = ".cache-" + username
    global sp_oauth
    global access_token
    sp_oauth = oauth2.SpotifyOAuth(client_id=client_id, client_secret=client_secret,redirect_uri=redirect_uri,scope=scope,cache_path=cache )
    # auth_url = 'https://accounts.spotify.com/authorize'
	#get cached token
    auth_url = sp_oauth.get_authorize_url()
    print('auth_url',auth_url)
    # token_info = sp_oauth.get_access_token()
    token_info = util.prompt_for_user_token(username, scope)
    access_token = token_info


    print('token_info', token_info)

    print("did it come here?")
    # if cached token exists, get it
    if token_info:
        return render_template('index.html')
        # print("Found cached token!")
        # milli_sec = int(round(time.time()))
        # expiry = token_info['expires_at']

        # # refresh token if expired
        # if milli_sec >= int(expiry):
        #     print('token expired')
        #     return redirect(auth_url)
        # # if token hasn't expired
        # else:
        #     access_token = token_info['access_token']

    # if no cached token, get a new access token
    else:
        return redirect(auth_url)

# display playlist page


@app.route('/results')
def results():
    playlist = request.args.get('url')

    return render_template('playlist.html', playlist=playlist)

# get new access token


@app.route('/callback/')
def my_callback():
    global access_token
    global sp_oauth
    global username

    url = request.url
    # get access token from spotify
    code = sp_oauth.parse_response_code(url)

    if code:
        print("Found Spotify auth code in Request URL! Trying to get valid access token...")
        token_info = util.prompt_for_user_token(username, scope)
        access_token = token_info 
    else:
        print('didnt come here')

    if access_token:
        return render_template('index.html')
    else:
        print('did not get access token')
        return render_template('username.html')
# create plalist


@app.route("/moodify", methods=['POST'])
def moodify():
    global access_token
    mood = request.json['mood']
    mood_string = request.json['mood_string']

    mood = float(mood)

    spotify_auth = authenticate_spotify(access_token)
    top_artists = aggregate_top_artists(spotify_auth)
    top_tracks = aggregate_top_tracks(spotify_auth, top_artists)
    selected_tracks = select_tracks(spotify_auth, top_tracks, mood)
    playlist = create_playlist(
        spotify_auth, selected_tracks, mood, mood_string)
    res = make_response(jsonify({
        "result": playlist
    }), 200)

    return res
