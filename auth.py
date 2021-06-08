from google.cloud import datastore
from flask import Flask, request, jsonify, _request_ctx_stack, Blueprint, make_response
import requests
import constants
import boat
import load
import user
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

app = Flask(__name__)

client = datastore.Client()

BOATS = "boats"

ALGORITHMS = ["RS256"]


# This code is adapted from https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

def verify_jwt(request):
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                             "Authorization header is expected"}, 401)
    parts = request.headers['Authorization'].split()
    token = parts[1]

    jsonurl = urlopen("https://" + constants.DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Invalid header. "
                             "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=constants.CLIENT_ID,
                issuer="https://" + constants.DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                             "description":
                                 "incorrect claims,"
                                 " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Unable to parse authentication"
                                 " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                         "description":
                             "No RSA key in JWKS"}, 401)

def verify_jwt_1(request):
    counter = 0
    if 'application/json' not in request.accept_mimetypes:
        res = make_response(json.dumps({"Error": "Media Type not available"}))
        res.mimetype = 'application/json'
        res.status_code = 406
        return res
    query = client.query(kind=constants.boats)
    q_limit = int(request.args.get('limit', '5'))
    q_offset = int(request.args.get('offset', '0'))
    l_iterator = query.fetch(limit=q_limit, offset=q_offset)
    pages = l_iterator.pages
    results = list(next(pages))
    if l_iterator.next_page_token:
        next_offset = q_offset + q_limit
        next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
    else:
        next_url = None
    for e in results:
        counter += 1
        e["id"] = e.key.id
        e["self"] = request.url_root + 'boats/' + str(e.key.id)
        if len(e['loads']) > 0:
            for i in e['loads']:
                i['self'] = request.url_root + 'loads/' + str(i['id'])
    output = {"boats": results, "total": counter}
    if next_url:
        output["next"] = next_url

    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(output, 200)
    parts = request.headers['Authorization'].split()
    token = parts[1]

    jsonurl = urlopen("https://" + constants.DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError(output, 200)
    if unverified_header["alg"] == "HS256":
        raise AuthError(output, 200)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=constants.CLIENT_ID,
                issuer="https://" + constants.DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError(output, 200)
        except jwt.JWTClaimsError:
            raise AuthError(output, 200)
        except Exception:
            raise AuthError(output, 200)

        return payload
    else:
        raise AuthError(output, 200)

