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
from lxml import etree
from tempfile import NamedTemporaryFile

config = ConfigParser.ConfigParser()
config.read(os.environ['CKAN_CONFIG'])

MAIN_SECTION = 'app:main'
PLUGIN_SECTION = 'plugin:validation'

SITE_URL = config.get(MAIN_SECTION, 'ckan.site_url')
API_URL = urlparse.urljoin(SITE_URL, 'api/3/')
API_KEY = config.get(PLUGIN_SECTION, 'api_key')
WELIVE_API = config.get(PLUGIN_SECTION, 'welive_api')

JSON_FORMAT = ['json', 'application/json']
XML_FORMAT = ['xml', 'application/xml', 'text/xml']
CSV_FORMAT = ['csv', 'text/comma-separated-values', 'text/csv', 'application/csv']
RDF_FORMAT = ['rdf', 'application/rdf+xml', 'text/plain', 'application/x-turtle', 'text/rdf+n3']

def validate_xml(validation, url):
    r = requests.get(url)
    schema_root = etree.XML(validation)
    schema = etree.XMLSchema(schema_root)
    parser = etree.XMLParser(schema = schema)
    errors = []
    try:
        root = etree.fromstring(r.content, parser)
        return True, errors
    except etree.XMLSyntaxError as e:
        errors.append(e.message)
        return False, errors

def validate_json(validation, url):
    r = requests.get(url)
    schema_dict = eval(validation)
    errors = []
    try:
        jsonschema.validate(r.json(), schema_dict)
        return True, errors
    except jsonschema.ValidationError as e:
        errors.append(e.message)
        return False, errors

def validate_csv(validation, url):
    csv_text = requests.get(url).content
    api_url = WELIVE_API + 'validation/csv'
    files = {'csv': csv_text, 'schema': validation}
    r = requests.post(api_url, files=files)
    errors = r.json()['errors']
    if r.json()['result'] == 'true':
        return True, errors
    else:
        return False, errors

def validate_rdf(url):
    rdf_text = requests.get(url).content
    api_url = WELIVE_API + 'validation/rdf'
    files = {'rdf': rdf_text}
    r = requests.post(api_url, files=files)
    errors = r.json()['errors']
    print errors
    if r.json()['result'] == 'true':
        return True, errors
    else:
        return False, errors


@periodic_task(run_every=timedelta(seconds=5))
def validate():
    res = requests.get(
        API_URL + 'action/package_list',
        headers = {'Authorization': API_KEY,
                   'Content-Type': 'application/json'}
    )
    package_list = res.json()['result']

    for package in package_list:
        res = requests.post(
            API_URL + 'action/package_show', json.dumps({'id': package}),
            headers = {'Authorization': API_KEY,
                       'Content-Type': 'application/json'}
        )
        package = res.json()
        if 'resources' in package['result']:
            for resource in package['result']['resources']:
                # TODO: Check format!!!
                if resource['format'].lower() in JSON_FORMAT or resource['format'].lower() in XML_FORMAT or resource['format'].lower() in CSV_FORMAT or resource['format'].lower() in RDF_FORMAT:
                    last = None
                    last_validation = datetime(1970, 01, 01)
                    if resource['update_time'] == None:
                        last = dateutil.parser.parse(resource['created'])
                    else:
                        last = dateutil.parser.parse(resource['update_time'])
                    if 'validation_time' in resource:
                        last_validation = dateutil.parser.parse(resource['validation_time'])
                    errors = None
                    if (last > last_validation):
                        validation = False
                        if resource['format'].lower() in RDF_FORMAT:
                            validation, errors = validate_rdf(resource['url'])
                        elif resource['format'].lower() in JSON_FORMAT and ('validation' in resource):
                            validation, errors = validate_json(resource['validation'], resource['url'])
                        elif resource['format'].lower() in XML_FORMAT and ('validation' in resource):
                            validation, errors = validate_xml(resource['validation'], resource['url'])
                        elif resource['format'].lower() in CSV_FORMAT and ('validation' in resource):
                            validation, errors = validate_csv(resource['validation'], resource['url'])
                        resource['validated'] = validation
                        resource['validation_time'] = str(datetime.now())
                        if errors != None:
                            resource['validation_errors'] = str(errors)
                        else:
                            resource['validation_errors'] = ""
                        res = requests.post(
                            API_URL + 'action/resource_update', json.dumps(resource),
                            headers = {'Authorization': API_KEY,
                                       'Content-Type': 'application/json'}
                        )
