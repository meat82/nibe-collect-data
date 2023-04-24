#
#   This is a Python script to call the NIBE Uplink API which is protected by OAuth2 authentication
#   The necessary OAuth2 Token must have already been allocated and saved to a file called
#   .NIBE_Uplink_API_Token.json in the user's home directory
#
#   For more information see https://www.marshflattsfarm.org.uk/wordpress/?page_id=4988
#
#   Usage:
#       python3  get_parameters_for_categories_for_systems.py
#
#   Pre-requisites:
#     - A suitable OAuth2 Token must have already been allocated and saved to file
#
from os import path
from json import dump, load
from requests_oauthlib import OAuth2Session
import requests
import os

HTTP_STATUS_OK = 200

#   The name of the file used to store the Token needs to be visible within the token_saver() function, so make it a Global Variable
home_dir = path.expanduser('~')
token_filename= home_dir + '/.NIBE_Uplink_API_Token.json'

#   Define a function that will be automatically called to save a new Token when it is refreshed
def token_saver(token):
    with open(token_filename, 'w') as token_file:
        dump(token, token_file)

#   Edit-in your own client_id and client_secret strings below
client_id = os.environ['NIBE_CLIENT_ID'] # (32 hex digits)
client_secret = os.environ['NIBE_CLIENT_SECRET'] # (44 characters)

token_url = 'https://api.nibeuplink.com/oauth/token'

temperature_api_endpoint = "http://localhost:8009/temperatures/add"

#   Read the previously-saved Token from file
with open(token_filename, 'r') as token_file:
    token = load(token_file)

#   Specify the list of extra arguments to include when refreshing a Token
extra_args = {'client_id': client_id, 'client_secret': client_secret}

#   Instantiate an OAuth2Session object (a subclass of Requests.Session) that will be used to query the API
#     - The default Client is of type WebApplicationClient, which is what we want; no need to specify that
#     - The 'client_id' was allocated when the Application was Registered
#     - The 'token' was allocated previously; read-in from a file
#     - The 'auto_refresh_url' says what URL to call to obtain a new Access Token using the Refresh Token
#     - The 'auto_refresh_kwargs' specifies which additional arguments need to be passed when refreshing a Token
#     - The 'token_updater' is the function that will persist the new Token whenever it is refreshed
nibeuplink = OAuth2Session(client_id=client_id, token=token, auto_refresh_url=token_url, auto_refresh_kwargs=extra_args, token_updater=token_saver)

#   Call the NIBE Uplink API - Get a list of the Systems assigned to the authorized user
#   Documentation for this API call is at: https://api.nibeuplink.com/docs/v1/Api/GET-api-v1-systems_page_itemsPerPage
response = nibeuplink.get('https://api.nibeuplink.com/api/v1/systems')
if response.status_code != HTTP_STATUS_OK:
    print('HTTP Status: ' + str(response.status_code))
    print(response.text)
    raise SystemExit('API call not successful')

#   The array of Systems is tagged as 'objects' in the JSON output
systems = response.json()['objects']

for system in systems:
    system_id = system['systemId']

    #   The Unit ID needs to be supplied as an HTTP Parameter in subsequent API calls
    params = {'systemUnitId': 0}
    #   Call the NIBE Uplink API - Get the Parameters for this Category
    #   Documentation for this API call is at: https://api.nibeuplink.com/docs/v1/Api/GET-api-v1-systems-systemId-serviceinfo-categories-categoryId_systemUnitId
    response_category = nibeuplink.get('https://api.nibeuplink.com/api/v1/systems/' + str(system_id) + '/serviceinfo/categories/STATUS', params=params)
    if response_category.status_code != HTTP_STATUS_OK:
        print('HTTP Status: ' + str(response_category.status_code))
        print(response_category.text)
        raise SystemExit('API call not successful')
    parameters = response_category.json()
    for parameter in parameters:
        parameter_id = parameter['parameterId']
        if(parameter_id == 40004):
            parameter_display_value = parameter['displayValue']
            temperature = parameter_display_value[0:len(parameter_display_value)-2]
            # data to be sent to api
            data = {'temperatureValue':temperature}
            # sending post request and saving response as response object
            response_temperature = requests.post(url = temperature_api_endpoint, json = data)
            if response_temperature.status_code != HTTP_STATUS_OK:
                print('HTTP Status: ' + str(response_temperature.status_code))
                print(response_temperature.text)
                raise SystemExit('Temperature API call not successful')
            else:
                print(response_temperature.json())
