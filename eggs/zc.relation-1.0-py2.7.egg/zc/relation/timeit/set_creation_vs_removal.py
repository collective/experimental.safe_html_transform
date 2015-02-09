"""
Example output:

----8<----8<----8<----

control: 0.0847041606903

(the following results have the control subtracted)

create_empty: 0.00116777420044
create_one: 0.00260376930237
create_ten: 0.00407481193542
create_hundred: 0.0167508125305
create_thousand: 0.149729013443
create_tenthousand: 1.55575275421

remove_one: 0.00317978858948
remove_ten: 0.0110769271851
remove_hundred: 0.0708107948303
remove_thousand: 0.52201294899
remove_tenthousand: 5.27875876427

len_one: 0.00183796882629
len_ten: 0.001877784729
len_hundred: 0.00301790237427
len_thousand: 0.00213479995728
len_tenthousand: 0.00438284873962

----8<----8<----8<----

remove one/create one is similar

ten starts giving obvious wins to creation.  removing 1 (10%) slightly cheaper

create 100/remove 10 gives slight win to remove (10%-ish)

create 1000/remove 100 gives significant win to removal.  Progression for both
patterns begins to be linear with larger numbers, which makes sense.  That
suggests 20% might be the approximate break even point.

create 10000/remove 1000 suggests a break even point of about 26%.

The cost of the len is not nothing, but begins to pay for itself with
larger numbers.

This will be our heuristic then, rather than trying to calculate a curve I
couldn't make anyway.

given len_removal, len_set, and ratio (len_set/len_removal)
if len_removal < 5 or ratio <= .1 or len_set > 500 and ration <= .2:
    remove rather than create

"""

import timeit

setup = '''
import BTrees
one = BTrees.family32.IO.TreeSet((0,))
ten = BTrees.family32.IO.TreeSet(range(10))
hundred = BTrees.family32.IO.TreeSet(range(100))
thousand = BTrees.family32.IO.TreeSet(range(1000))
tenthousand = BTrees.family32.IO.TreeSet(range(10000))
sets = [BTrees.family32.IO.TreeSet(tenthousand) for i in range(1000)]
'''

base = 's = sets.pop()'

create_template = base + '''
BTrees.family32.IO.TreeSet(%s)'''

remove_template = base + '''
for i in range(0, 10000, %d):
    s.remove(i)'''

len_template = base + '''
len(%s)'''

control = timeit.Timer(base, setup)

create_empty = timeit.Timer(create_template % ('',), setup)
create_one = timeit.Timer(create_template % ('one',), setup)
create_ten = timeit.Timer(create_template % ('ten',), setup)
create_hundred = timeit.Timer(create_template % ('hundred',), setup)
create_thousand = timeit.Timer(create_template % ('thousand',), setup)
create_tenthousand = timeit.Timer(create_template % ('tenthousand',), setup)

remove_one = timeit.Timer(remove_template % (10000,), setup)
remove_ten = timeit.Timer(remove_template % (1000,), setup)
remove_hundred = timeit.Timer(remove_template % (100,), setup)
remove_thousand = timeit.Timer(remove_template % (10,), setup)
remove_tenthousand = timeit.Timer(remove_template % (1,), setup)

len_one = timeit.Timer(len_template % ('one',), setup)
len_ten = timeit.Timer(len_template % ('ten',), setup)
len_hundred = timeit.Timer(len_template % ('hundred',), setup)
len_thousand = timeit.Timer(len_template % ('thousand',), setup)
len_tenthousand = timeit.Timer(len_template % ('tenthousand',), setup)

d = {}

control_result = d['control_result'] = min(control.repeat(3, 1000))
d['create_empty_result'] = min(create_empty.repeat(3, 1000))
d['create_one_result'] = min(create_one.repeat(3, 1000))
d['create_ten_result'] = min(create_ten.repeat(3, 1000))
d['create_hundred_result'] = min(create_hundred.repeat(3, 1000))
d['create_thousand_result'] = min(create_thousand.repeat(3, 1000))
d['create_tenthousand_result'] = min(create_tenthousand.repeat(3, 1000))
d['remove_one_result'] = min(remove_one.repeat(3, 1000))
d['remove_ten_result'] = min(remove_ten.repeat(3, 1000))
d['remove_hundred_result'] = min(remove_hundred.repeat(3, 1000))
d['remove_thousand_result'] = min(remove_thousand.repeat(3, 1000))
d['remove_tenthousand_result'] = min(remove_tenthousand.repeat(3, 1000))
d['len_one_result'] = min(len_one.repeat(3, 1000))
d['len_ten_result'] = min(len_ten.repeat(3, 1000))
d['len_hundred_result'] = min(len_hundred.repeat(3, 1000))
d['len_thousand_result'] = min(len_thousand.repeat(3, 1000))
d['len_tenthousand_result'] = min(len_tenthousand.repeat(3, 1000))

for k, v in d.items():
    if k == 'control_result':
        continue
    d[k[:-7]] = v - control_result

print '''
control: %(control_result)s

(the following results have the control subtracted)

create_empty: %(create_empty)s
create_one: %(create_one)s
create_ten: %(create_ten)s
create_hundred: %(create_hundred)s
create_thousand: %(create_thousand)s
create_tenthousand: %(create_tenthousand)s

remove_one: %(remove_one)s
remove_ten: %(remove_ten)s
remove_hundred: %(remove_hundred)s
remove_thousand: %(remove_thousand)s
remove_tenthousand: %(remove_tenthousand)s

len_one: %(len_one)s
len_ten: %(len_ten)s
len_hundred: %(len_hundred)s
len_thousand: %(len_thousand)s
len_tenthousand: %(len_tenthousand)s
''' % d
