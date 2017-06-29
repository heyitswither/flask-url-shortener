from flask import Flask, abort, redirect, render_template, render_template_string, request, Markup, make_response
import json
import random
import ssl
import asyncio

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

app = Flask(__name__)
validChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_'

BASE62 = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"

def valid_url(url):
  try:
    URLValidator()(url)
  except ValidationError:
    return False
  else:
    return True

def encode(num, alphabet=BASE62):
  """Encode a positive number in Base X

  Arguments:
  - `num`: The number to encode
  - `alphabet`: The alphabet to use for encoding
  """
  if num == 0:
    return alphabet[0]
  arr = []
  base = len(alphabet)
  while num:
      num, rem = divmod(num, base)
      arr.append(alphabet[rem])
  arr.reverse()
  return ''.join(arr)

def urls_file_exists(): # Imports storage file, or creates in not found
  global store_dict
  try:
    with open('storage.json', 'r') as fileIn:
      store_dict = json.load(fileIn)
  except FileNotFoundError:
    with open('storage.json', 'w+') as fileOut:
      store_temp = {"urls": []}
      json.dump(store_temp, fileOut, indent=2, sort_keys=True)
      store_dict = store_temp

def save_urls_file(): # Saves storage dict to file
  global store_dict
  with open('storage.json', 'w') as fileOut:
    json.dump(store_dict, fileOut, indent=2, sort_keys=True)

def short_code_exists(short_code): # Check if a short code exists, requires short_code, returns bool
  global store_dict
  for url_dict in store_dict['urls']:
    for key in url_dict:
      if key == short_code:
        return True
  return False

def long_url_exists(long_url): # Check if a long url exists, requires long url, returns bool
  global store_dict
  for url_dict in store_dict['urls']:
    for key in url_dict:
      if url_dict[key] == long_url:
        return True
  return False

def get_long_url(short_code): # Gets a long url, requires short_code, returns str long_url
  global store_dict
  for url_dict in store_dict['urls']:
    for key in url_dict:
      if key == short_code:
        return url_dict[key]
  return 'Url not found'

def get_short_url(long_url): # Gets a short code, requires long_url, returns str short_code
  global store_dict
  for url_dict in store_dict['urls']:
    for key in url_dict:
      if url_dict[key] == long_url:
        return key
  return 'Url not found'

def random_url(): # Returns unique str short_code
  random_code = random.randint(0, 550731775)
  random_code_encoded = encode(random_code)
  while short_code_exists(random_code_encoded):
    random_code = random.randint(0, 550731775)
  return random_code_encoded

def create_url(long_url): # Creates short links, requires long_url, returns str short_code
  global store_dict
  if long_url_exists(long_url):
    return get_short_url(long_url)
  created_short_url = random_url()
  store_dict['urls'].append({created_short_url: long_url})
  save_urls_file()
  return created_short_url

def create_custom_url(request, short_url, long_url): # Creates custom short links, requires short_code, long_url, returns success/fail
  global store_dict
  global validChars
  if short_code_exists(short_url):
    return False
  for letter in short_url:
    if not letter in validChars:
      return False
  store_dict['urls'].append({short_url: long_url})
  save_urls_file()
  return True

@app.before_request
def before_request():
  if request.url.startswith('http://'):
    url = request.url.replace('http://', 'https://', 1)
    return redirect(url)

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
    if 'previewsEnabled' in request.cookies:
      if request.cookies.get('previewsEnabled') == "true":
        previews_status = "on"
        opposite_status = "off"
      elif request.cookies.get('previewsEnabled') == "false":
        previews_status = "off"
        opposite_status = "on"
    else:
      previews_status = "off"
      opposite_status = "on"
    return render_template('index.html', previews_status=previews_status, opposite_status=opposite_status)
  elif request.method == 'POST':
    custom_url = dict(request.form)['custom_url'][0]
    long_url = dict(request.form)['long_url'][0]
    if not long_url.startswith('http://') or not long_url.startswith('https://'):
      long_url = "http://" + long_url
    if not valid_url(long_url):
      response = 'Invalid long URL'
      return render_template('previews.html', response=response, previews_status=previews_status, opposite_status=opposite_status)
    elif long_url.split('/')[2] == '/'.join(request.url_root.split('/')[:3]):
      response = 'Invalid long URL'
      return render_template('previews.html', response=response, previews_status=previews_status, opposite_status=opposite_status)

    if 'previewsEnabled' in request.cookies:
      if request.cookies.get('previewsEnabled') == "true":
        previews_status = "on"
        opposite_status = "off"
      elif request.cookies.get('previewsEnabled') == "false":
        previews_status = "off"
        opposite_status = "on"
    else:
      previews_status = "off"
      opposite_status = "on"

    if long_url == "":
      response = 'You cannot leave the long URL field empty!'
      return render_template('previews.html', response=response, previews_status=previews_status, opposite_status=opposite_status)
    elif not custom_url == "":
      if create_custom_url(request, custom_url, long_url):
        print("New URL {} ==> {}".format(custom_url, long_url))
        new_url = custom_url
      else:
        reponse = 'Short code is invalid or already in use'
        return render_template('previews.html', response=response, previews_status=previews_status, opposite_status=opposite_status)
    elif custom_url == "":
      new_url = create_url(long_url)
      print("New URL {} ==> {}".format(new_url, long_url))
    return render_template('new.html', new_url=request.url_root + new_url, old_url=get_long_url(new_url), previews_status=previews_status, opposite_status=opposite_status)

@app.route('/<short_url_request>')
def short_url_handler(short_url_request):
  if not short_code_exists(short_url_request):
    return abort(404)
  elif "previewsEnabled" in request.cookies and request.cookies.get('previewsEnabled') == "true":
    return redirect('/preview/{}'.format(short_url_request))
  else:
    return redirect(get_long_url(short_url_request))

@app.route('/preview/<short_url_request>')
def short_url_preview(short_url_request):
  if not short_code_exists(short_url_request):
    return abort(404)
  if 'previewsEnabled' in request.cookies:
    if request.cookies.get('previewsEnabled') == "true":
      previews_status = "on"
      opposite_status = "off"
    elif request.cookies.get('previewsEnabled') == "false":
      previews_status = "off"
      opposite_status = "on"
  else:
    previews_status = "off"
    opposite_status = "on"
  return render_template('previews.html', response='This URL redirects to {}'.format(get_long_url(short_url_request)), previews_status=previews_status, opposite_status=opposite_status)

@app.route('/preview-toggle/')
def preview_toggle():
  if "previewsEnabled" in request.cookies and request.cookies.get('previewsEnabled') == "true":
    response = 'Previews have been disabled'
    resp = make_response(render_template('previews.html', response=response, previews_status='off', opposite_status='on'))
    resp.set_cookie('previewsEnabled', 'false')
  elif "previewsEnabled" in request.cookies and request.cookies.get('previewsEnabled') == "false":
    response = 'Previews have been enabled'
    resp = make_response(render_template('previews.html', response=response, previews_status='on', opposite_status='off'))
    resp.set_cookie('previewsEnabled', 'true')
  else:
    response = 'Previews have been enabled'
    resp = make_response(render_template('previews.html', response=response, previews_status='on', opposite_status='off'))
    resp.set_cookie('previewsEnabled', 'true')
  return resp

if __name__ == '__main__':
  context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
  context.load_cert_chain('/etc/letsencrypt/live/vps2.heyitswither.ml/cert.pem', '/etc/letsencrypt/live/vps2.heyitswither.ml/privkey.pem')
  urls_file_exists()
  app.run(debug=True, host='0.0.0.0', port=443, ssl_context=context)
