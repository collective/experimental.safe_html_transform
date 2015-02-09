##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
""" ActionIcons tool:  standard CMF mappings.

This module makes available a "starter set" of action -> icon mappings.
It will be installed by default when the tool is set up, unless an alternate
set is provided.

$Id: standard_mappings.py 110650 2010-04-08 15:30:52Z tseaver $
"""

OBJECT_ACTIONS = \
( { 'category'              : 'object'
  , 'action_id'             : 'view'
  , 'title'                 : 'View'
  , 'priority'              : 0
  , 'icon_expr'             : 'view_icon.png'
  }
, { 'category'              : 'object'
  , 'action_id'             : 'preview'
  , 'title'                 : 'Preview'
  , 'priority'              : 1
  , 'icon_expr'             : 'preview_icon.png'
  }
, { 'category'              : 'object'
  , 'action_id'             : 'edit'
  , 'title'                 : 'Edit'
  , 'priority'              : 2
  , 'icon_expr'             : 'edit_icon.png'
  }
, { 'category'              : 'object'
  , 'action_id'             : 'metadata'
  , 'title'                 : 'Metadata'
  , 'priority'              : 3
  , 'icon_expr'             : 'metadata_icon.png'
  }
)

FOLDER_ACTIONS = \
( { 'category'              : 'folder'
  , 'action_id'             : 'folderContents'
  , 'title'                 : 'Folder Contents'
  , 'priority'              : 0
  , 'icon_expr'             : 'folder_icon.png'
  }
, { 'category'              : 'folder'
  , 'action_id'             : 'localroles'
  , 'title'                 : 'Local Roles'
  , 'priority'              : 1
  , 'icon_expr'             : 'user_icon.png'
  }
, { 'category'              : 'folder'
  , 'action_id'             : 'syndication'
  , 'title'                 : 'Syndication'
  , 'priority'              : 2
  , 'icon_expr'             : 'syndication_icon.png'
  }
)

WORKFLOW_ACTIONS = \
( { 'category'              : 'workflow'
  , 'action_id'             : 'submit'
  , 'title'                 : 'Submit'
  , 'priority'              : 0
  , 'icon_expr'             : 'submit_icon.png'
  }
, { 'category'              : 'workflow'
  , 'action_id'             : 'history'
  , 'title'                 : 'History'
  , 'priority'              : 1
  , 'icon_expr'             : 'history_icon.png'
  }
, { 'category'              : 'workflow'
  , 'action_id'             : 'retract'
  , 'title'                 : 'Retract'
  , 'priority'              : 2
  , 'icon_expr'             : 'retract_icon.png'
  }
, { 'category'              : 'workflow'
  , 'action_id'             : 'publish'
  , 'title'                 : 'Publish'
  , 'priority'              : 3
  , 'icon_expr'             : 'approve_icon.png'
  }
, { 'category'              : 'workflow'
  , 'action_id'             : 'reject'
  , 'title'                 : 'Reject'
  , 'priority'              : 4
  , 'icon_expr'             : 'reject_icon.png'
  }
, { 'category'              : 'workflow'
  , 'action_id'             : 'expire'
  , 'title'                 : 'Expire'
  , 'priority'              : 5
  , 'icon_expr'             : 'expire_icon.png'
  }
, { 'category'              : 'workflow'
  , 'action_id'             : 'yank'
  , 'title'                 : 'Yank'
  , 'priority'              : 6
  , 'icon_expr'             : 'yank_icon.png'
  }
)

GLOBAL_ACTIONS = \
( { 'category'              : 'global'
  , 'action_id'             : 'undo'
  , 'title'                 : 'Undo'
  , 'priority'              : 0
  , 'icon_expr'             : 'undo_icon.png'
  }
, { 'category'              : 'global'
  , 'action_id'             : 'configPortal'
  , 'title'                 : 'Policies'
  , 'priority'              : 1
  , 'icon_expr'             : 'policies_icon.png'
  }
, { 'category'              : 'global'
  , 'action_id'             : 'worklist'
  , 'title'                 : 'Worklist'
  , 'priority'              : 2
  , 'icon_expr'             : 'worklist_icon.png'
  }
)

DEFAULT_MAPPINGS = ( OBJECT_ACTIONS
                   + FOLDER_ACTIONS
                   + WORKFLOW_ACTIONS
                   + GLOBAL_ACTIONS
                   )

def installActionIconMappings( tool, mappings=DEFAULT_MAPPINGS, clear_first=1 ):

    """ Add the specified mappings to the tool.

    o If 'clear_first', then zap existing mappings first.
    """
    if clear_first:
        tool.clearActionIcons()

    for mapping in mappings:
        tool.addActionIcon( category=mapping[ 'category' ]
                          , action_id=mapping[ 'action_id' ]
                          , icon_expr=mapping[ 'icon_expr' ]
                          , title=mapping[ 'title' ]
                          , priority=mapping[ 'priority' ]
                          )
