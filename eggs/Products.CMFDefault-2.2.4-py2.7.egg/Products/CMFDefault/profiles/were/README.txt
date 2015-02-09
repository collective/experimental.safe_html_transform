'were' profile
==============

This profile supplies an alternate main template to the one provided
in the 'zpt_generic' skins directory, offering the following optimization
opportunity:

- it uses the 'ursine_globals' view to look up its globals, rather than
  the usual Python script implementation: that view can be (and *is*) tested,
  tweaked, and profiled as normal Python code
  
This skin should provide about a ten percent speed boost (e.g., 30ms vs.
33-34ms for the empty site root;  YMMV, of course).
