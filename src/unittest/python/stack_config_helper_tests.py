from __future__ import print_function, absolute_import, division

import copy
import boto3
import unittest2 as unittest
from mock import patch
from moto import mock_cloudformation

from cfn_sphere_python.stack_config_helper import StackConfigHelper

SIMPLE_SMALL_CONFIG = {
    'region': 'eu-west-4',
    'tags': {'one': 'two'},
    'stacks': {
        'foo': {
            'parameters': {
                'vpc': '123456'
            }
        },
        'bar': {}
    }
}
# two stacks in one config, with one cross reference
FIRST_TEST_CONFIG = {
    'region': 'eu-west-1',
    'tags': {
        'one': 'two',
        'three': 'four'
    },
    'stacks': {
        'foo': {},
        'foo-one': {
            'parameters': {
                'param': 'value',
                'num': 1234,
                'ref': '|ref|foo.output'
            }
        }
    }
}
# This contains a cross reference to one of the FIRST_TEST_CONFIG stacks
SECOND_TEST_CONFIG = {
    'region': 'eu-west-1',
    'stacks': {
        'lorum': {
            'parameters': {
                'ref': '|ref|foo.output'
            }
        }
    }
}


class StackConfigHelperTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    @staticmethod
    def get_stack_config_helper(test_config):
        obj = None
        with patch('cfn_sphere_python.stack_config_helper.StackConfigHelper._load_config') as load_config_mock:
            load_config_mock.return_value = copy.deepcopy(test_config)
            obj = StackConfigHelper(config_file='foo', suffix='-it')
        return obj

    def test_update_parameters(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        stacks_config.update_parameters('foo', {'vpc': 'foo'})
        print(stacks_config.config)
        self.assertEqual('foo', stacks_config.config['stacks']['foo']['parameters']['vpc'])

    def test_init__with_minimal_parameters(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)

        self.assertEqual(SIMPLE_SMALL_CONFIG, stacks_config.config)
        self.assertEqual('eu-west-4', stacks_config.config['region'])
        self.assertEqual({'one': 'two'}, stacks_config.config['tags'])

    def test_init__with_all_parameters_set_which_overrides_config(self):
        with patch('cfn_sphere_python.stack_config_helper.StackConfigHelper._load_config') as load_config_mock:
            load_config_mock.return_value = copy.deepcopy(FIRST_TEST_CONFIG)
            stacks_config = StackConfigHelper(
                config_file='foo',
                suffix='bar',
                region='eu-central-2',
                tags={'foo': 'bar'})

            # suffix, region and tags will be overridden by given values
            self.assertEqual('bar', stacks_config.suffix)
            self.assertEqual({'foo': 'bar'}, stacks_config.config['tags'])
            self.assertEqual('eu-central-2', stacks_config.config['region'])

    def test__new_stackname(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        self.assertEqual('foo-it', stacks_config._new_stackname('foo'))

    def test__new_stackname_no_suffix(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        stacks_config.suffix = None
        self.assertEqual('foo', stacks_config._new_stackname('foo'))


if __name__ == '__main__':
    unittest.main()
