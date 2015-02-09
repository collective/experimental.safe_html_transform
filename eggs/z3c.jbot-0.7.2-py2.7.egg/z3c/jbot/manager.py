from zope import interface

import os
import sys

import utility
import interfaces

IGNORE = object()
DELETE = object()

def root_length(a, b):
    if b.startswith(a):
        return len(a)
    else:
        return 0

def sort_by_path(path, paths):
    return sorted(
        paths, key=lambda syspath: root_length(syspath, path), reverse=True)

def find_zope2_product(path):
    """Check the Zope2 magic Products semi-namespace to see if the
    path is part of a Product."""

    _syspaths = sort_by_path(path, sys.modules["Products"].__path__)
    syspath = _syspaths[0]

    if not path.startswith(syspath):
        return None

    product = path[len(syspath)+1:].split(os.path.sep, 2)[0]

    return "Products." + product


def find_package(syspaths, path):
    """Determine the Python-package where path is located.  If the path is
    not located within the Python sys-path, return ``None``."""

    _syspaths = sort_by_path(path, syspaths)
    syspath = _syspaths[0]

    path = os.path.normpath(path)
    if not path.startswith(syspath):
        if utility.ZOPE_2:
            return find_zope2_product(path)
        return None

    path = path[len(syspath):]

    # convert path to dotted filename
    if path.startswith(os.path.sep):
        path = path[1:]

    return path

class TemplateManagerFactory(object):
    def __init__(self, name):
        self.manager = TemplateManager(name)

    def __call__(self, layer):
        return self.manager

class TemplateManager(object):
    interface.implements(interfaces.ITemplateManager)

    def __init__(self, name):
        self.syspaths = tuple(sys.path)
        self.templates = {}
        self.paths = {}
        self.directories = set()
        self.name = name

    def registerDirectory(self, directory):
        self.directories.add(directory)

        for filename in os.listdir(directory):
            self.paths[filename] = "%s/%s" % (directory, filename)

        for template, filename in self.templates.items():
            if filename is IGNORE:
                del self.templates[template]

    def unregisterDirectory(self, directory):
        self.directories.remove(directory)

        templates = []

        for template, filename in self.templates.items():
            if filename in self.paths:
                templates.append(template)

        for filename in os.listdir(directory):
            if filename in self.paths:
                del self.paths[filename]

        for template in templates:
            inst = template.__get__(self)
            self.registerTemplate(inst, template)
            del self.templates[template]
            inst.filename = inst._filename

    def unregisterAllDirectories(self):
        for directory in tuple(self.directories):
            self.unregisterDirectory(directory)

    def registerTemplate(self, template, token):
        # assert that the template is not already registered
        filename = self.templates.get(token)
        if filename is IGNORE:
            return

        # if the template filename matches an override, we're done
        paths = self.paths
        if paths.get(filename) == template.filename:
            return

        # verify that override has not been unregistered
        if filename is not None and filename not in paths:
            template.filename = template._filename
            del self.templates[token]

        # check if an override exists
        path = find_package(self.syspaths, template.filename)
        if path is None:
            # permanently ignore template
            self.templates[token] = IGNORE
            return

        filename = path.replace(os.path.sep, '.')
        if filename not in paths:
            self.templates[token] = IGNORE
            return

        path = paths[filename]

        # save original filename
        template._filename = template.filename

        # save template and registry and assign path
        template.filename = path
        self.templates[token] = filename

        return True
