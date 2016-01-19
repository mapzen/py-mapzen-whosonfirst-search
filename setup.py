#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
version = open("VERSION").read()
desc = open("README.md").read(),

setup(
    name='mapzen.whosonfirst.search',
    namespace_packages=['mapzen', 'mapzen.whosonfirst', 'mapzen.whosonfirst.search'],
    version=version,
    description='Simple Python wrapper for Who\'s On First search functionality',
    author='Mapzen',
    url='https://github.com/mapzen/py-mapzen-whosonfirst-search',
    install_requires=[
        'geojson',
        'elasticsearch',
        'slack.api>=0.4',	# https://github.com/whosonfirst/py-slack-api
        'mapzen.whosonfirst.utils>=0.17',
        'mapzen.whosonfirst.placetypes>=0.11'
        ],
    dependency_links=[
        'https://github.com/whosonfirst/py-slack-api/tarball/master#egg=slack.api-0.4',
        'https://github.com/whosonfirst/py-mapzen-whosonfirst-utils/tarball/master#egg=mapzen.whosonfirst.utils-0.17',
        'https://github.com/whosonfirst/py-mapzen-whosonfirst-placetypes/tarball/master#egg=mapzen.whosonfirst.placetypes-0.11'
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
    download_url='https://github.com/mapzen/py-mapzen-whosonfirst-search/releases/tag/' + version,
    license='BSD')
