from pybuilder.core import use_plugin, init, Author

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "cfn-sphere-python"
authors = [Author('Felix Borchers', 'felix.borcher@gmail.com')]
description = "cfn-sphere-python - A python wrapper for cfn-sphere to simplify the use of cfn-sphere stacks configs in python."
license = 'APACHE LICENCE, VERSION 2.0'
summary = 'cfn-sphere-python Python Wrapper for AWS CloudFormation management tool cfn-sphere'
url = 'https://github.com/ImmobilienScout24/cfn-sphere-python'
version = '0.2'

default_task = ['clean', 'analyze', 'package']


@init
def set_properties(project):
    project.build_depends_on("unittest2")
    project.build_depends_on("mock")
    project.build_depends_on("moto")
    project.depends_on("boto3")
    project.depends_on("cfn-sphere")

    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration'
    ])
    project.set_property('coverage_threshold_warn', 60)
