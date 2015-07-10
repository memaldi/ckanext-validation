import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class ValidationPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IConfigurer)

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
