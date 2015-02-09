## Script (Python) "switchLanguage"
##title=
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=set_language=None
REQUEST=context.REQUEST

here_url=context.absolute_url()

query = {}
if set_language:
    # no cookie support
    query['cl']=set_language

    query['set_language']=set_language

qst="?"
for k, v in query.items():
    qst=qst+"%s=%s&" % (k, v)
redirect=here_url+qst[:-1]

REQUEST.RESPONSE.redirect(redirect)

