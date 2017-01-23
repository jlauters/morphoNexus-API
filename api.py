import json
import requests
import collections
import datetime
import time
import logging
import urllib
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import sha256_crypt
from functools import wraps, update_wrapper
from flask import Flask, request, current_app, make_response, session, escape, Response
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import safe_str_cmp
from neo4j.v1 import GraphDatabase, basic_auth
from simpleCrossDomain import crossdomain
from basicAuth import check_auth, requires_auth

config = json.load(open('./config.json'));

# Init
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = config['auth_secret']

# start jwt service
jwt = JWTManager(app)

# Core Routes
@app.route("/")
def index():

  resp = (("status", "ok"),
          ("v1", "http://inquisite.whirl-i-gig.com/api/v1"))
  resp = collections.OrderedDict(resp)

  return Response(response=json.dumps(resp), status=200, mimetype="application/json")


# Login
@app.route('/login', methods=['POST'])
@crossdomain(origin='*')
def login():

  username = request.form.get('username')
  password = request.form.get('password')

  logging.warning("username: " + username)
  logging.warning("password: " + password)

  if username is not None and password is not None:
    # Get DB User 

    for person in db_user:
      #if pwd_context.verify(password, person['password']):
      if sha256_crypt.verify(password, person['password']):
      
        logging.warning('password verified. login success!')
        ret = {'access_token': create_access_token(identity=username), 'email': person['email'], 'user_id': person['user_id']}
        return Response(response=json.dumps(ret), status=200, mimetype="application/json")

    # We didn't find anyone
    ret = {"status": "err", "msg": "No user was found with that username, or your password was typed incorrectly"}
    return Response(response=json.dumps(ret), status=422, mimetype="application/json")

  else:

    resp = (("status", "err"),
            ("msg", "username and password are required"))
    resp = collections.OrderedDict(resp)
    return Response(response=json.dumps(resp), status=200, mimetype="application/json")


# Logout
@app.route('/logout')
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def logout():
  db_session.pop('username', None)




@app.errorhandler(404)
def page_not_found(e):

  resp = (("status", "err"),
          ("msg", "The request could not be completed"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=404, mimetype="application/json")

if __name__ == '__main__':
  app.run()
