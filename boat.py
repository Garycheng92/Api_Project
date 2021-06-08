from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants
import auth

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


@bp.route('', methods=['POST','GET', 'PUT'])
def boats_get_post():
    if request.method == 'POST':
        payload = auth.verify_jwt(request)
        content = request.get_json()
        if 'application/json' not in request.content_type:
            res = make_response(json.dumps({"Error": "Media type Unsupported"}))
            res.mimetype = 'application/json'
            res.status_code = 415
            return res
        if 'application/json' not in request.accept_mimetypes:
            res = make_response(json.dumps({"Error": "Media Type not available"}))
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        if len(content.keys()) < 3 or len(content.keys()) > 3:
            return json.dumps({"Error": "The request object only takes 3 attributes"}),400
        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
        new_boat.update({'name': content['name'], 'type': content['type'],
          'length': content['length'], 'loads': [], "owner": payload['sub']})
        client.put(new_boat)
        res = make_response(json.dumps({"id": new_boat.id, "name": content["name"], "type": content["type"],
                           "length": content["length"], 'loads': [], "self": request.url_root + 'boats/' +str(new_boat.id)}))
        res.mimetype = 'application/json'
        res.status_code = 201
        return res

    elif request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            res = make_response(json.dumps({"Error": "Media Type not available"}))
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        payload = auth.verify_jwt_1(request)
        counter = 0
        query = client.query(kind=constants.boats)
        query.add_filter('owner', '=', payload['sub'])
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
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
        res = make_response(json.dumps(output))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

    elif request.method == 'PUT':
        res = make_response(json.dumps({"Error": "Method not Recognized"}))
        res.mimetype = 'application/json'
        res.status_code = 405
        return res

    else:
        return 'Method not recogonized'

@bp.route('/<bid>', methods=['PUT','DELETE', 'PATCH'])
def boats_put_delete(bid):
    if request.method == 'PUT':
        payload = auth.verify_jwt(request)
        if 'application/json' not in request.content_type:
            res = make_response(json.dumps({"Error": "Media type Unsupported"}))
            res.mimetype = 'application/json'
            res.status_code = 415
            return res
        if 'application/json' not in request.accept_mimetypes:
            res = make_response(json.dumps({"Error": "Media Type not available"}))
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        content = request.get_json()
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        if not boat or boat['owner'] != payload['sub']:
            res = make_response(json.dumps({"Error": "No boat with this boat_id exists"}))
            res.mimetype = 'application/json'
            res.status_code = 403
            return res
        boat.update({'name': content['name'], 'type': content['type'],
          'length': content['length']})
        client.put(boat)
        res = make_response(json.dumps(boat))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

    elif request.method == 'PATCH':
        payload = auth.verify_jwt(request)
        if 'application/json' not in request.content_type:
            res = make_response(json.dumps({"Error": "Media type Unsupported"}))
            res.mimetype = 'application/json'
            res.status_code = 415
            return
        if 'application/json' not in request.accept_mimetypes:
            res = make_response(json.dumps({"Error": "Media Type not available"}))
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        content = request.get_json()
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        if not boat or boat['owner'] != payload['sub']:
            res = make_response(json.dumps({"Error": "No boat with this boat_id exists"}))
            res.mimetype = 'application/json'
            res.status_code = 403
            return res
        boat.update({'name': content['name'], 'type': content['type'],
          'length': content['length']})
        client.put(boat)
        res = make_response(json.dumps(boat))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

    elif request.method == 'DELETE':
        payload = auth.verify_jwt(request)
        key = client.key(constants.boats, int(bid))
        boat = client.get(key=key)
        if not boat or boat['owner'] != payload['sub']:
            res = make_response(json.dumps({"Error": "No boat with this boat_id exists"}))
            res.mimetype = 'application/json'
            res.status_code = 403
            return res
        if len(boat['loads']) > 0:
            for i in boat['loads']:
                load_key = client.key(constants.loads, int(i['id']))
                load = client.get(key=load_key)
                load['carrier'] = {}
                client.put(load)
        client.delete(key)
        return ('',204)
    else:
        return 'Method not recogonized'

@bp.route('/<bid>/loads/<lid>', methods=['PUT','DELETE'])
def assign_unassign_load(bid,lid):
    if request.method == 'PUT':
        payload = auth.verify_jwt(request)
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        if not boat:
            return json.dumps({"Error": "No boat with this boat_id exists"}), 404
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        if not load:
            return json.dumps({"Error": "No load with this load_id exists"}), 404
        if load['carrier']:
            return json.dumps({"Error": "Load already assigned to a boat"}), 403
        boat['loads'].append({"id": load.id})
        load['carrier']["id"] = boat.id
        load['carrier']["name"] = boat['name']
        client.put(boat)
        client.put(load)
        return('',204)
    if request.method == 'DELETE':
        payload = auth.verify_jwt(request)
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        if not boat:
            return json.dumps({"Error": "No boat with this boat_id exists"}), 404
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        if not load:
            return json.dumps({"Error": "No load with this load_id exists"}), 404
        load['carrier'] = {}
        for i in boat['loads']:
            if str(i['id']) == str(lid):
                boat['loads'].remove(i)
        client.put(boat)
        client.put(load)
        return('',204)