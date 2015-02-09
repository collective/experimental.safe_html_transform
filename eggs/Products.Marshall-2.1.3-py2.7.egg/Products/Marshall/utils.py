def fixtag(tag, namespaces):
    """ returns the tag name seperated from the namespace uri
    as givein in {some.namespace}tag in elementtree"""

    # given a decorated tag (of the form {uri}tag), return prefixed
    # tag and namespace declaration, if any

    namespace_uri, tag = tag[1:].split("}", 1)
    ns = namespaces.get(namespace_uri)
    return tag, ns
