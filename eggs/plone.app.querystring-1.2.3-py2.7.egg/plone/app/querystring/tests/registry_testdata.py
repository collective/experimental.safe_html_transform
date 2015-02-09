# -*- coding: utf-8 -*-
import os

parsed_correct = {
    'plone': {
        'app': {
            'querystring': {
                'field': {
                    'getId': {
                        'operations': [
                            'plone.app.querystring.operation.string.is'],
                        'group': u'Metadata',
                        'description': u'The short name of an item '
                                       u'(used in the url)',
                        'vocabulary': None,
                        'title': u'Short Name',
                        'enabled': True,
                        'sortable': True
                    },
                    'created': {
                        'operations': [
                            'plone.app.querystring.operation.date.lessThan',
                            'plone.app.querystring.operation.date.largerThan'
                        ],
                        'group': u'Dates',
                        'description': u'The time and date an item was '
                                       u'created',
                        'vocabulary': None,
                        'title': u'Creation Date',
                        'enabled': True,
                        'sortable': False
                    }
                },
                'operation': {
                    'date': {
                        'largerThan': {
                            'widget': None,
                            'operation': u'plone.app.querystring.queryparser'
                                         u'._largerThan',
                            'description': u'Please use YYYY/MM/DD.',
                            'title': u'after'
                        },
                        'lessThan': {
                            'widget': None,
                            'operation': u'plone.app.querystring.queryparser.'
                                         u'_lessThan',
                            'description': u'Please use YYYY/MM/DD.',
                            'title': u'before'
                        }
                    },
                    'string': {
                        'is': {
                            'widget': None,
                            'operation': u'plone.app.querystring.queryparser.'
                                         u'_equal',
                            'description': u'Tip: you can use * to '
                                           u'autocomplete.',
                            'title': u'equals'
                        }
                    }
                }
            }
        }
    }
}


def reg_load_xml(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as rx:
        return rx.read()

minimal_correct_xml = reg_load_xml('registry_minimal_correct.xml')
test_missing_operator_xml = reg_load_xml('registry_test_missing_operator.xml')
test_vocabulary_xml = reg_load_xml('registry_test_vocabulary.xml')
