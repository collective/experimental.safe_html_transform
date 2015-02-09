========
Batching
========

Batching is the mechanism with which you split up a large dataset over multiple
pages. The batching implementation discussed here has many features to help
with constructing templates.

A basic batch is created using a few paramenters.

  >>> from plone.batching.batch import Batch
  >>> batch = Batch.fromPagenumber(
  ... items=range(333), pagesize=10, pagenumber=1, navlistsize=5)


Items on page
-------------

The batch is iterable. It will only return the items for the current page.

 >>> list(batch)
 [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

If we change to a different page it will change the result set to that page.

  >>> batch.pagenumber = 3
  >>> list(batch)
  [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]

Batch size
----------

We can ask a batch for its size using two different methods. The first is to use the normal Python style.

  >>> len(batch)
  333

The other is more convenient for use with template.

  >>> batch.sequence_length
  333

It is also possible to ask for the items on the current page.

  >>> batch.items_on_page 
  10

We can get the number of pages in a batch. This is actually the same as requesting the number of the last page.

  >>> batch.lastpage
  34

If we switch to this page the `items_on_page` attribute should be different
(because our items are indivisible by ten).

  >>> batch.pagenumber = batch.lastpage
  >>> batch.items_on_page
  3

Navigation
----------

Because the batch implementation is geared towards templates it also provides a
few navigation related methods.

The first thing we can check is whether our batch spans over multiple pages.

  >>> batch = Batch.fromPagenumber(
  ...          items=range(333), pagesize=10, navlistsize=5)
  >>> batch.multiple_pages
  True

  >>> other_batch = Batch.fromPagenumber(
  ...          items=range(3))
  >>> other_batch.multiple_pages
  False

It will also do simple math for giving the next and previous page numbers.

  >>> batch.nextpage
  2

  >>> batch.pagenumber = 5
  >>> batch.previouspage
  4
  
We can also ask if there are any next or previous pages.

  >>> batch.has_next
  True

  >>> batch.pagenumber = batch.lastpage
  >>> batch.has_next
  False

  >>> batch.has_previous
  True

  >>> batch.pagenumber = 1
  >>> batch.has_previous
  False

You might want to display the next item count. This can be usefull in case the
batch is not exactly divisible by the pagesize.

  >>> batch.pagenumber = batch.lastpage - 1
  >>> batch.next_item_count
  3

The system maintains a navigation list as well. This is normally used to
display numbers at the bottom of the screen for quick access to those pages.

  >>> batch.pagenumber = 1
  >>> batch.navlist
  [1, 2, 3, 4, 5]

Keep in mind that the navlist centers around the current page when it can.

  >>> batch.pagenumber = 10
  >>> batch.navlist
  [8, 9, 10, 11, 12]
  
You can specify the navlist size to be any size you want.

  >>> other_batch = Batch.fromPagenumber(items=range(333), pagesize=10, pagenumber=10,
  ...                     navlistsize=12)
  >>> other_batch.navlist
  [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

We have already seen the `lastpage` property. There is also the equivalent
`firstpage` property.

  >>> batch.firstpage
  1

Normally you would want to provide your users with a quick way to jump the the
first or last page from anywhere in the batch. To make sure you will not show
the links twice (once in the navlist and once for quick access) you can use the
special helpers.

  >>> batch.pagenumber = 1
  >>> batch.show_link_to_first
  False

  >>> batch.pagenumber = 15
  >>> batch.show_link_to_first
  True

  >>> batch.pagenumber = 1
  >>> batch.show_link_to_last
  True

  >>> batch.pagenumber = batch.lastpage
  >>> batch.show_link_to_last
  False

For extra visual smoothness you might also want to display an elipses next to
your quicklink to the first page. 

  >>> batch.pagenumber = 15
  >>> batch.second_page_not_in_navlist
  True

This should only be done in case the second page is not in the navigation list.

  >>> batch.pagenumber = 4
  >>> batch.navlist
  [2, 3, 4, 5, 6]
  >>> batch.second_page_not_in_navlist
  False

The same goes for the showing an elipses before the last link.

  >>> batch.pagenumber = 15
  >>> batch.before_last_page_not_in_navlist
  True

  >>> batch.pagenumber = batch.lastpage - 2
  >>> batch.before_last_page_not_in_navlist
  False

To make displaying the links to next and previous pages even easier you can
also get two seperate navlist for both of them.

  >>> batch.pagenumber = 1
  >>> batch.next_pages
  [2, 3, 4, 5]

  >>> batch.pagenumber = batch.lastpage - 2
  >>> batch.next_pages
  [33, 34]


  >>> batch.pagenumber = batch.lastpage
  >>> batch.previous_pages
  [32, 33]

  >>> batch.pagenumber = batch.firstpage + 1
  >>> batch.previous_pages
  [1]
