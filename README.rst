====================
experimental.safe_html_transform
====================

This is add-on to replace the old safe_html from Portal Transform such that we can remove the CMFDefault dependencies and also this helps in removing the old safe_html transform and installing new safe_html transform on just inatalling the add-on.

====================
How it works ?
====================

Basically to get this add-on we have to go to the site setup and select add-ons and then install our new add-on named "experimental.safe_html_transform". After that when we click on the HTML Filtering from site setup we will see our new control panel instead of old safe_html control panel.

====================
Why this add-on is required ?
====================

This add-on is required for two main reasons :-
1) It removes the CMFDefault dependencies from the Plone (From HTML Filtering)
2) It is quite faster transform then the earlier one as it uses lxml for filtering HTML

====================
What is does ?
====================

Works same as the old safe_html but more accurate and fast. Also when we install this add-on then the old safe_html transform is unregistered and our new transform is registered just on installing the add-on. Quite Cool, right ? :P
