from flask import Blueprint, request, make_response
from google.cloud import datastore
import json
import constants


client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
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
        if len(content.keys()) < 3 or len(content.keys()) > 3:
            return json.dumps({"Error": "The request object only takes 3 attributes"}),400
        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        new_load.update({"volume": content["volume"], "carrier": {}, "content": content["content"],
                         "creation_date": content["creation_date"]})
        client.put(new_load)
        res = make_response(json.dumps({"id": new_load.id, "volume": content["volume"], "content": content["content"],
                                        "creation_date": content["creation_date"], 'loads': [],
                                        "self": request.url_root + 'loads/' + str(new_load.id)}))
        res.mimetype = 'application/json'
        res.status_code = 201
        return res
    elif request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            res = make_response(json.dumps({"Error": "Media Type not available"}))
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        query = client.query(kind=constants.loads)
        counter = 0
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            counter += 1
            e["id"] = e.key.id
            e["self"] = request.url_root + 'loads/' + str(e.key.id)
            if e['carrier']:
                e['carrier']['self'] = request.url_root + 'boats/' + str(e['carrier']['id'])
        output = {"loads": results, "total": counter}
        if next_url:
            output["next"] = next_url
        res = make_response(json.dumps(output))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

@bp.route('/<lid>', methods=['PUT','DELETE', 'PATCH'])
def load_put_delete(lid):
    if request.method == 'PUT':
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
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        if not load:
            res = make_response(json.dumps({"Error": "No load with this load_id exists"}))
            res.mimetype = 'application/json'
            res.status_code = 403
            return res
        load.update({"volume": content["volume"], "content": content["content"], "creation_date": content["creation_date"]})
        client.put(load)
        res = make_response(json.dumps(load))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res

    elif request.method == 'DELETE':
        key = client.key(constants.loads, int(lid))
        load = client.get(key=key)
        if not load:
            return json.dumps({"Error": "No load with this load_id exists"}), 404
        if load['carrier']:
            boat_key = client.key(constants.boats, int(load['carrier']['id']))
            boat = client.get(key=boat_key)
            for i in boat['loads']:
                if str(i['id']) == str(lid):
                    boat['loads'].remove(i)
            client.put(boat)
        client.delete(key)
        return ('',204)

    elif request.method == 'PATCH':
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
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)
        if not load:
            res = make_response(json.dumps({"Error": "No load with this load_id exists"}))
            res.mimetype = 'application/json'
            res.status_code = 403
            return res
        load.update({"volume": content["volume"], "content": content["content"], "creation_date": content["creation_date"]})
        client.put(load)
        res = make_response(json.dumps(load))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res
    else:
        return 'Method not recogonized'
