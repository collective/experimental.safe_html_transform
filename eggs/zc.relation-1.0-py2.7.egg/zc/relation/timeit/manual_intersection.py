"""
This one is not very surprising, in retrospect.

Example result:

[('control_result', 0.000244140625),
 ('manual one ten', 0.028602838516235352),
 ('intersect one ten', 0.031899929046630859),
 ('intersect ten one', 0.031992912292480469),
 ('manual one hundred', 0.028395891189575195),
 ('intersect one hundred', 0.031839847564697266),
 ('intersect hundred one', 0.031901836395263672),
 ('manual ten hundred', 0.061377763748168945),
 ('intersect ten hundred', 0.038860797882080078),
 ('intersect hundred ten', 0.038875818252563477),
 ('manual one thousand', 0.028687715530395508),
 ('intersect one thousand', 0.03191065788269043),
 ('intersect thousand one', 0.03180384635925293),
 ('manual ten thousand', 0.061729907989501953),
 ('intersect ten thousand', 0.039285898208618164),
 ('intersect thousand ten', 0.039031744003295898),
 ('manual hundred thousand', 0.39881396293640137),
 ('intersect hundred thousand', 0.12407588958740234),
 ('intersect thousand hundred', 0.12287592887878418),
 ('manual one tenthousand', 0.028566837310791016),
 ('intersect one tenthousand', 0.031667947769165039),
 ('intersect tenthousand one', 0.031734943389892578),
 ('manual ten tenthousand', 0.062446832656860352),
 ('intersect ten tenthousand', 0.039116859436035156),
 ('intersect tenthousand ten', 0.039546728134155273),
 ('manual hundred tenthousand', 0.40611386299133301),
 ('intersect hundred tenthousand', 0.1228797435760498),
 ('intersect tenthousand hundred', 0.12310886383056641),
 ('manual thousand tenthousand', 3.989987850189209),
 ('intersect thousand tenthousand', 0.91191983222961426),
 ('intersect tenthousand thousand', 0.91330981254577637)]

Conclusion: just use intersection.  manual intersection with one on left is
always slightly better than C intersection, but not worth it in terms of
complexity.

While order is irrelevant for an individual intersection, it is very relevant
for a manual intersection: unsurprisingly, you want to sort smaller sets first,
because as long as one of your two sets is small, you go pretty fast.
Therefore, given a multi-intersection of [small, medium, large] it makes the
most sense to order them that way:

intersect(intersect(small, medium), large)
"""

import timeit
import pprint

setup = '''
import BTrees
one = BTrees.family32.IO.TreeSet((0,))
ten = BTrees.family32.IO.TreeSet(range(10))
hundred = BTrees.family32.IO.TreeSet(range(100))
thousand = BTrees.family32.IO.TreeSet(range(1000))
tenthousand = BTrees.family32.IO.TreeSet(range(10000))
'''

manual_template = 'BTrees.family32.IO.TreeSet(i for i in %s if i in %s)'

intersect_template = 'BTrees.family32.IO.intersection(%s, %s)'

options = ('one', 'ten', 'hundred', 'thousand', 'tenthousand')

runs = 10000

control = timeit.Timer('pass', setup)
control_result = min(control.repeat(3, runs))
d = [('control_result', control_result)]

for i, big in enumerate(options):
    for little in options[:i]:
        d.append((
            'manual %s %s' % (little, big),
            min(timeit.Timer(
                manual_template % (little, big),
                setup).repeat(3, runs)) - control_result))
        d.append((
            'intersect %s %s' % (little, big),
            min(timeit.Timer(
                intersect_template % (little, big),
                setup).repeat(3, runs)) - control_result))
        d.append((
            'intersect %s %s' % (big, little),
            min(timeit.Timer(
                intersect_template % (big, little),
                setup).repeat(3, runs)) - control_result))

pprint.pprint(d)
