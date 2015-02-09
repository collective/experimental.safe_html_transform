from doctest import DocTestSuite
from unittest import TestSuite


def test_suite():
    return TestSuite((
        DocTestSuite('Products.statusmessages.adapter'),
        DocTestSuite('Products.statusmessages.message'),
        ))
