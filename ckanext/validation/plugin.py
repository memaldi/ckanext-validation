import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import uuid
import ckan.model
from ckan.lib.celery_app import celery
from ckan.lib.base import model
from ckan.model.resource import Resource
import ConfigParser
import os
import json
import requests
import datetime


class ValidationPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceController)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'validation')

    def _modify_package_schema(self, schema):
        schema['resources'].update(
            {'validation': [toolkit.get_validator('ignore_missing')]}
        )
        schema['resources'].update(
            {'validated': [toolkit.get_validator('ignore_missing')]}
        )
        schema['resources'].update(
            {'update_time': [toolkit.get_validator('ignore_missing')]}
        )
        schema['resources'].update(
            {'validation_time': [toolkit.get_validator('ignore_missing')]}
        )
        schema['resources'].update(
            {'validation_errors': [toolkit.get_validator('ignore_missing')]}
        )
        return schema

    def create_package_schema(self):
        schema = super(ValidationPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(ValidationPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(ValidationPlugin, self).show_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def after_update(self, context, resource):
        pass

    def before_update(self, context, current, resource):
        if 'for_edit' in context:
            resource['update_time'] = str(datetime.datetime.now())

    def before_show(self, resource_dict):
        if 'validation_errors' in resource_dict:
            if resource_dict['validation_errors'] != "":
                resource_dict['validation_errors_dict'] = eval(
                    resource_dict['validation_errors']
                )
            else:
                resource_dict['validation_errors_dict'] = None

    def before_create(self, context, resource):
        resource['update_time'] = str(datetime.datetime.now())

    def after_create(self, context, resource):
        pass

    def before_delete(self, context, resource, resources):
        pass

    def after_delete(self, context, resources):
        pass
