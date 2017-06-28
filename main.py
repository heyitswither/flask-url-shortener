from flask import Flask, abort, redirect, render_template, render_template_string, request
import json
import random

app = Flask(__name__)
validChars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

BASE62 = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"

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
    return 'That url is taken'
  for letter in short_url:
    if not letter in validChars:
      return 'Invalid short code'
  store_dict['urls'].append({short_url: long_url})
  save_urls_file()
  return 'Url successfully created\n<a href="{}"></a> ==> <a href = "{}"></a>'.format(request.url_root + short_url, long_url)

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
    return render_template('index.html')
  elif request.method == 'POST':
    custom_url = dict(request.form)['custom_url'][0]
    long_url = dict(request.form)['long_url'][0]
    if long_url == "":
      new_url_response = 'You cannot leave the long URL field empty!'
    elif not custom_url == "":
      new_url_response = create_custom_url(request, custom_url, long_url)
    elif custom_url == "":
      new_url_response = '<a href="{}"></a>'.format(request.url_root + create_url(long_url))
    return render_template('new.html', new_url_response=new_url_response)

@app.route('/<short_url_request>')
def short_url_handler(short_url_request):
  if not short_code_exists(short_url_request):
    return abort(404)
  return redirect(get_long_url(short_url_request))

if __name__ == '__main__':
  urls_file_exists()
  app.run(debug=True, host='0.0.0.0', port=8080)
