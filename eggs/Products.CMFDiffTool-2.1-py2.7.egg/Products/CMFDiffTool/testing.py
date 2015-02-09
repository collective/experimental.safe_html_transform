#coding=utf8
from plone.dexterity.fti import DexterityFTI
from Products.CMFCore.utils import getToolByName
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.component import getSiteManager
from zope.schema.interfaces import IVocabularyFactory

from collective.testcaselayer import ptc
from collective.testcaselayer import common

TEST_CONTENT_TYPE_ID = 'TestContentType'

VOCABULARY_TUPLES = [
    (u'first_value', u'First Title'),
    (u'second_value', None),
]

VOCABULARY = SimpleVocabulary(
    [SimpleTerm(value=v, title=t) for (v, t) in VOCABULARY_TUPLES])


def vocabulary_factory(context):
    return VOCABULARY


class PackageLayer(ptc.BasePTCLayer):

    def afterSetUp(self):
        import Products.CMFDiffTool
        import plone.app.dexterity
        self.loadZCML('configure.zcml', package=Products.CMFDiffTool)
        self.loadZCML('configure.zcml', package=plone.app.dexterity)

        portal = self.portal
        types_tool = getToolByName(portal, 'portal_types')

        sm = getSiteManager(portal)
        sm.registerUtility(
            component=vocabulary_factory,
            provided=IVocabularyFactory,
            name=u'Products.CMFDiffTool.testing.VOCABULARY'
        )

        fti = DexterityFTI(
            TEST_CONTENT_TYPE_ID,
            factory=TEST_CONTENT_TYPE_ID,
            global_allow=True,
            behaviors=(
                'plone.app.versioningbehavior.behaviors.IVersionable',
                'plone.app.dexterity.behaviors.metadata.IBasic',
                'plone.app.dexterity.behaviors.metadata.IRelatedItems',
            ),
            model_source='''
            <model xmlns="http://namespaces.plone.org/supermodel/schema">
                <schema>
                    <field name="text" type="zope.schema.Text">
                        <title>Text</title>
                        <required>False</required>
                    </field>
                    <field name="file" type="plone.namedfile.field.NamedFile">
                        <title>File</title>
                        <required>False</required>
                    </field>
                    <field name="date" type="zope.schema.Date">
                        <title>Date</title>
                        <required>False</required>
                    </field>
                    <field name="files" type="zope.schema.List">
                        <title>Date</title>
                        <required>False</required>
                        <value_type type="plone.namedfile.field.NamedFile">
                            <title>Val</title>
                        </value_type>
                    </field>
                    <field name="choice" type="zope.schema.Choice">
                        <title>Choice</title>
                        <required>False</required>
                        <vocabulary>Products.CMFDiffTool.testing.VOCABULARY</vocabulary>
                    </field>
                </schema>
            </model>
            '''
        )
        types_tool._setObject(TEST_CONTENT_TYPE_ID, fti)

package_layer = PackageLayer([common.common_layer])
