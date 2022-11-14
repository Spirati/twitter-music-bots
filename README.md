FFmpeg is not included with the repository, so install it on your system and put it on your PATH as necessary.
Get a Twitter developer account with Elevated access and set up an app to use OAuth1. Make a `.env` file with the following in it:
```
TWITTER_OAUTH_API_KEY=(YOUR OAUTH API KEY)
TWITTER_OAUTH_API_SECRET=(YOUR OAUTH API SECRET)
OAUTHLIB_INSECURE_TRANSPORT=1
```
Install from `requirements.txt`, then just run `main.py` from the project directory; usage instructions are the same as in `HOW TO.txt`.