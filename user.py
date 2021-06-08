from flask import Flask, request, jsonify, _request_ctx_stack, Blueprint
from google.cloud import datastore
import json
import constants


client = datastore.Client()

bp = Blueprint('user', __name__, url_prefix='/users')

@bp.route('', methods=['GET'])
def get_user():
    pointer = 0
    ans = []
    query = client.query(kind=constants.users)
    for i in list(query.fetch()):
        ans.append(i)
        pointer += 1
    return jsonify(ans), 200