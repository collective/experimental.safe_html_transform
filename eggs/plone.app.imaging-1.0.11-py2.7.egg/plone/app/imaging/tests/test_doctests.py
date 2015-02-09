import doctest
from unittest import TestSuite

from plone.app.controlpanel.tests.cptc import ControlPanelTestCase
from Testing import ZopeTestCase as ztc

from plone.app.imaging.tests.base import ImagingFunctionalTestCase
from plone.app.imaging import testing

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


class ImagingControlPanelTestCase(ControlPanelTestCase):
    """ base class for control-panel tests """

    layer = testing.imaging


def test_suite():
    return TestSuite([
        ztc.FunctionalDocFileSuite(
           'traversal.txt', package='plone.app.imaging.tests',
           test_class=ImagingFunctionalTestCase, optionflags=optionflags),
        ztc.FunctionalDocFileSuite(
           'transforms.txt', package='plone.app.imaging.tests',
           test_class=ImagingFunctionalTestCase, optionflags=optionflags),
        ztc.FunctionalDocFileSuite(
           'configlet.txt', package='plone.app.imaging.tests',
           test_class=ImagingControlPanelTestCase, optionflags=optionflags),
    ])
