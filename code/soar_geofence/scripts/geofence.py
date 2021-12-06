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
import math
import numpy as np
import geopy.distance

class Fence():
    def __init__(self, coords):
        '''
        coords: [[lat, lon], ... [lat, lon]]]
        '''
        self.nodes = self.nodes_map(coords)
        self.edges = self.fence_edges(coords)

    def nodes_map(self, coords):
        nodes = {}
        for i in range(0, len(coords)):
            nodes[i] = coords[i]
        return nodes

    def fence_edges(self, coords):
        edges = []

        for v1 in coords:
            dist = np.array([self.getGPSdistance(v1[0], v1[1], v2[0], v2[1]) for v2 in coords])
            sort = np.argsort(dist)
            print(v1, sort, dist)
            edges.append([sort[1], sort[2]])
            # edges.append([coords[sort[1]], coords[sort[2]]])
        return edges


    # Borrowed from soar_rover
    def getGPSdistance(self, lat1deg, lon1deg, lat2deg, lon2deg):
        """
        Distance between two locations in 2D
        Parameters
        ----------
        loc1: list
            First location, in [lat, lon]
        loc2: list
            Second location, in [lat, lon]
        
        Return
        ------
        float
            Distance between to locations.
        """
        
        distMeters = geopy.distance.distance([lat1deg, lon1deg], [lat2deg, lon2deg]).meters

        return distMeters

    def getHeading(latCurDeg, lonCurDeg, latGoalDeg, lonGoalDeg):
        # NOTE:  The lat/lon values in the formulas below are in units of ***[radians]***
        
        latCurRad = latCurDeg*(math.pi/180.0)
        lonCurRad = lonCurDeg*(math.pi/180.0)
        latGoalRad = latGoalDeg*(math.pi/180.0)
        lonGoalRad = lonGoalDeg*(math.pi/180.0)
        
        # 1) What angle is required to travel directly from the current location to the goal location?
        #    See http://www.movable-type.co.uk/scripts/latlong.html
        y = math.sin(lonGoalRad - lonCurRad) * math.cos(latGoalRad)
        x = math.cos(latCurRad)*math.sin(latGoalRad) - math.sin(latCurRad)*math.cos(latGoalRad)*math.cos(lonGoalRad-lonCurRad)
        headingRad = (math.atan2(y, x) + 2*math.pi) % (2*math.pi)  # In the range [0,2*pi]
                
        return (headingRad*(180/math.pi))

    def distance2fence(self, lat, lon):
        return


if __name__ == "__main__":
    coords = [
            [42.99559635044619, -78.79735971011293, 20],
            [42.99531277502557, -78.79685522306578, 20],
            [42.99551134918702, -78.79665526993782, 20],
            [42.99579492459777, -78.79715975860931, 20]
        ]
    gf = Fence(coords)
    print(gf.edges)
    if gf.getGPSdistance(coords[1][0], coords[1][1], coords[0][0], coords[0][1]) > gf.getGPSdistance(coords[1][0], coords[1][1], coords[3][0], coords[3][1]):
        print('asdf')