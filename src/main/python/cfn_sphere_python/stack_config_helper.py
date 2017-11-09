import json
import logging
import os
import boto3

import cfn_sphere


class StackConfigHelper(object):

    def __init__(self, config_file, suffix='it', region=None, tags=None):
        self.logger = cfn_sphere.util.get_logger()
        self.logger.setLevel(logging.INFO)

        self.config_file = config_file
        self.config = self._load_config()
        self.suffix = suffix
        if region is not None:
            self.config['region'] = region
        if tags is not None:
            self.config['tags'] = tags
        self.stack_name_mappings = {}

        self._rename_stacks()

    def _load_config(self):
        with RunInDirectory(self._get_config_file_dir()):
            config = cfn_sphere.file_loader.FileLoader.get_yaml_or_json_file(
                os.path.basename(self.config_file), None)
        return config

    def _get_config_file_dir(self):
        return os.path.dirname(os.path.realpath(self.config_file))

    def update_parameters(self, stack_base_name, parameters):
        '''
        public
        replace and add parameters of given stackname
        '''
        stack_name = self._new_stackname(stack_base_name)
        stack_parameters = self.config['stacks'][stack_name].get('parameters', {})
        for key, value in parameters.items():
            stack_parameters[key] = value
        self.config['stacks'][stack_name]['parameters'] = stack_parameters

    def create_or_update_stacks(self):
        '''
        This wraps the cfn-sphere sync of given stack configs
        '''
        with RunInDirectory(self._get_config_file_dir()):
            self.logger.info('Region: %s, Creating/Updating cfn stacks from %s',
                             self.config['region'], self.config_file)
            self.logger.debug('new config: \n %s',
                              json.dumps(self.config, indent=2))
            cfn_sphere.StackActionHandler(
                config=self._create_stack_config()).create_or_update_stacks()
        return self

    def delete_stacks(self):
        '''
        This wraps the cfn-sphere delete of given stack configs
        '''
        cfn_sphere.StackActionHandler(
            config=self._create_stack_config()).delete_stacks()

    def _create_stack_config(self):
        return cfn_sphere.stack_configuration.Config(config_dict=self.config)

    def update_references(self, mapping):
        '''
        public
        updates all cross references in all stack configs
        mapping contains stack names to update
        '''
        for stack_name, stack_config in self.config['stacks'].items():
            new_stack_config = self._rename_stack_references(stack_config, mapping)
            self.config['stacks'][stack_name] = new_stack_config

    def _rename_stacks(self):
        '''
        rename stacks with adding suffix
        renames refs to stacks too
        '''
        new_stacks = {}
        for name, value in self.config['stacks'].items():
            new_name = self._new_stackname(name)
            new_stacks[new_name] = value
            self.stack_name_mappings[name] = new_name
        for stack_name, stack_config in new_stacks.items():
            new_stacks[stack_name] = self._rename_stack_references(
                stack_config, self.stack_name_mappings)
        self.config['stacks'] = new_stacks

    def _rename_stack_references(self, stack_config, mapping):
        if ('parameters' not in stack_config
                or not stack_config['parameters']
                or not mapping):
            return stack_config

        new_stack_config = stack_config
        for key, value in stack_config['parameters'].items():
            if isinstance(value, (str, unicode)) and value.lower().startswith('|ref|'):
                ref = value.split('|', 2)[2]
                for old, new in mapping.items():
                    if ref.startswith('{}.'.format(old)):
                        new_stack_config['parameters'][key] = '|ref|{}{}'.format(
                            new, ref[len(old):])
                        break
        return new_stack_config

    def get_stack_output(self, base_stack_name, key):
        response = boto3.client('cloudformation').describe_stacks(
            StackName=self._new_stackname(base_stack_name))
        outputs = response['Stacks'][0]['Outputs']
        return [o['OutputValue'] for o in outputs if o['OutputKey'] == key][0]

    def _new_stackname(self, name):
        return '{}-{}'.format(name, self.suffix) if self.suffix else name

    def get_shortest_stack_basename(self):
        shortest_stack_name = None
        for stack_name, _ in self.config['stacks'].items():
            if not shortest_stack_name or len(stack_name) < len(shortest_stack_name):
                shortest_stack_name = stack_name
        basename = [old for old, new in self.stack_name_mappings.items() if new ==
                    shortest_stack_name][0]
        return basename


class RunInDirectory(object):

    def __init__(self, new_pwd):
        self.new_pwd = new_pwd
        self.old_pwd = None

    def __enter__(self):
        self.old_pwd = os.getcwd()
        os.chdir(self.new_pwd)

    def __exit__(self, *_):
        os.chdir(self.old_pwd)
