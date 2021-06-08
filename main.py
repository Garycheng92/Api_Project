from google.cloud import datastore
from flask import Flask, request, jsonify, _request_ctx_stack, Blueprint
import requests
import constants
import boat
import load
import user
from auth import app
from functools import wraps
import json

from six.moves.urllib.request import urlopen
from flask_cors import cross_origin
from jose import jwt

import json
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode


app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
app.register_blueprint(user.bp)
app.secret_key = 'SECRET_KEY'

client = datastore.Client()

BOATS = "boats"

CALLBACK_URL = 'https://apiproject-315912.ue.r.appspot.com/callback'

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=constants.CLIENT_ID,
    client_secret=constants.CLIENT_SECRET,
    api_base_url="https://" + constants.DOMAIN,
    access_token_url="https://" + constants.DOMAIN + "/oauth/token",
    authorize_url="https://" + constants.DOMAIN+ "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)


# This code is adapted from https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['POST'])
def login_user():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    body = {'grant_type': 'password', 'username': username,
            'password': password,
            'client_id': constants.CLIENT_ID,
            'client_secret': constants.CLIENT_SECRET
            }
    headers = {'content-type': 'application/json'}
    url = 'https://' + constants.DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    return r.text, 200, {'Content-Type': 'application/json'}


@app.route('/callback')
def callback_handling():
    # Handles response from token endpoint
    token = auth0.authorize_access_token()['id_token']
    resp = auth0.get('userinfo')
    userinfo = resp.json()


    # Store the user information in flask session.
    session['jwt_payload'] = userinfo
    session['profile'] = {
        'token': token,
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    new_user = datastore.entity.Entity(key=client.key(constants.users))
    new_user.update({"name": session["profile"]["user_id"]})
    client.put(new_user)
    return redirect('/dashboard')


@app.route('/ui_login')
def ui_login():
    return auth0.authorize_redirect(redirect_uri=CALLBACK_URL)

def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'profile' not in session:
      # Redirect to Login page here
      return redirect('/')
    return f(*args, **kwargs)

  return decorated

@app.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html',
                           userinfo=session['profile'],
                           userinfo_pretty=json.dumps(session['jwt_payload'], indent=4))
@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    params = {'returnTo': url_for('https://apiproject-315912.ue.r.appspot.com', _external=True), 'client_id': 'yeKoIg5b2orB6zvjRum5CRnI7W9n4vMH'}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
