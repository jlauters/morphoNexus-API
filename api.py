import json
import requests
import collections
import datetime
import time
import logging
from passlib.apps import custom_app_context as pwd_context
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
driver = GraphDatabase.driver(config['database_url'], auth=basic_auth(config['database_user'],config['database_pass']))
db_session = driver.session()


# JWT Real simple user class
class User(object):
  def __init__(self, id, username, password):
    self.id = id
    self.username = username
    self.password = password
    
  def __str__(self):
    return "User(id='%s')" % self.id

# start jwt service
#jwt = JWT(app, authenticate, identity)
jwt = JWTManager(app)


# Inquisite Core Routes
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
    db_user = db_session.run("MATCH (n:Person) WHERE n.email='" + username + "' RETURN n.name AS name, n.email AS email, n.password AS password, ID(n) AS user_id")
    for person in db_user:
      if pwd_context.verify(password, person['password']):
      
        logging.warning('password verified. login success!')
        ret = {'access_token': create_access_token(identity=username), 'email': person['email'], 'user_id': person['user_id']}
        return Response(response=json.dumps(ret), status=200, mimetype="application/json")
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


# People
@app.route('/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def peopleList():

  persons = []
  people = db_session.run("MATCH (n:Person) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")
  for p in people:
    persons.append({
      "name": p['name'],
      "location": p['location'],
      "email": p['email'],
      "url": p['url'],
      "tagline": p['tagline']
    })

  resp = (("status", "ok"),
          ("people", persons))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

# Get Person by ID
@app.route('/people/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPerson(person_id):

  logging.warning('in getPerson')

  current_user = get_jwt_identity()
  logging.warning("current_user: " + current_user)
  logging.warning("person_id: " + person_id)


  result = db_session.run("MATCH (n:Person) WHERE ID(n) = " + person_id + 
    " RETURN n.name AS name, n.email AS email, n.url AS url, n.location AS location, n.tagline AS tagline")
  if result:
    for p in result:
      resp = (("status", "ok"),
              ("name", p['name']),
              ("email", p['email']),
              ("url", p['url']),
              ("location", p['location']),
              ("tagline", p['tagline']))
  else:
    resp = (("status", "err")
            ("msg", "Could not find person for that ID"))
    
  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

# Add Person
@app.route('/people/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
def addPerson():

  logging.warning("in addPerson")

  name     = request.form.get('name')
  location = request.form.get('location')
  email    = request.form.get('email')
  url      = request.form.get('url')
  tagline  = request.form.get('tagline')
  password = request.form.get('password')

  logging.warning( "name: " + name )
  logging.warning( "location: " + location )
  logging.warning( "email: " + email )
  logging.warning( "url: " + url )
  logging.warning( "tagline: " + tagline )
  logging.warning( "password: " + password )

  if password is not None:
    user = User()
    User.hash_password(user, password)

    password_hash = user.password_hash
    ts            = time.time()
    created_on    = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    result = db_session.run("CREATE (n:Person {url: '" + url + "', name: '" + name + "', email: '" + email 
      + "', location: '" + location + "', tagline: '" + tagline + "', password: '" + password_hash + "', created_on: '" + created_on + "'})") 

    if result:
      resp = (("status", "ok"),
            ("msg", name + " added"))
    else:
      resp = (("status", "err"),
            ("msg", "Something went wrong saving Person"))

  else:
    resp = (("status", "err"),
            ("msg", "User Password is required"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editPerson(person_id):
 
  name     = request.args.get('name')
  location = request.args.get('location')
  email    = request.args.get('email')
  url      = request.args.get('url')
  tagline  = request.args.get('tagline')

  update = []
  if name is not None:
    update.append("p.name = '" + name + "'")

  if location is not None:
    update.append("p.location = '" + location + "'")

  if email is not None:
    update.append("p.email = '" + email + "'")

  if url is not None:
    update.append("p.url = '" + url + "'")

  if tagline is not None:
    update.append("p.tagline = '" + tagline + "'")


  update_str = "%s" % ", ".join(map(str, update))

  updated_person = {}
  yyresult = db_session.run("MATCH (p:Person) WHERE ID(p)=" + person_id + " SET " + update_str + 
    " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline")

  for p in result:
    updated_person['name'] = p['name']
    updated_person['location'] = p['location']
    updated_person['email'] = p['email']
    updated_person['url'] = p['url']
    updated_person['tagline'] = p['tagline']

  if result:
    resp = (("status", "ok"),
            ("msg", "Person updated"),
            ("person", updated_person))
  else:
    resp = (("status", "err"),
            ("msg", "problem updating Person"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/delete', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deletePerson(person_id):
  
  result = db_session.run("MATCH (n:Person) WHERE ID(n)=" + person_id + " OPTIONAL MATCH (n)-[r]-() DELETE r,n")

  if result:
    resp = (("status", "ok"),
            ("msg", "Peson Deleted Successfully"))
  else:
    resp = (("status", "err"),
            ("msg", "Something went wrong deleting Person"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/repos', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getPersonRepos(person_id):

  result = db_session.run("MATCH (n)<-[:OWNS|FOLLOWS|COLLABORATES_WITH]-(p) WHERE ID(p)=" + person_id + " RETURN n")

  print "Looking for repos ..."
  print result

  repos = []
  for item in result:
    print "going through items ... "
    print item 

  if result:
    resp = (("status", "ok"),
            ("repos", repos))
  else:
    resp = (("status", "err"),
            ("msg", "error getting repos for Person"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/people/<person_id>/set_password', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setPassword(person_id):

  password  = request.args.get('password')

  # TODO: Look into neo4j user authentication / encryption

# Organizations
@app.route('/organizations', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def orgList():
  
  orgslist = []
  orgs = db_session.run("MATCH (n:Organization) RETURN n.name AS name, n.location AS location, n.email AS email, n.url AS url, n.tagline AS tagline")
  for o in orgs:
    orgslist.append({
      "name": o['name'],
      "location": o['location'],
      "email": o['email'],
      "url": o['url'],
      "tagline": o['tagline']
    })  

  resp = (("status", "ok"),
          ("orgs", orgslist))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addOrg():

  name     = request.args.get('name')
  location = request.args.get('location')
  email    = request.args.get('email')
  url      = request.args.get('url')
  tagline  = request.args.get('tagline')
  
  result = db_session.run("CREATE (o:Organization {name: '" + name + "', location: '" + location + "', email: '" + email + "', url: '" + url + 
    "', tagline: '" + tagline + "'})")

  if result:
    resp = (("status", "ok"),
            ("msg", "Organization Added"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding Organization"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editOrg(org_id):

  name     = request.args.get('name')
  location = request.args.get('location')
  email    = request.args.get('email')
  url      = request.args.get('url')
  tagline  = request.args.get('tagline')

  update = []
  if name is not None:
    update.append("o.name = '" + name + "'")

  if location is not None:
    update.append("o.location = '" + location + "'")

  if email is not None:
    update.append("o.email = '" + email + "'")

  if url is not None:
    update.append("o.url = '" + url + "'")

  if tagline is not None:
    update.append("o.tagline = '" + tagline + "'")

  update_str = "%s" % ", ".join(map(str, update))

  updated_org = {}
  result = db_session.run("MATCH (o:Organization) WHERE ID(o)=" + org_id + " SET " + update_str + 
    " RETURN o.name AS name, o.location AS location, o.email AS email, o.url AS url, o.tagline AS tagline")

  for o in result:
    updated_org['name'] = o['name']
    updated_org['location'] = o['location']
    updated_org['email'] = o['email']
    updated_org['url'] = o['url']
    updated_org['tagline'] = o['tagline']

  if result:
    resp = (("status", "ok"),
            ("msg", "Organization updated"),
            ("org", updated_org))
  else:
    resp = (("status", "err"),
            ("msg", "Problem updating Organization"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/delete', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteOrg(org_id):

  result = db_session.run("MATCH (o:Organization) WHERE ID(o)=" + org_id + " OPTIONAL MATCH (o)-[r]-() DELETE r,o")
  if result:
    resp = (("status", "ok"),
            ("msg", "Organization deleted"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem deleting Organizatin"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/repos', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getOrgRepos(org_id):

  result = db_session.run("MATCH (n)<-[:PART_OF]-(o) WHERE ID(o)=" + org_id + " RETURN n")
  if result:
    resp = (("status", "ok"),
            ("repos", result))
  else:
    resp = (("status", "err"),
            ("msg", "problem getting repos for Organization"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/add_person/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addPersonToOrg(org_id, person_id):

  result = db_session.run("MATCH (o:Organization) WHERE ID(o)=" + org_id + " MATCH (p:Person) WHERE ID(p)=" + person_id +
    " MERGE (p)-[:PART_OF]->(o)")

  if result: 
    resp = (("status", "ok"),
            ("msg", "Person is part of Org"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding person to org"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/remove_person/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removePersonFromOrg(org_id, person_id):

  result = db_session.run("START p=node(*) MATCH (p)-[rel:PART_OF]->(n) WHERE ID(p)=" + person_id + " AND ID(n)=" + org_id + " DELETE rel")
  if result:
    resp = (("status", "ok"),
            ("msg", "removed person from org"))
  else:
    resp = (("status", "err"),
            ("msg", "problem removing person from org"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/organizations/<org_id>/people', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getOrgPeople(org_id):

  org_people = []
  result = db_session.run("MATCH (n)-[:OWNED_BY|FOLLOWED_BY|MANAGED_BY|PART_OF]-(p) WHERE ID(n)=" + org_id + 
    " RETURN p.name AS name, p.location AS location, p.email AS email, p.url AS url, p.tagline AS tagline")
  for p in result:
    org_people.append({
      "name": p['name'],
      "location": p['location'],
      "email": p['email'],
      "url": p['url'],
      "tagline": p['tagline']
    })  

  resp = (("status", "ok"),
          ("people", org_people))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

# Repositories
@app.route('/repositories', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def repoList():

  repos = []

  result = db_session.run("MATCH (n:Repository) RETURN n.url AS url, n.name AS name, n.readme AS readme")
  for r in result:
    repos.append({
      "name": r['name'],
      "url": r['url'],
      "readme": r['readme']
    })

  resp = (("status", "ok"),
          ("repos", repos))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/add', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepo():

  url    = request.args.get('url')
  name   = request.args.get('name')
  readme = request.args.get('readme')
  
  ts = time.time()
  created_on    = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

  result = db_session.run("CREATE (n:Repository {url: '" + url + "', name: '" + name + "', readme: '" + readme + 
    "', created_on: '" + created_on + "'})")
  if result:
    resp = (("status", "ok"),
            ("msg", "Created Repo"))
  else:
    resp = (("status", "err"),
            ("msg", "problem creating repo"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/edit', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def editRepo(repo_id):

  url    = request.args.get('url')
  name   = request.args.get('name')
  readme = request.args.get('readme')

  update = []
  if name is not None:
    update.append("n.name = '" + name + "'")

  if url is not None:
    update.append("n.url = '" + url + "'")

  if readme is not None:
    update.append("n.readme = '" + readme + "'")

  update_str = "%s" % ", ".join(map(str, update))

  updated_repo = {}
  result = db_session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " SET " + update_str + 
    " RETURN n.name AS name, n.url AS url, n.readme AS readme")

  for r in result:
    updated_repo['name'] = r['name']
    updated_repo['url'] = r['url']
    updated_repo['readme'] = r['readme']

  if result:
    resp = (("status", "ok"),
            ("msg", "Repository updated"),
            ("repo", updated_repo))
  else:
    resp = (("status", "err"),
            ("msg", "Problem updating Repo"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/delete', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def deleteRepo(repo_id):

  result = db_session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " OPTIONAL MATCH (o)-[r]-() DELETE r,o")
  if result:
    resp = (("status", "ok"),
            ("msg", "Repo deleted"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem deleting repo"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/owner', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoOwner(repo_id):

  owner = {}
  result = db_session.run("MATCH (n)<-[:OWNED_BY]-(p) WHERE ID(n)=" + repo_id + 
    " RETURN p.name AS name, p.email AS email, p.url AS url, p.locaton AS location, p.tagline AS tagline")
  for r in result:
    owner['name']     = r['name']
    owner['location'] = r['location']
    owner['email']    = r['email']
    owner['url']      = r['url']
    owner['tagline']  = r['tagline']

  if result:
    resp = (("status", "ok"),
            ("owner", owner))
  else:
    resp = (("status", "err"),
            ("msg", "could not retreive owner"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoInfo(repo_id):

  repo = {}
  result = db_session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " RETURN n.name AS name, n.url AS url, n.readme AS readme")
  for r in result:
    repo['name']   = r['name']
    repo['url']    = r['url']
    repo['readme'] = r['readme']

  if result:
    resp = (("status", "ok"),
            ("repo", repo ))
  else:
    resp = (("status", "err"),
            ("msg", "could not return repo info"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/add_collaborator/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoCollab(repo_id, person_id):

  result = db_session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " MATCH (p:Person) WHERE ID(p)=" + person_id +
    " MERGE (p)-[:COLLABORATES_WITH]->(n)")

  if result:
    resp = (("status", "ok"),
            ("msg", "Collaborator Added"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding Collaborator"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/remove_collaborator/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoCollab(repo_id, person_id):

  result = db_session.run("START p=node(*) MATCH (p)-[rel:COLLABORATES_WITH]->(n) WHERE ID(p)=" + person_id + " AND ID(n)=" + repo_id + " DELETE rel")
  if result:
    resp = (("status", "ok"),
            ("msg", "Collaborator removed"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem removing collaborator"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")
 
@app.route('/repositories/<repo_id>/add_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoFollower(repo_id, person_id):

  result = db_session.run("MATCH (n:Repository) WHERE ID(n)=" + repo_id + " MATCH (p:Person) WHERE ID(p)=" + person_id +
    " MERGE (p)-[:FOLLOWS]->(n)")
  if result:
    resp = (("status", "ok"),
            ("msg", "Folower Added"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem adding follower"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/remove_follower/<person_id>', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def removeRepoFollower(repo_id, person_id):

  result = db_session.run("START p=node(*) MATCH (p)-[rel:FOLLOWS]->(n) WHERE ID(p)=" + person_id + " AND ID(n)=" + repo_id + " DELETE rel")
  if result:
    resp = (("status", "ok"),
            ("msg", "Follower Removed"))
  else:
    resp = (("status", "err"),
            ("msg", "Problem removing follower"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=200, mimetype="application/json")

@app.route('/repositories/<repo_id>/add_data_node', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def addRepoData(repo_id):

  result = db_session.run()


@app.route('/repositories/<repo_id>/query', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def queryRepo(repo_id):

  result = db_session.run()

@app.route('/repositories/<repo_id>/get_all_data', methods=['GET'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def getRepoData(repo_id):

  result = db_session.run()

@app.route('/repositories/<repo_id>/set_entry_point', methods=['POST'])
@crossdomain(origin='*', headers=['Content-Type', 'Authorization'])
@jwt_required
def setEntryPoint(repo_id):

  result = db_session.run()

@app.errorhandler(404)
def page_not_found(e):

  resp = (("status", "err"),
          ("msg", "The request could not be completed"))

  resp = collections.OrderedDict(resp)
  return Response(response=json.dumps(resp), status=404, mimetype="application/json")

if __name__ == '__main__':
  app.run()
