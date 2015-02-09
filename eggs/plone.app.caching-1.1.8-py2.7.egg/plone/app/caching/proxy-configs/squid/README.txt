
This is an example buildout demonstrating a Squid-behind-Apache proxy configuration optimized for a Plone site using plone.app.caching.

This example also demonstrates one way to configure split-view caching (see the plone.app.caching readme) although it's also perfectly useable for the non-split-view caching case.  Split-view caching is enabled by setting a "Vary: X-Anonymous" header and "s-maxage" value on the split-views to be cached, via the plone.app.caching control panel.

To install, you first need to have buildout installed.  See http://www.buildout.org/install.html

Copy the entire contents of this directory to a new project directory and run buildout in that directory (for this example, let's assume a system-wide buildout is already installed).

% cp -R * /path/to/project/
% cd /path/to/project
% buildout

This will initialize the project directory and run all the 'parts' as defined in buildout.cfg.

- An Apache vhost configuration will be generated at "./etc/httpd-vhost.conf"

- A Squid configuration file will be generated at "./etc/squid.conf"

- A wrapper script to start up Squid will be generated at "./bin/squid"

For more detail, see the comments in the configuration files.  In particular, you may wish to study the Apache vhost configuration as much of the "magic" is encapsulated therein.