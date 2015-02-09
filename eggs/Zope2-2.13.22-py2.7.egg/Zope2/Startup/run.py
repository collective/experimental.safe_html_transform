##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

def run():
    """ Start a Zope instance """
    import Zope2.Startup
    starter = Zope2.Startup.get_starter()
    opts = _setconfig()
    starter.setConfiguration(opts.configroot)
    try:
        starter.prepare()
    except:
        starter.shutdown()
        raise
    starter.run()

def configure(configfile):
    """ Provide an API which allows scripts like zopectl to configure
    Zope before attempting to do 'app = Zope2.app(). Should be used as
    follows:  from Zope2.Startup.run import configure;
    configure('/path/to/configfile'); import Zope2; app = Zope2.app() """
    import Zope2.Startup
    starter = Zope2.Startup.get_starter()
    opts = _setconfig(configfile)
    starter.setConfiguration(opts.configroot)
    starter.setupSecurityOptions()
    starter.dropPrivileges()
    return starter

def _setconfig(configfile=None):
    """ Configure a Zope instance based on ZopeOptions.  Optionally
    accept a configfile argument (string path) in order to specify
    where the configuration file exists. """
    from Zope2.Startup import options, handlers
    from App import config
    opts = options.ZopeOptions()
    if configfile:
        opts.configfile = configfile
        opts.realize(raise_getopt_errs=0)
    else:
        opts.realize()

    handlers.handleConfig(opts.configroot, opts.confighandlers)
    import App.config
    App.config.setConfiguration(opts.configroot)
    return opts

def make_wsgi_app(global_config, zope_conf):
    from App.config import setConfiguration
    from Zope2.Startup import get_starter
    from Zope2.Startup.handlers import handleConfig
    from Zope2.Startup.options import ZopeOptions
    from ZPublisher.WSGIPublisher import publish_module
    starter = get_starter()
    opts = ZopeOptions()
    opts.configfile = zope_conf
    opts.realize(args=(), progname='Zope2WSGI', raise_getopt_errs=False)
    handleConfig(opts.configroot, opts.confighandlers)
    setConfiguration(opts.configroot)
    starter.setConfiguration(opts.configroot)
    starter.prepare()
    return publish_module

if __name__ == '__main__':
    run()

