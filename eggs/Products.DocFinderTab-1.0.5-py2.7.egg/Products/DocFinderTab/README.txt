DocFinderTab
============

This product makes Dieter Maurer's DocFinder_ available from a ZMI management
tab. Looking inside an object becomes as easy as clicking its "Doc" tab!

DocFinderTab allows you to view an object's:

- Class (and base class) names and docstrings.

- Attribute names, roles, arguments, and docstrings.

DocFinderTab can be of great help when discovering object APIs and debugging
security problems.

.. _DocFinder: http://www.dieter.handshake.de/pyprojects/zope/DocFinder.html

Egg Installation
================

Either use easy_install or add Products.DocFinderTab to the eggs section of
your buildout.cfg and re-run buildout.

Traditional Product Installation
================================

Copy or symlink the DocFinderTab subdirectory of this package into your
Products directory.

Final Steps
===========

Restart Zope. This will add a "Doc" tab to every object's managment
screens (ZMI). Now click the "Doc" tab and start exploring.

See the online help for a detailed explanation of what you can
do with DocFinderTab, or read help/README.stx directly.

