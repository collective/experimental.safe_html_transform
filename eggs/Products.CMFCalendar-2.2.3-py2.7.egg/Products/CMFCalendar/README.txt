======================
 Products.CMFCalendar
======================

.. contents::

The CMFCalendar product is an example of creating a CMF
Product.  The CMFCalendar product is also expected to be a
generally useful *out of the box* and skinnable to accomodate
customization within your existing CMF instance.  To see how to
go about building a CMF product, this hopefully allows a
developer to follow through the process of registering their
product, skins, and help with the CMF by example.  It shows how
an object is created and registered with the types_tool,
necessary skins added to the skins_tool, with the Calendar
skins directory added to the skin paths, and providing
portal_metadatool with an Element policy for the content_type
of the object.

For installing set the *active site configuration* of your site's
setup tool to the CMFCalendar profile and import all steps.

After installing the CMFCalendar you should notice a calendar
appear in your CMF.  This is fully customisable to your portals
needs.
