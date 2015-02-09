from Products.CMFCore.utils import getToolByName

js_date_input_id = '++resource++plone.app.jquerytools.dateinput.js'
css_date_input_id = '++resource++plone.app.jquerytools.dateinput.css'

def importVarious(context):
    """Enable plone.app.jquerytools dateinput js and css resources
       in portal_javascripts and portal_css
    """
    if context.readDataFile('collective.z3cform.datetimewidget.txt') is None:
        return

    site = context.getSite()
    
#    print "Enabling %s" % js_date_input_id
    jsrr = getToolByName(site, 'portal_javascripts')
    if js_date_input_id in jsrr.getResourceIds():
        jsrr.updateScript(js_date_input_id, enabled=True)

#    print "Enabling %s" % css_date_input_id
    cssrr = getToolByName(site, 'portal_css')
    if css_date_input_id in cssrr.getResourceIds():
        cssrr.updateStylesheet(css_date_input_id, enabled=True)
    
