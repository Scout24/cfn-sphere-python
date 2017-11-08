from __future__ import print_function, absolute_import, division

import copy
import unittest2 as unittest
from mock import patch

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
            obj = StackConfigHelper(config_file='foo')
        return obj

    @patch('cfn_sphere_python.stack_config_helper.StackConfigHelper._rename_stacks')
    def test_init__with_minimal_parameters(self, rename_stacks):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        rename_stacks.assert_called_once()

        self.assertEqual(SIMPLE_SMALL_CONFIG, stacks_config.config)
        self.assertEqual('eu-west-4', stacks_config.config['region'])
        self.assertEqual({'one': 'two'}, stacks_config.config['tags'])

    def test_init__default_suffix_and_set_mappings(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        self.assertEqual({'foo': 'foo-it', 'bar': 'bar-it'},
                         stacks_config.stack_name_mappings)

    @patch('cfn_sphere_python.stack_config_helper.StackConfigHelper._rename_stacks')
    def test_init__with_all_parameters_set_which_overrides_config(self, rename_stacks):
        with patch('cfn_sphere_python.stack_config_helper.StackConfigHelper._load_config') as load_config_mock:
            load_config_mock.return_value = copy.deepcopy(FIRST_TEST_CONFIG)
            stacks_config = StackConfigHelper(
                config_file='foo',
                suffix='bar',
                region='eu-central-2',
                tags={'foo': 'bar'})

            rename_stacks.assert_called_once()
            # suffix, region and tags will be overridden by given values
            self.assertEqual('bar', stacks_config.suffix)
            self.assertEqual({'foo': 'bar'}, stacks_config.config['tags'])
            self.assertEqual('eu-central-2', stacks_config.config['region'])

    def test_update_parameters_adding_to_empty(self):
        stacks_config = self.get_stack_config_helper(FIRST_TEST_CONFIG)
        self.assertIsNone(self.get_stack_parameters(stacks_config, 'foo'))
        stacks_config.update_parameters('foo', {'bar': 'tender'})
        self.assertEqual({'bar': 'tender'},
                         self.get_stack_parameters(stacks_config, 'foo'))

    def test_update_parameters_replace_and_add(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        self.assertEqual({
            'vpc': '123456'
        }, self.get_stack_parameters(stacks_config, 'foo'))
        stacks_config.update_parameters('foo', {'bar': 'tender', 'vpc': '654321'})
        self.assertEqual({'vpc': '654321', 'bar': 'tender'},
                         self.get_stack_parameters(stacks_config, 'foo'))
        # the other is untouched
        self.assertIsNone(self.get_stack_parameters(stacks_config, 'bar'))

    @staticmethod
    def get_stack_parameters(stacks_config, stack_basename):
        config = stacks_config.config['stacks'][stacks_config._new_stackname(stack_basename)]
        return config.get('parameters', None)

    def test_update_references(self):
        stacks_config = self.get_stack_config_helper(SECOND_TEST_CONFIG)
        stacks_config.update_references({'foo': 'new_foo'})
        self.assertEqual({'ref': '|ref|new_foo.output'},
                         self.get_stack_parameters(stacks_config, 'lorum'))

    def test_update_references_w_empty_mapping(self):
        stacks_config = self.get_stack_config_helper(SECOND_TEST_CONFIG)
        stacks_config.update_references({})
        self.assertEqual({'ref': '|ref|foo.output'},
                         self.get_stack_parameters(stacks_config, 'lorum'))

    @patch('cfn_sphere_python.stack_config_helper.StackConfigHelper._rename_stack_references')
    def test__rename_stacks(self, rename_refs_mock):
        stacks_config = self.get_stack_config_helper(FIRST_TEST_CONFIG)
        self.assertEqual(rename_refs_mock.call_count, 2)
        # after init the stacknames are already renamed
        new_stack_names = [k for k, v in stacks_config.config['stacks'].iteritems()]
        self.assertEqual(['foo-it', 'foo-one-it'], new_stack_names)
        self.assertEqual({'foo': 'foo-it', 'foo-one': 'foo-one-it'},
                         stacks_config.stack_name_mappings)

    def test__rename_stack_references(self):
        stacks_config = self.get_stack_config_helper(FIRST_TEST_CONFIG)
        # current stacknames with new ones
        mapping = {'foo-it': 'foo-new', 'foo-one-it': 'foo-one-new'}
        result = stacks_config._rename_stack_references(
            stacks_config.config['stacks']['foo-one-it'], mapping)
        self.assertEqual({'parameters': {
            'param': 'value',
            'num': 1234,
            'ref': '|ref|foo-new.output'
        }}, result)

    def test_get_stack_output(self):
        # TODO
        pass

    def test__new_stackname(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        self.assertEqual('foo-it', stacks_config._new_stackname('foo'))

    def test__new_stackname_no_suffix(self):
        stacks_config = self.get_stack_config_helper(SIMPLE_SMALL_CONFIG)
        stacks_config.suffix = None
        self.assertEqual('foo', stacks_config._new_stackname('foo'))

    def test_get_shortest_stack_basename(self):
        stacks_config = self.get_stack_config_helper(FIRST_TEST_CONFIG)
        self.assertEqual('foo', stacks_config.get_shortest_stack_basename())
        stacks_config = self.get_stack_config_helper(SECOND_TEST_CONFIG)
        self.assertEqual('lorum', stacks_config.get_shortest_stack_basename())


if __name__ == '__main__':
    unittest.main()
