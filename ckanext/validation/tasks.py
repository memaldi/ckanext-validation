import pylons
import ConfigParser
import os
from ckan.lib.celery_app import celery
import jsonschema
import json
import requests
import urlparse
from datetime import timedelta, datetime
from celery.decorators import periodic_task
import dateutil.parser

config = ConfigParser.ConfigParser()
config.read(os.environ['CKAN_CONFIG'])

MAIN_SECTION = 'app:main'
PLUGIN_SECTION = 'plugin:validation'

SITE_URL = config.get(MAIN_SECTION, 'ckan.site_url')
API_URL = urlparse.urljoin(SITE_URL, 'api/3/')
API_KEY = config.get(PLUGIN_SECTION, 'api_key')

JSON_FORMAT = ['json', 'application/json']

LAST_VALIDATION = datetime.now()

def validate_json(validation, url):
    r = requests.get(url)
    schema_dict = eval(validation)
    try:
        jsonschema.validate(r.json(), schema_dict)
        return True
    except jsonschema.ValidationError:
        return False

#@celery.task(name = "validation.validate")
@periodic_task(run_every=timedelta(seconds=5))
def validate():
    res = requests.get(
        API_URL + 'action/package_list',
        headers = {'Authorization': API_KEY,
                   'Content-Type': 'application/json'}
    )
    package_list = res.json()['result']

    for package in package_list:
        print package
        res = requests.post(
            API_URL + 'action/package_show', json.dumps({'id': package}),
            headers = {'Authorization': API_KEY,
                       'Content-Type': 'application/json'}
        )
        package = res.json()
        if 'resources' in package['result']:
            for resource in package['result']['resources']:
                last = None
                if resource['last_modified'] == None:
                    last = dateutil.parser.parse(resource['created'])
                else:
                    last = dateutil.parser.parse(resource['last_modified'])

                # print last
                # print LAST_VALIDATION
                # print last > LAST_VALIDATION
                # if (last > LAST_VALIDATION) and ('validation' in resource):
                validation = validate_json(resource['validation'], resource['url'])
                print validation


    # res = requests.post(
    #     API_URL + 'action/resource_show', json.dumps({'id': resource_id}),
    #     headers = {'Authorization': API_KEY,
    #                'Content-Type': 'application/json'}
    # )
    # json_res = json.loads(res.content)
    # if 'result' in json_res:
    #     resource = json_res['result']
    #     if 'format' in resource:
    #         if (resource['format'].lower() in JSON_FORMAT) and ('validation' in resource):
    #             validated = validate_json(resource)
    #             resource['validated'] = validated
    #             res = requests.post(
    #                 API_URL + 'action/resource_update', json.dumps(resource),
    #                 headers = {'Authorization': API_KEY,
    #                            'Content-Type': 'application/json'}
    #             )
