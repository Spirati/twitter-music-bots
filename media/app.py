from fastapi import FastAPI, Request
from dotenv import load_dotenv
from os import getenv
from requests_oauthlib import OAuth1Session
import webbrowser
import json

from time import sleep

from os import listdir
from os.path import getsize

def upload_files(session: OAuth1Session):
    filenames = listdir("out")
    if len(filenames) > 300:
        print("Too many files!")
        return []

    ids = []
    
    for filename in filenames:
        f = open(f"out/{filename}", "rb")
        size = getsize(f"out/{filename}")
        
        init = session.post(
            "https://upload.twitter.com/1.1/media/upload.json", {
                "command": "INIT",
                "total_bytes": size,
                "media_type": "video/mp4"
            }
        )
        init_json = init.json()
        print(init_json)
        append = session.post(
            "https://upload.twitter.com/1.1/media/upload.json", files={
                "command": "APPEND",
                "media_id": init_json["media_id"],
                "media": f,
                "segment_index": 0
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

        ids.append(init_json["media_id"])
    
    return ids

app = FastAPI()
load_dotenv()

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

    for media_id in media_ids:
        tweets.append(twitter.post("https://api.twitter.com/1.1/statuses/update.json", {
            "status": "check this shit out",
            "media_ids": media_id
        }).json())

    #TODO: take the tweet ids after posting and fold into a cheap bots done quick source
    
    return json.dumps(tweets)

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
