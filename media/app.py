from fastapi import FastAPI, Request
from dotenv import load_dotenv
from os import getenv
from requests_oauthlib import OAuth1Session
import webbrowser
import json

from time import sleep

from os import listdir
from os.path import getsize, abspath, join, dirname
import sys

ROOT_DIR = dirname(sys.argv[0])

def upload_files(session: OAuth1Session):
    filenames = listdir(join(ROOT_DIR, "out"))
    if len(filenames) > 300:
        print("Too many files!")
        return []

    ids = []
    
    for filename in filenames:
        size = getsize(join(ROOT_DIR, "out", filename))
        with open(join(ROOT_DIR, 'out', filename), "rb") as f:
            
            init = session.post(
                "https://upload.twitter.com/1.1/media/upload.json", {
                    "command": "INIT",
                    "total_bytes": size,
                    "media_type": "video/mp4",
                    "media_category": "tweet_video"
                }
            )
            init_json = init.json()
            append = session.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                data={
                    "command": "APPEND",
                    "media_id": init_json["media_id"],
                    "segment_index": 0
                },
                files={
                    "media": f.read()
                }
            )
        finalize = session.post(
            "https://upload.twitter.com/1.1/media/upload.json", {
                "command": "FINALIZE",
                "media_id": init_json["media_id"]
            }
        )
        finalize_json = finalize.json()
        check = finalize_json
        while check.get("processing_info", None):
            sleep(check["processing_info"]["check_after_secs"])
            check = session.post(
            "https://upload.twitter.com/1.1/media/upload.json", {
                "command": "STATUS",
                "media_id": init_json["media_id"]
                }
            ).json()

        ids.append((".".join(filename.split("-process")[0].split(".")[:-1]), init_json["media_id"]))
    
    return ids

app = FastAPI()

load_dotenv(join(ROOT_DIR, '.env'))

api_key = getenv("TWITTER_OAUTH_API_KEY")
api_secret = getenv("TWITTER_OAUTH_API_SECRET")
token_url = "https://api.twitter.com/oauth/request_token"
access_url = "https://api.twitter.com/oauth/access_token"
authorize_url = "https://api.twitter.com/oauth/authorize"

session = {}

@app.get("/")
def home(request: Request):
    twitter = OAuth1Session(
        client_key=api_key, client_secret=api_secret,
        resource_owner_key=session['resource_token'], resource_owner_secret=session['resource_secret'],
        verifier=request.query_params['oauth_verifier']
    )
    token_res = twitter.fetch_access_token(access_url)

    token = token_res['oauth_token']
    secret = token_res['oauth_token_secret']

    twitter = OAuth1Session(
        client_key=api_key, client_secret=api_secret,
        resource_owner_key=token, resource_owner_secret=secret,
    )

    media_ids = upload_files(twitter)

    tweets = []

    for name,media_id in media_ids:
        tweets.append((name, twitter.post("https://api.twitter.com/1.1/statuses/update.json", {
            "status": name[:140],
            "media_ids": media_id
        }).json()))

    # print(tweets)
    #TODO: take the tweet ids after posting and fold into a cheap bots done quick source
    media_links = [(name, tweet['entities']['media'][0]['expanded_url']) for name,tweet in filter(lambda x: x[1].get("entities", None), tweets)]

    print("FAILED TO PROCESS:", [name for name,tweet in filter(lambda x: "entities" not in x[1], tweets)])
    
    output = {
        "origin": [" ".join(c) for c in media_links] 
    }

    return output

def start_server():
    twitter = OAuth1Session(client_key=api_key, client_secret=api_secret)
    res = twitter.fetch_request_token(token_url)
    session['resource_token'] = res['oauth_token']
    session['resource_secret'] = res['oauth_token_secret']

    auth_url = twitter.authorization_url(authorize_url)
    
    print("Please now authorize with Twitter.")
    webbrowser.open(auth_url)

    import uvicorn
    uvicorn.run("media.app:app", host="localhost", port=15189, workers=1)
