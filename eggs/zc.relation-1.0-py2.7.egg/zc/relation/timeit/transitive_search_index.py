"""
The goal of this file is to determine how well the transposing transitive
index helps searches.

The result of the first test has three big sections, one for
`findRelationTokens`, one for `findValueTokens`, and one for `canFind`. 
Within each section, we have six searches, each broader than the last. 
A 'brute' result is a result without a search index.  A 'relation'
result uses a search index without a configured value index.  A 'value'
result uses a search index with a configured value index.  'relation'
and 'value' results should really only differ materially for
`findValueTokens`.  A 'brute_generate' result shows how fast it takes to
get the generator back from a brute search, without actually iterating
over it, and is not pertinent for `canFind`.

The result of the second test shows how expensive it is to install a search
index that is not used.

Example result:

                               Test 1


[('control_result', 0.0091979503631591797),
 "**** res = list(catalog.findRelationTokens({'token': 9})) ****",
 '**** [109] ****',
 ('brute_generate', 0.230133056640625),
 ('brute', 0.79251599311828613),
 ('relation', 0.52498507499694824),
 ('value', 0.52437424659729004),
 "**** res = list(catalog.findRelationTokens({'token': 7})) ****",
 '**** [107] ****',
 ('brute_generate', 0.2291419506072998),
 ('brute', 0.80537819862365723),
 ('relation', 0.52660107612609863),
 ('value', 0.53035998344421387),
 "**** res = list(catalog.findRelationTokens({'token': 5})) ****",
 '**** [105, 107, 108, 109] ****',
 ('brute_generate', 0.23081111907958984),
 ('brute', 1.9628522396087646),
 ('relation', 0.53455114364624023),
 ('value', 0.53245711326599121),
 "**** res = list(catalog.findRelationTokens({'token': 3})) ****",
 '**** [103, 105, 106, 107, 108, 109] ****',
 ('brute_generate', 0.23008418083190918),
 ('brute', 2.7950401306152344),
 ('relation', 0.53938508033752441),
 ('value', 0.53650403022766113),
 "**** res = list(catalog.findRelationTokens({'token': 1})) ****",
 '**** [101, 103, 104, 105, 106, 107, 108, 109] ****',
 ('brute_generate', 0.23291897773742676),
 ('brute', 3.614861011505127),
 ('relation', 0.53824424743652344),
 ('value', 0.53764486312866211),
 "**** res = list(catalog.findRelationTokens({'token': 0})) ****",
 '**** [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111] ****',
 ('brute_generate', 0.23366808891296387),
 ('brute', 5.3421971797943115),
 ('relation', 0.54594111442565918),
 ('value', 0.54389309883117676),
 '------------------',
 '------------------',
 "**** res = list(catalog.findValueTokens('children', {'token': 9})) ****",
 '**** [23, 24] ****',
 ('brute_generate', 0.2296299934387207),
 ('brute', 0.84845805168151855),
 ('relation', 0.68227314949035645),
 ('value', 0.54161596298217773),
 "**** res = list(catalog.findValueTokens('children', {'token': 7})) ****",
 '**** [17, 18, 19] ****',
 ('brute_generate', 0.22747707366943359),
 ('brute', 0.87759518623352051),
 ('relation', 0.69233298301696777),
 ('value', 0.53438305854797363),
 "**** res = list(catalog.findValueTokens('children', {'token': 5})) ****",
 '**** [7, 8, 9, 17, 18, 19, 20, 21, 22, 23, 24] ****',
 ('brute_generate', 0.22690701484680176),
 ('brute', 2.1761610507965088),
 ('relation', 0.80766010284423828),
 ('value', 0.54901003837585449),
 "**** res = list(catalog.findValueTokens('children', {'token': 3})) ****",
 '**** [5, 6, 7, 8, 9, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24] ****',
 ('brute_generate', 0.22738194465637207),
 ('brute', 3.0915610790252686),
 ('relation', 0.86617612838745117),
 ('value', 0.55521416664123535),
 "**** res = list(catalog.findValueTokens('children', {'token': 1})) ****",
 '**** [3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24] ****',
 ('brute_generate', 0.22893619537353516),
 ('brute', 4.0192921161651611),
 ('relation', 0.94522690773010254),
 ('value', 0.55083107948303223),
 "**** res = list(catalog.findValueTokens('children', {'token': 0})) ****",
 '**** [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32] ****',
 ('brute_generate', 0.22567915916442871),
 ('brute', 5.9501399993896484),
 ('relation', 1.1025910377502441),
 ('value', 0.56526517868041992),
 '------------------',
 '------------------',
 "**** res = catalog.canFind({'token': 9}, targetQuery={'children': 23}) ****",
 '**** True ****',
 ('brute', 0.77447414398193359),
 ('relation', 0.66926908493041992),
 ('value', 0.66884613037109375),
 "**** res = catalog.canFind({'token': 7}, targetQuery={'children': 23}) ****",
 '**** False ****',
 ('brute', 0.93198609352111816),
 ('relation', 0.6589500904083252),
 ('value', 0.6538691520690918),
 "**** res = catalog.canFind({'token': 5}, targetQuery={'children': 23}) ****",
 '**** True ****',
 ('brute', 1.9603328704833984),
 ('relation', 0.67744708061218262),
 ('value', 0.67296600341796875),
 "**** res = catalog.canFind({'token': 3}, targetQuery={'children': 23}) ****",
 '**** True ****',
 ('brute', 2.7534151077270508),
 ('relation', 0.67701125144958496),
 ('value', 0.67615604400634766),
 "**** res = catalog.canFind({'token': 1}, targetQuery={'children': 23}) ****",
 '**** True ****',
 ('brute', 3.5522449016571045),
 ('relation', 0.67667698860168457),
 ('value', 0.67722702026367188),
 "**** res = catalog.canFind({'token': 0}, targetQuery={'children': 23}) ****",
 '**** True ****',
 ('brute', 5.198289155960083),
 ('relation', 0.67714405059814453),
 ('value', 0.67705321311950684),
 '------------------',
 '------------------']


                               Test 2


[('control_result', 0.0068368911743164062),
 "**** res = catalog.findRelationTokens({'token': 9}) ****",
 ('brute', 0.23646903038024902),
 ('index', 0.29944419860839844),
 "**** res = catalog.findRelationTokens({'token': 0}) ****",
 ('brute', 0.23561906814575195),
 ('index', 0.30117917060852051),
 '------------------',
 '------------------',
 "**** res = catalog.findValueTokens('children', {'token': 9}) ****",
 ('brute', 0.2293241024017334),
 ('index', 0.30806207656860352),
 "**** res = catalog.findValueTokens('children', {'token': 0}) ****",
 ('brute', 0.23177909851074219),
 ('index', 0.30793118476867676),
 '------------------',
 '------------------']

Notes:

- While simply creating a generator is unsurprisingly the least work, if you
  want all the results then the index is always a win (on read!), even in the
  smallest search.  Even in this small graph it can give us factor-of-10
  results at the broadest search.

- The relation index, without the additional value index, still does a pretty
  good job on value searches, as hoped.

- In the second test we are only creating the generator each time.  We see
  what the cost is to install a search index.  This is small--as we see
  in the first test, getting the results takes much more time--and is
  hopefully a largely non-increasing cost once you add your first search
  index.

It might be nice to be able to demand a generator even when you have a search
index, in case you only want a result or two for a given call.  Probably
should be YAGNI for now.

It would be nice to add some further tests later to see how much worse
the write performance is when you have these indexes.

(I want to write look at the intransitive search too: is it really only
useful when you have a query factory that mutates the initial search, as
in tokens.txt?)

"""

