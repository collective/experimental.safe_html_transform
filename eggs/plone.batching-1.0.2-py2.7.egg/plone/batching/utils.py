def opt(start, end, size, orphan, sequence_length):
    """ Calculate start, end, batchsize
    """
    # This is copied from ZTUtils.Batch.py because orphans were not correct
    # there. 04/16/04 modified by Danny Bloemendaal (_ender_). Removed
    # try/except structs because in some situations they cause some unexpected
    # problems. Also fixed some problems with the orphan stuff.
    # Seems to work now.
    length = sequence_length
    if size < 1:
        if start > 0 < end >= start:
            size = end + 1 - start
        else:
            size = 25
    start = min(start, length)
    if end > 0:
        end = max(end, start)
    else:
        end = start + size - 1
        if (end + orphan) >= length:
            end = length
    return start, end, size


def calculate_pagenumber(elementnumber, batchsize, overlap=0):
    """ Calculate the pagenumber for the navigation """
    # To find first element in a page,
    # elementnumber = pagenumber * (size - overlap) - size (- orphan?)
    realsize = batchsize - overlap
    if realsize != 0:
        pagenumber, remainder = divmod(elementnumber, realsize)
    else:
        pagenumber, remainder = divmod(elementnumber, 1)
    if remainder > overlap:
        pagenumber += 1
    pagenumber = max(pagenumber, 1)
    return pagenumber


def calculate_pagerange(pagenumber, numpages, pagerange):
    """ Calculate the pagerange for the navigation quicklinks """
    # Pagerange is the number of pages linked to in the navigation, odd number
    pagerange = max(0, pagerange + pagerange % 2 - 1)
    # Making sure the list will not start with negative values
    pagerangestart = max(1, pagenumber - (pagerange - 1) / 2)
    # Making sure the list does not expand beyond the last page
    pagerangeend = min(pagenumber + (pagerange - 1) / 2, numpages) + 1
    return pagerange, pagerangestart, pagerangeend


def calculate_quantum_leap_gap(numpages, pagerange):
    """ Find the QuantumLeap gap. Current width of list is 6 clicks (30/5) """
    return int(max(1, round(float(numpages - pagerange) / 30)) * 5)


def calculate_leapback(pagenumber, numpages, pagerange):
    """ Check the distance between start and 0 and add links as necessary """
    leapback = []
    quantum_leap_gap = calculate_quantum_leap_gap(numpages, pagerange)
    num_back_leaps = max(0, min(3, int(round(
        float(pagenumber - pagerange) / quantum_leap_gap) - 0.3)))
    if num_back_leaps:
        pagerange, pagerangestart, pagerangeend = calculate_pagerange(
            pagenumber, numpages, pagerange)
        leapback = range(pagerangestart - num_back_leaps * quantum_leap_gap,
            pagerangestart, quantum_leap_gap)
    return leapback


def calculate_leapforward(pagenumber, numpages, pagerange):
    """ Check the distance between end and length and add links as necessary
    """
    leapforward = []
    quantum_leap_gap = calculate_quantum_leap_gap(numpages, pagerange)
    num_forward_leaps = max(0, min(3, int(round(
        float(numpages - pagenumber - pagerange) / quantum_leap_gap) - 0.3)))
    if num_forward_leaps:
        pagerange, pagerangestart, pagerangeend = calculate_pagerange(
            pagenumber, numpages, pagerange)
        leapforward = range(pagerangeend - 1 + quantum_leap_gap,
            pagerangeend - 1 + (num_forward_leaps + 1) * quantum_leap_gap,
            quantum_leap_gap)
    return leapforward
