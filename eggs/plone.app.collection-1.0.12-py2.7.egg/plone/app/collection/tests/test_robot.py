# -*- coding: utf-8 -*-
import os
import unittest

from plone.testing import layered

from plone.app.collection.testing import PLONEAPPCOLLECTION_ROBOT_TESTING

import robotsuite


def test_suite():
    suite = unittest.TestSuite()
    current_dir = os.path.abspath(os.path.dirname(__file__))
    robot_dir = os.path.join(current_dir, 'robot')
    robot_tests = [
        'robot/{0}'.format(doc) for doc in os.listdir(robot_dir) if doc.endswith('.robot')
    ]
    for test in robot_tests:
        suite.addTests([
            layered(
                robotsuite.RobotTestSuite(test),
                layer=PLONEAPPCOLLECTION_ROBOT_TESTING
            ),
        ])
    return suite