import timeit
import pprint

# see zc/relation/searchindex.txt

brute_setup = '''
import BTrees
relations = BTrees.family64.IO.BTree()
relations[99] = None # just to give us a start

class Relation(object):
    def __init__(self, token, children=()):
        self.token = token
        self.children = BTrees.family64.IF.TreeSet(children)
        self.id = relations.maxKey() + 1
        relations[self.id] = self


def token(rel, self):
    return rel.token

def children(rel, self):
    return rel.children

def dumpRelation(obj, index, cache):
    return obj.id

def loadRelation(token, index, cache):
    return relations[token]

import zc.relation.queryfactory
factory = zc.relation.queryfactory.TransposingTransitive(
    'token', 'children')
import zc.relation.catalog
catalog = zc.relation.catalog.Catalog(
    dumpRelation, loadRelation, BTrees.family64.IO, BTrees.family64)
catalog.addValueIndex(token)
catalog.addValueIndex(children, multiple=True)
catalog.addDefaultQueryFactory(factory)

for token, children in (
    (0, (1, 2)), (1, (3, 4)), (2, (10, 11, 12)), (3, (5, 6)),
    (4, (13, 14)), (5, (7, 8, 9)), (6, (15, 16)), (7, (17, 18, 19)),
    (8, (20, 21, 22)), (9, (23, 24)), (10, (25, 26)),
    (11, (27, 28, 29, 30, 31, 32))):
    catalog.index(Relation(token, children))

'''

