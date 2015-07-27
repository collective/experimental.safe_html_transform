# -*- coding: utf-8 -*-
"""Installer for the experimental.safe_html_transform package."""

from setuptools import find_packages
from setuptools import setup


long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')


setup(
    name='experimental.safe_html_transform',
    version='0.1',
    description="Experimental safe_html transform for Plone.",
    long_description=long_description,
    # Get more from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3.4",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='Plone Python',
    author='Timo Stollenwerk',
    author_email='tisto@plone.org',
    url='http://pypi.python.org/pypi/experimental.safe_html_transform',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['experimental'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'plone.api',
        'setuptools',
        'z3c.jbot',
        'plone.app.registry',
        'Products.MimetypesRegistry',
        'Products.PortalTransforms',
        'Products.CMFPlone',
    ],
    extras_require={
        'test': [
            'plone.app.testing',
            'plone.app.contenttypes',
            'plone.app.robotframework[debug]',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
