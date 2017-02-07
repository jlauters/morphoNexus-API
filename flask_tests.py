# Flask Test Suite Skeleton
import os
import json
import unittest

config = json.load(open('./config.json'))

from api import app

class FlaskTestCase(unittest.TestCase):

  def setUp(self):
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = config['auth_secret']
    self.app = app.test_client()

  def tearDown(self):
    app.config['TESTING'] = False
    self.app = None

  def login(self, username, password):
    return self.app.post('/login', data = dict(
      username = username,
      password = password
    ), follow_redirects = True)

  def logout(self, access_token):
    return self.app.get('/logout', environ_base={"Authorization": "Bearer " + access_token}, follow_redirects = True)

  #-----------------------------------
  # Inquisite Core API Endpoint Tests
  #-----------------------------------

  # make sure our base url just returns something
  def test_base_url(self):
    rv = self.app.get('/')
    assert rv.data != ''      

  def test_parse_matrix(self):

    test_file = open('./nexus/Amphisbaenia_combinedmatrix.txt', 'r')

    print "in test parse_matrix"
    print test_file

    rv = self.app.post('/parse_matrix', data=dict(
      matrix_file = test_file
    ))

    retobj = json.loads(rv.data)
 
    print "matrix GET url"
    print retobj['matrix_url']

    assert retobj['status'] == 'ok'
    assert retobj['msg'] != ''

if __name__ == '__main__':
  unittest.main()
