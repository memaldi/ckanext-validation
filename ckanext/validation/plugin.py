import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import uuid
import ckan.model
from ckan.lib.celery_app import celery


class ValidationPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IMapper)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'validation')

    def _modify_package_schema(self, schema):
        schema['resources'].update({
                'validation' : [ toolkit.get_validator('ignore_missing') ]
                })
        schema['resources'].update({
                'validated' : [ toolkit.get_validator('ignore_missing') ]
                })
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
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def launch_validation_task(self, mapper, connection, instance):
        if type(instance) is ckan.model.resource.Resource:
            celery.send_task("validation.validate", args=[instance.id], task_id=str(uuid.uuid4()))

    def after_update(self, mapper, connection, instance):
        self.launch_validation_task(mapper, connection, instance)

    def after_insert(self, mapper, connection, instance):
        self.launch_validation_task(mapper, connection, instance)

    def after_delete(self, mapper, connection, instance):
        pass

    def before_insert(self, mapper, connection, instance):
        pass

    def before_update(self, mapper, connection, instance):
        pass

    def before_delete(self, mapper, connection, instance):
        pass
