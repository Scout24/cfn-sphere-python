## cfn-sphere-python

[![Build Status](https://travis-ci.org/ImmobilienScout24/cfn-sphere-python.svg?branch=master)](https://travis-ci.org/ImmobilienScout24/cfn-sphere-python)

[![Code Health](https://landscape.io/github//ImmobilienScout24/cfn-sphere-python/master/landscape.svg?style=flat)](https://landscape.io/github/ImmobilienScout24/cfn-sphere-python/master)

# This project is DEPRECATED and not any longer supported

Wrapper for using cfn-sphere stacks configuration with python.
I developed this to (integration)test [https://github.com/cfn-sphere/cfn-sphere](cfn-sphere) stacks configs within python scripts, instead of using bash.

The contained StackConfigHelper class is a python wrapper for syncing [https://github.com/cfn-sphere/cfn-sphere](cfn-sphere)
style stacks config to AWS.
It is like doing: ```cf sync -y cfn/dms.stacks.yaml``` in python.
Additionally you can change the stacks config programatically w/o changing
your config file.

# Features

- renaming all stacks with a suffix
  cross referencing parameters between stacks will be renamed too
- adding or changing parameters of a stack
- getting outputs of a stack
- changing the region to deploy
- replacing tags

# example usage

Create a config from a cfn-sphere yaml file with suffix the stacksnames with 'test':
```
from cfn_sphere_python.stack_config_helper import StackConfigHelper

config = StackConfigHelper(config_file='cfn/stacks.yaml', suffix='test')
```
to update some parameters call this
```
config.update_parameters('stack_basename', parameter_dict)
```

You can create the stacks (this is the same as calling ```cf sync cfn/stacks.yaml```):
```
config.create_or_update_stacks()
```
To retrieve outputs of a stack:
```
config.get_stack_output('stack_basename','host')
```
To update all stack cross references:
```
config.update_references({'old_stackname': 'new_stackname'})
```
To delete all stacks:
```
config.delete_stacks()
```

# related projects

* [https://github.com/cfn-sphere/cfn-sphere](cfn-sphere)
