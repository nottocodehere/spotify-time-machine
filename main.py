import requests
import urllib.parse
from datetime import datetime
from flask import Flask, redirect, request, jsonify, session, render_template
import os
from dotenv import load_dotenv
from billboard_grabber import BillboardGrabber

# importing keys from .env file
load_dotenv(os.path.join(os.getcwd(), '.env'))

#initializing Billboard grabber
song_grabber = BillboardGrabber()

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1/"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET")

playlists = []
playlist_id = ""

def token_checker():
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh-token")


@app.route("/")
def index():
    return """<h1>Welcome to Spotify Time-machine playlist creator</h1>
    <a href='/login'>Login with spotify</a>"""


@app.route("/login")
def login():
    scope = "user-read-private user-read-email playlist-modify-private playlist-modify-public"
    # scope = "user-read-private user-read-email"
    params = {
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "response_type": "code",
        "scope": scope,
        "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
        "show_dialog": "True"
    }

    auth_url = f"{SPOTIFY_AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)


@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error": request.args["error"]})

    if "code" in request.args:
        req_body = {
            "code": request.args["code"],
            "grant_type": "authorization_code",
            "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
            "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
            "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET")
        }

        response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
        token_info = response.json()
        print(f"Token info we got: {token_info}")

        session["access_token"] = token_info["access_token"]
        session["refresh_token"] = token_info["refresh_token"]
        session["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]

        print(f"Expires {session['expires_at']}")
        print(f'Session TOKEN {session["access_token"]}')

        # return redirect("/playlists")
        return redirect("/menu")


@app.route("/refresh-token")
def refresh_token():
    if "refresh_token" in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
            "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET")
        }

        response = requests.post(SPOTIFY_TOKEN_URL, data=req_body)
        new_token_info = response.json()
        session["access_token"] = new_token_info["access_token"]
        session["expires_at"] = datetime.now().timestamp() + new_token_info["expires_in"]

        return redirect("/menu")

# Here goes the workable part

@app.route("/playlists")
def get_playlists():
    global playlists

    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh-token")

    token_checker()

    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }

    response = requests.get(f"{SPOTIFY_API_BASE}me/playlists", headers=headers)
    playlists = response.json()

    return playlists

# playlists = get_playlists()


@app.route("/current")
def create_playlist(date=song_grabber.search_date):
    global playlist_id
    # TODO CHECK IF IT ALREADY EXISTS +++

    playlist_name = f"Time-machine - {song_grabber.search_date}"
    print(playlists["items"])

    for item in playlists["items"]:
        if item["name"] == playlist_name:
            print("The playlist already exists, returning to menu")
            return redirect("/menu")


    # Schema json["items"][item]["name"]
    # if "access_token" not in session:
    #     return redirect("/login")
    #
    # if datetime.now().timestamp() > session["expires_at"]:
    #     return redirect("/refresh-token")
    token_checker()

    headers = {
        "Authorization": f"Bearer {session['access_token']}",
        # "Content - Type": "application / json"
    }

    data = {
        "name": playlist_name,
        "description": f"Top-100 picks for {song_grabber.search_date}",
        "public": True
    }

    response = requests.post(f"{SPOTIFY_API_BASE}users/31vkajssxmzwfsgyw3oeggmbl4wy/playlists", headers=headers,
                             json=data)
    # top100 = response.json()
    playlist_top100 = response.json()
    # print(f"PLAYLIST ORIGINAL RESPONSE {playlist_top100}")

    playlist_id = playlist_top100["id"]
    # print(f"PLAYLIST {playlist_id}")
    return playlist_top100


# @app.route("/playlists/<date>")
# def playlist(date=song_grabber.search_date):
#     return f"""<h1> Historical playlist for {date}, based on The Billboard Top-100</h1>"""

@app.route("/menu")
def menu():
    return render_template("menu.html")



@app.route("/playlist_info")
def search_add_song():
    # endpoint API BASE +/search
    if "access_token" not in session:
        return redirect("/login")

    if datetime.now().timestamp() > session["expires_at"]:
        return redirect("/refresh-token")

    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }

    song_id_list = {"uris": []}

    for key, value in song_grabber.song_dict.items():
        search_params = {
            "q": f"track: {value[1]} artist: {value[0]}",
            "type": "track",
        }

        get_track_id = requests.get(url=f"{SPOTIFY_API_BASE}search", params=urllib.parse.urlencode(search_params), headers=headers)
        print(f"RESPONSE: {get_track_id.request.url}")
        # r = requests.get(url="https://api.spotify.com/v1/search?q=track+Sufragette+City+artist%3A+David+Bowie&type=track", headers=headers)

        track_info = get_track_id.json()
        track_id = track_info["tracks"]["items"][0]["uri"]

        song_id_list["uris"].append(track_id)


    # data = {"uris":[track_id]}
    send_track = requests.post(url=f"{SPOTIFY_API_BASE}playlists/{playlist_id}/tracks", headers=headers, json=song_id_list)
    res_send_track = send_track.json()

    #Schema - result["tracks"]["items"][0]["uri"]

    return res_send_track



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, use_reloader=False)

# SCHEMA - track:Many%20Iny%20They%20Mirror20artist:Michael%20Jackson
