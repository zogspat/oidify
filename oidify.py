import requests
from requests.auth import HTTPBasicAuth
import webbrowser
from flask import Flask
from flask import request
import logging
import json
from pathlib import Path
import http.client as http_client
import os, sys
import uuid

#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propogate=True

app = Flask(__name__)

oktaInstance = "https://dev-okta-instance-change.okta.com"
client_id = "xxxx"
client_secret = "xxx-yyy"
aznEndpoint = oktaInstance + "/oauth2/unique-instance-identifier/v1/authorize"
tokenEndpoint = oktaInstance + "/oauth2/unique-instance-identifier/v1/token"
redirUri = "http://localhost:8000"
scope = "openid email"
response_type = "code"
issuerUrl = oktaInstance
userName = "username@test-domain.com"

def updateKubeConfig(idToken):
	# will take this from the command line or something later:
	commandLine = "kubectl config set-credentials " + userName + " --auth-provider=oidc --auth-provider-arg=idp-issuer-url=" + issuerUrl + " --auth-provider-arg=client-id=" \
				  + client_id + " --auth-provider-arg=client-secret=" + client_secret + " --auth-provider-arg=id-token=" + idToken
	result = os.system(commandLine)
	#print(result)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def exchangeAznCode(azncode):
	print("I'm here")
	heads = {'accept': 'application/json',
				'content-type': 'application/x-www-form-urlencoded'}
	params = {'grant_type': 'authorization_code',
				'redirect_uri': redirUri,
				'code': azncode}
	response = requests.post(tokenEndpoint, headers=heads, auth=HTTPBasicAuth(client_id, client_secret), data=params)
	try:
		jsonResponse = response.json()
		print("id_token post ac exchange: ", jsonResponse.get('id_token'))	
		updateKubeConfig(jsonResponse.get('id_token'))
	except ValueError:
		print("Unable to parse id_token from server response")
	shutdown_server()

def getAznCode():
	azncode = ""
	params = {'client_id': client_id,
			  'redirect_uri': redirUri,
			  'scope': scope,
			  'response_type': response_type,
			  'nonce': str(uuid.uuid4()),
			  'state': str(uuid.uuid4())}
	response = requests.get(aznEndpoint, params=params)
	if (response.status_code != 200):
		print("Azn request failed. Sad face. Error code: ", response.status_code)
		print("The error may be on the queryString: :", response.url)
		shutdown_server()
	else:	
		webbrowser.open(response.url)


getAznCode()

@app.route('/')
def data():
    # here we want to get the value of user (i.e. ?user=some-value)
	azncode = request.args.get('code')
	exchangeAznCode(azncode)
	#return azncode
	return("close... the... tab....")

if __name__=='__main__':
	app.run(port=8000)
