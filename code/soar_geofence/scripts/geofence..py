#!/usr/bin/env python3

'''
    "geofence": {
        "poly": [[42.99559635044619, -78.79735971011293, 181.28],
            [42.99531277502557, -78.79685522306578, 180.59],
            [42.99551134918702, -78.79665526993782, 180.9],
            [42.99579492459777, -78.79715975860931, 181.44]],
        "ceilingMetersAGL": 22
    }
'''


class Geofence():
    def __init__(self, coords):
        '''
        coords: [[lat, lon], ... [lat, lon]]]
        '''
        self.fence = coords


    def distance2fence(self, lat, lon):
        return