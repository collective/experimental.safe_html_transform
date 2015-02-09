def update_only_validator(form, action):
    """Only validate an action when updating a form.

    This allows you to create an action without having formlib render a
    button for it.
    """ 
    return "form_result" not in form.__dict__


def null_validator(*args, **kwargs):
    """A validator that doesn't validate anything.
    
    This is somewhat lame, but if you have a "Cancel" type button that
    won't want to validate the form, you need something like this.

    @form.action(_(u"label_cancel", default=u"Cancel"),
                 validator=null_validator,
                 name=u'cancel')
    """
    return ()
