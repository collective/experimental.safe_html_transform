from doctest import ELLIPSIS

from Testing.ZopeTestCase import ZopeDocFileSuite

from Products.contentmigration.tests.cmtc import SchemaExtenderMigratorTestCase


def test_suite():
    try:
        import archetypes.schemaextender
        archetypes.schemaextender  # pyflakes
    except ImportError:
        # No tests
        suites = ZopeDocFileSuite()
    else:
        suites = (
            ZopeDocFileSuite(
                '../schemaextender.txt',
                package='Products.contentmigration.tests',
                optionflags=ELLIPSIS,
                test_class=SchemaExtenderMigratorTestCase),
            )

    from unittest import TestSuite
    return TestSuite(suites)
