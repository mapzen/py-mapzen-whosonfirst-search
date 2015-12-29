#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
desc = open("README.md").read(),

setup(
    name='mapzen.whosonfirst.search',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.search'],
    version='0.12',
    description='Simple Python wrapper for Who\'s On First search functionality',
    author='Mapzen',
    url='https://github.com/mapzen/py-mapzen-whosonfirst-search',
    install_requires=[
        'geojson',
        'elasticsearch',
        'slack.api>=0.4'	# https://github.com/whosonfirst/py-slack-api
        ],
    dependency_links=[
        'https://github.com/whosonfirst/py-slack-api/tarball/master#egg=slack.api-0.4',
        ],
    packages=packages,
    scripts=[
        'scripts/wof-es-id',
        'scripts/wof-es-index',
        'scripts/wof-es-index-files',
        'scripts/wof-es-index-filelist',
        'scripts/wof-es-prepare',
        'scripts/wof-es-rawquery',
        ],
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-search/releases/tag/v0.12',
    license='BSD')
