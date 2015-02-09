# $Id: patch_inspect.py,v 1.2 2006/02/19 22:18:47 stefan Exp $
'''Monkey patches for 'inspect' to let it recognize Zopes data types.'''

# prevent refreshing as it would introduce loops
__refresh_module__= 0


import inspect

# patch 'ismethod'
_ismethod= inspect.ismethod

def implementsMethod(object):
  return _ismethod(object) or \
         (hasattr(object,'__doc__') \
          and hasattr(object,'__name__') \
          and hasattr(object,'im_class') \
          and hasattr(object,'im_func') \
          and hasattr(object,'im_self') \
          and inspect.isfunction(object.im_func) \
          )

inspect.ismethod= implementsMethod

# Python 2.1 backward compatibility
if not hasattr(inspect,'getmro'):
  def getmro(class_):
    '''the method resolution order for *class_* (as a tuple).'''
    r= []; queue= [class_]; cls= {}; seen= cls.has_key
    while queue:
      cl= queue.pop(0)
      if seen(cl): continue
      cls[cl]= None
      r.append(cl)
      queue[0:0]= list(cl.__bases__)
    return tuple(r)

  inspect.getmro= getmro
