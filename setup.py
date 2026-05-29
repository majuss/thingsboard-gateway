# -*- coding: utf-8 -*-

#     Copyright 2026. ThingsBoard
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from setuptools import setup
from os import path

from thingsboard_gateway import version

current_directory = path.abspath(path.dirname(__file__))
with open(path.join(current_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    version=version.VERSION,
    name="thingsboard-gateway",
    author="ThingsBoard",
    author_email="info@thingsboard.io",
    license="Apache Software License (Apache Software License 2.0)",
    description="Thingsboard Gateway for IoT devices.",
    url="https://github.com/thingsboard/thingsboard-gateway",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires=">=3.10",
    packages=['thingsboard_gateway', 'thingsboard_gateway.gateway',
              'thingsboard_gateway.gateway.entities',
              'thingsboard_gateway.gateway.shell',
              'thingsboard_gateway.gateway.statistics',
              'thingsboard_gateway.storage', 'thingsboard_gateway.storage.memory',
              'thingsboard_gateway.gateway.report_strategy', 'thingsboard_gateway.storage.file',
              'thingsboard_gateway.storage.sqlite',
              'thingsboard_gateway.connectors',
              'thingsboard_gateway.connectors.bacnet', 'thingsboard_gateway.connectors.bacnet.entities',
              'thingsboard_gateway.extensions', 'thingsboard_gateway.extensions.bacnet',
              'thingsboard_gateway.extensions.bacnet.proprietary',
              'thingsboard_gateway.tb_utility',
              ],
    install_requires=[
        'setuptools',
        'cryptography',
        'jsonpath-rw',
        'regex',
        'PyYAML',
        'orjson',
        'pybase64',
        'simplejson',
        'urllib3>=2.3.0',
        'requests>=2.32.3',
        'mmh3',
        'python-dateutil',
        'cachetools',
        'tb-paho-mqtt-client>=2.1.2',
        'tb-mqtt-client==1.13.13',
        'packaging>=23.1',
        'service-identity',
        'psutil',
        'PySocks',
        'bacpypes3',
    ],
    download_url='https://github.com/thingsboard/thingsboard-gateway/archive/%s.tar.gz' % version.VERSION,
    entry_points={
        'console_scripts': [
            'thingsboard-gateway = thingsboard_gateway.tb_gateway:daemon',
        ]
    })