#                                  _____________0_____________
#                                 /                           \
#                        ________1_______                ______2____________
#                       /                \              /          |        \
#                ______3_____            _4_          10       ____11_____   12
#               /            \          /   \         / \     / /  |  \ \ \
#       _______5_______       6       13     14     25  26  27 28 29 30 31 32
#      /       |       \     / \
#    _7_      _8_       9   15 16
#   / | \    / | \     / \
# 17 18 19  20 21 22  23 24

relation_index_setup = brute_setup + '''
import zc.relation.searchindex
catalog.addSearchIndex(
    zc.relation.searchindex.TransposingTransitive('token', 'children'))
'''

value_index_setup = brute_setup + '''
import zc.relation.searchindex
catalog.addSearchIndex(
    zc.relation.searchindex.TransposingTransitive(
        'token', 'children', names=('children',)))
'''

relations_run_template = '''
res = list(catalog.findRelationTokens({'token': %d}))
'''

value_run_template = '''
res = list(catalog.findValueTokens('children', {'token': %d}))
'''

canfind_run_template = '''
res = catalog.canFind({'token': %d}, targetQuery={'children': 23})
'''

options = (9,7,5,3,1,0)

runs = 10000

control = timeit.Timer('res = catalog.__len__()\nlist()', brute_setup)
control_result = min(control.repeat(3, runs))
d = [('control_result', control_result)]

for template in (relations_run_template, value_run_template,
                 canfind_run_template):
    for o in options:
        run = template % (o,)
        # verify we get the same results
        brute_globs = {}
        relation_globs = {}
        value_globs = {}
        exec brute_setup + run in brute_globs
        exec relation_index_setup + run in relation_globs
        exec value_index_setup + run in value_globs
        brute = brute_globs['res']
        relation = relation_globs['res']
        value = value_globs['res']
        canfind = template == canfind_run_template
        if not canfind:
            brute.sort()
        assert brute == relation == value, '%s: %r, %r, %r' % (
            run, brute, relation, value)
        # end verify
        d.append('**** %s ****' % (run.strip(),))
        d.append('**** %s ****' % (brute,))
        if not canfind:
            # show how long it takes to make the generator
            altered = run.replace('list(', '', 1)
            altered = altered.replace(')', '', 1)
            d.append((
                'brute_generate',
                min(timeit.Timer(
                    altered, brute_setup).repeat(3, runs)) - control_result))
        d.append((
            'brute',
            min(timeit.Timer(
                run, brute_setup).repeat(3, runs)) - control_result))
        d.append((
            'relation',
            min(timeit.Timer(
                run, relation_index_setup).repeat(3, runs)) - control_result))
        d.append((
            'value',
            min(timeit.Timer(
                run, value_index_setup).repeat(3, runs)) - control_result))
        
    d.append('------------------')
    d.append('------------------')


print '                               Test 1\n\n'
pprint.pprint(d)

reverse_setup = brute_setup + """
import zc.relation.searchindex
catalog.addSearchIndex(
    zc.relation.searchindex.TransposingTransitive('children', 'token'))
"""

relations_run_template = '''
res = catalog.findRelationTokens({'token': %d})
'''

value_run_template = '''
res = catalog.findValueTokens('children', {'token': %d})
'''

print '\n\n                               Test 2\n\n'

control = timeit.Timer('res = catalog.__len__()', brute_setup)
control_result = min(control.repeat(3, runs))
d = [('control_result', control_result)]

for template in (relations_run_template, value_run_template):
    for o in (9,0):
        run = template % (o,)
        d.append('**** %s ****' % (run.strip(),))
        d.append((
            'brute',
            min(timeit.Timer(
                run, brute_setup).repeat(3, runs)) - control_result))
        d.append((
            'index',
            min(timeit.Timer(
                run, reverse_setup).repeat(3, runs)) - control_result))
        
    d.append('------------------')
    d.append('------------------')

pprint.pprint(d)
        
