Detailed documentation
======================



class IMyPackage(Interface):

    field1 = TextLine(title="Field1", default="")
    field2 = TextLine(title="Field2", defualt="Initial value")



#1 - change proposed

XML:
<records interface="my.package.IMyPackage" />
NEW XML:
<record interface="my.package.IMyPackage" />


REGISTRY:
reg['mr.package.IMyPackage.field1'] = ""
reg['mr.package.IMyPackage.field2'] = "Initial value"


#2 - change proposed

XML: 
<records
   name="my-package"
   interface="my.package.IMyPackage" />
NEW XML:
<record
   name="my-package"
   interface="my.package.IMyPackage" />


REGISTRY:
reg['mr-package.field1'] = ""
reg['mr-package.field2'] = "Initial value"


#3 - change proposed

XML:
<records interface="my.package.IMyPackage">
  <omit>field1</omit>
</records>
NEW XML:
<record interface="my.package.IMyPackage">
  <omit>field1</omit>
</record>

REGISTRY:
reg['mr.package.IMyPackage.field2'] = "Initial value"


#4 - is this possible now?

XML:
<record
    interface="my.package.IMyPackage"
    field="field1">
    <value>Some value</value>
</record>

REGISTRY:
reg['my.package.IMyPackage.field1'] = "Some value"


#5 - is this possible now?

XML:
<record
    name="my-package-field1"
    interface="my.package.IMyPackage"
    field="field1">
    <value>Some value</value>
</record>

REGISTRY:
reg['my-package-field1'] = "Some value"


#6 - change proposed

XML:
<record name="my-package.field1">
    <field type="plone.registry.field.TextLine">
        <title>New Field1 title</title>
    </field>
    <value>New value</value>
</record>
NEW XML:
<record name="my-package.field1">
    <field type="TextLine">
        <title>New Field1 title</title>
    </field>
    <value>New value</value>
</record>

REGISTRY:
reg['my-package.field1'] = "Some value"



