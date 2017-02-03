# matrix utils module

import json
import requests

def is_number(s):
  try:
    int(s)
    return True
  except ValueError:
    return False

def verifyTaxa(sci_name):

  sanitized_sci_name = sci_name.replace('H_', '')
  sanitized_sci_name = sanitized_sci_name.replace('"', '')
  sanitized_sci_name = sanitized_sci_name.replace("'", '')

  verifiedTaxa = []

  # NCBI is what Morphobank uses, checking all data sources to verify as close to 100% as possible
  # NCBI will be our preferred
  data_sources = '4'
  gnparser_url = 'http://resolver.globalnames.org/name_resolvers.json?perferred_data_sources=' + data_sources + '&best_match_only=true&resolve_once=false&names='

  gnparser = requests.get(gnparser_url + sanitized_sci_name + '&with_context=true')
  if 200 == gnparser.status_code:
    gnp_json = json.loads( gnparser.content )

    for data in gnp_json['data']:
      if data['is_known_name']:

        verifiedTaxa.append({
          "datasource": data['results'][0]['data_source_title'],
          "match_value": data['results'][0]['match_value'],
          "name_string": data['results'][0]['name_string']
        })

  return verifiedTaxa
