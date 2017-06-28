from flask import Flask, redirect, request

httpapp = Flask(__name__)

@httpapp.before_request
def http_before_request():
  url = request.url.replace('http://', 'https://', 1)
  return redirect(url)

@httpapp.route
def http_index():
  url = request.url.replace('http://', 'https://', 1)
  return redirect(url)

httpapp.run(debug=True, host='0.0.0.0', port=80)
