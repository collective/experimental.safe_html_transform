#!/usr/bin/env python
# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
ATXML data uploader
Give it a list of ATXML files, and it will do a PUT
to the server of those files, plus any "content" with the
same base name but different extension. If no list is specified,
will use all in the current directory.

Doesn't currently iterate over directories.

If you want to use this for content without ATXML files,
set the ATXML extension as the content

$Id: __init__.py 2886 2004-08-25 03:51:04Z dreamcatcher $
"""

import os, sys, time
import httplib, urllib
import string
from optparse import OptionParser
from base64 import encodestring
from WebDAV import davlib     # not the standard davlib
from xml.dom import minidom

class FakeResponse: pass

def upload(content, conn, path):
    if content:
        return conn.put(path, content, content_type='text/html')
    else:
        x = FakeResponse()
        x.status = 0
        return x

def getText(nodelist):
    """DOM helper, for extracting text"""
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

start = time.time()

usage = "usage: %prog [options] server[:port] /path/to/col/ [atxml files...]"
parser = OptionParser(usage=usage)
parser.add_option("-u", "--username", dest="username",
                 help="WebDAV user name", metavar="USER",
                 default="admin")
parser.add_option("-p", "--password", dest="password",
                 help="WebDAV password", metavar="PASS",
                 default="admin")
parser.add_option("-a", "--atxml", dest="atxmlend",
                 help="File extension of ATXML", metavar=".atxml",
                 default=".atxml")
parser.add_option("-c", "--content", dest="contentend",
                 help="File extension of content", metavar=".xml",
                 default=".xml")
parser.add_option("-s", "--server", dest="serverend",
                 help="File extension on server", metavar=".html",
                 default=".html")
(options, args) = parser.parse_args()

if len(args) < 2:
    print "Error: Server and path are required. Use -h for help."
    print
    sys.exit(-1)

if len(args) > 2:
    print "Using ATXML files supplied on commandline:"
    files = args[2:]
else:
    print "Using all ATXML files in directory:"
    files = [x for x in os.listdir(".") if x.endswith(options.atxmlend)]

server = args[0]
pathstarts = args[1].rstrip('/')+'/'
conn = davlib.DAV(server, timeout=300)
conn.setauth(options.username, options.password)

bad = []
count = 0
for file in files:
    try:
        metafile = open(file)
        metacontent = metafile.read()

        name = metafile.name
        print name,
        if not name.endswith(options.atxmlend):
            print "Not properly named. Expected to end with '%s'" % options.atxmlend
            continue
        if len(options.atxmlend) > 0:
            id = fid = name[:-len(options.atxmlend)]
        else:
            id = fid = name

        metafile.close()

        try:
            f = open(fid+options.contentend)
            content = f.read()
            f.close()
        except IOError:
            content = ""

        # find our true id, regardless of file name, if specified in the file
        try:
            dom = minidom.parseString(metacontent)
            field = [x for x in dom.getElementsByTagName('field') \
                     if x.getAttribute("id")=="id"][0]
            id = getText(field.childNodes) or fid
            dom.unlink()
        except:
            pass

        path = "%s%s%s" % (pathstarts,id,options.serverend)
        print "-> %s" % path,

        errormeta = None
        response = upload(metacontent, conn, path)
        if not response.status in(201, 204):
            errormeta = "%s %s" % (response.status,response.reason)
        #print response.status,

        errorcontent = None
        response = upload(content, conn, path)
        if not response.status in (204, 0):
            errorcontent = "%s %s" % (response.status,response.reason)
        #print response.status,

        if errormeta or errorcontent:
            print "FAIL"
            print "   Metadata: %s" % errormeta
            print "   Content:  %s" % errorcontent
            bad += [name]
        else:
            print "ok"
            count += 1
    except "ExpatError":
        print "FAIL: malformed ATXML file"
        bad += [name]
    except Exception, e:
        print "FAIL"
        print "  %s" % e
        bad += [name]

conn.close()

end = time.time()

print "Successfully imported: %s pieces out of %s" % (`count`,`len(files)`)
print "Time elapsed: %s" % `end-start`
print
print "There were %s failures: " % `len(bad)`,
for num in bad:
    print num,
