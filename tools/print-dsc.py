from diva.formats import DSCFormat
from pprint import pprint
from construct import *

import sys

i = SLInt32('i')

with open(sys.argv[1]) as f:
    dsc_data = DSCFormat.parse_stream(f)
    # print dsc_data
    print len(dsc_data.events)
    for i, e in enumerate(dsc_data.events):
        if i > 0 and dsc_data.events[i-1].timestamp > e.timestamp:
            print 'non-monotonic event: %r' % e

    event_ids = set(list(e.other_data[0] for e in dsc_data.events))
    event_data = {eid: {} for eid in event_ids}
    for e in dsc_data.events:
        eid = e.other_data[0]
        field_count = len(e.other_data)
        if field_count not in event_data[eid]:
            event_data[eid][field_count] = 0
        event_data[eid][field_count] += 1

    pprint(event_data)
