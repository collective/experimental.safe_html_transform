Introduction
============

The archetypes.referencebrowserwidget is a Plone/Archetype-widget for relation-
fields. It adds a new reference widget that allows you to search or browse the
portal when creating references.  It can be used as a dropin-replacement for
the default ATReferenceBrowserWidget or as a standalone widget.

To install it as a replacement just install the product via the quickinstaller.
For using it as a standalone widget see the demotype in demo.py.
The widget tries to be ui-compatible with its predecessor
ATReferenceBrowserWidget. You can use the same properties as for the standard
ReferenceField and for the ATReferenceBrowserWidget.

When you use this widget, there are two buttons presented for each widget. One
that opens a popup-window that let's you do the search/browsing and one that
let's you clear the reference or selected references (will be in effect after
the form's Save).

The popop window basically consists of two parts. The top half is a search form
and the bottom half is the browser/search results part. Both parts can be
turned off or on using the widget's properties.

The search part has additional configuration in the widget
(see properties below).

The widget supports:

* catalog-only query of popup-contents. This is massive! permformance
  win compared with ATReferenceBrowserWidget. Try accessing a folder
  with 10k+ objects with both widgets.

* generic referencefield implementation via adapter. OOTB it supports
  Archetypes.ReferenceField and plonerelations.ATField.

* overwrite the popup-template via namedtemplate-implementation

* resizeable popup via simple properties

* a good unittest and integrationtest coverage

Properties
==========

The popup window can be configured using the following widget properties:


* default_search_index: when a user searches in the popup, this index is
  used by default. It points to "SearchableText" by default.

* show_indexes: in the popup, when set to True, a drop-down list is shown
  with the index to be used for searching. If set to False,
  default_search_index will be used.

* size: in case of single-select widget, the default is set to 30. In case
  of multi-select, default is 8.

* available_indexes: optional dictionary that lists all the indexes that
  can be used for searching. Format: {'<catalog index>':'<friendly name'>,
  ... } The friendly name is what the end-users sees to make the indexes more
  sensible for him. If you do not use this property then all the indexes will be
  shown (I think nobody should allow this to happen!).

* allow_search: shows the search section in the popup

* allow_sorting: allows you change the order of referenced objects
  (requires multiValued=1)

* allow_browse: shows the browse section in the popup

* search_catalog: Catalog to use. Defaults to: portal_catalog

* startup_directory: directory where the popup opens. Optional. When
  omitted, the current folder is used or in the case where a property
  refwidget_startupdirectories under site_properties is found it is
  searched for a startup_directory.

  Property is a lines field having the following
  format::

    path1:path2

  path1 is the path where all widgets being under it set startup_directory
  to path2 if no startup_directory is set.

* startup_directory_method: the name of a method or variable that, if
  available at the instance, will be used to obtain the path of the
  startup directory. If present, 'startup_directory' will be ignored.

* restrict_browsing_to_startup_directory: allows you to restrict the
  breadcrumbs ('allow_browse' property) to contents inside the
  'startup_directory' only. So you are not able to walk up in the hierarchy.
  (default: 0 = disabled)

* image_portal_types: specify a list of image portal_types. Instances of
  these portal types are being previewed within the popup widget

* image_method: specifies the name of a method that is added to the image
  URL to preview the image in a particular resolution (e.g. 'mini' for
  thumbnails)

* show_review_state: allows you to display the workflow state for objects
  (off by default)

* show_path: display the relative path (relative to the portal object) of
  referenced objects

* only_for_review_states: items are only referencable if their workflow
  state matches the ones
  a specified (default: None = no filtering by workflow state)

* history_length: enable a history feature that show the paths of the last
  N visited folders (default : 0 = no history)

* force_close_on_insert: closes the popup when the user choses insert. This
  overrides the behavior in multiselect mode.

* base_query: defines query terms that will apply to all searches, mainly
  useful to create specific restrictions when allow_browse=0.  Can be
  either a dictonary with query parameters, or the name of a method or
  callable available in cotext that will return such a dictionary.

* hide_inaccessible: don't show inaccessible objects (no permission) in view
  mode.

* show_results_without_query: Don't ignore empty queries, but display results.

* popup_width: Width of popup-window in pixel. Defaults to: 500

* popup_height: height of popup-window in pixel. Defaults to: 550

* popup_name: Name of template to be used for popup. To use another template
  you have to register a named adapter for this template. Like:

    <zope:adapter
      for="Products.Five.BrowserView"
      factory=".view.default_popup_template"
      name="popup"
      provides="zope.formlib.namedtemplate.INamedTemplate"
      />

  See default implementation and unittests for examples.

Design notes
============

This notes were taken from the original ATReferenceBrowserWidget. Since I
didn't changed the ui, they are still valid (I think!?).

Both the templates (widget and popup) are prototypes. There are still some
inline styles, especially in the popup because I didn't want to tweak with
plone's css stuff and I didn't want to do hacking and tricking to incorporate
a stylesheet myself.So, that's still a point of interest.

Furthermore I made some design decisions. Right now, in the popup window, all
objects are shown (when browsing) and objects that may be referenced to are
bold and the other objects are greyed out.  I chose to show the
non-referenceable objects too because they may be an important part of the
context that help the user search for the desired objects to browse to.
Another thing that I chose for is that in case of a multi-value widget, the
popup remains open so that you can continue to add references without having to
reopen the popup over and over again. Problem is that you have to close the
window yourself. This may change if it turns out to be an annoyance.

A thing that is more related to forms in general is that the items in the
multiselect listbox need to be selected before Save is clicked otherwise only
the selected items are submitted. That kinda sucks usability-wise because now
the user basically has to make two selections: first by choosing the items in
the popup and secondly by selecting them again in the listbox. Right now I made
it so that the items are selected by default but if the user starts clicking in
the list, then there might be an issue. Btw, the inandout widget has the same
problem.  Best would be to select all the items in a script just before the
form is submitted so that the complete list is submitted. But that requires
changes in the base_edit form I think. But it's something to think about since
there are now already two widgets that needs to be prepared like this (inandout
and this one, haven't looked at picklist though, could have the same problem).

Anyway, have fun with it and if you have suggestions please let me know. If you
see problems, please fix them when you can.
