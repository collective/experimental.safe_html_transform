Experimental Browser Views

  This sub-package provides Zope 3-style browser views for some CMF content
  interfaces. These views are not used by the default profile.

  The content of this sub-package is experimental and might be refactored
  without further notice. Documentation and unittests are still missing but
  the views should work just as well as the corresponding skin methods.

  See TODO.txt for a detailed list of converted skin methods.

  Using the Browser Views

    In an un-customized CMFDefault site you will notice no difference because
    the browser views are just different in implementation, not in look and
    feel. But the browser view machinery bypasses the CMF skin machinery, so
    you will notice that TTW customizations no longer have any effect.
