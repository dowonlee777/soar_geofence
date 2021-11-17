#!/usr/bin/env python3
import math

'''
For calculating lat/lon given deviations in cartesian (from an origin coordinate). And vice versa

Usage: 

import coordinate

# Define origin
origin = coordinate.Origin(lat, lon)

# lat, lon given x,y offset from origin
offLat, offLon = coordinate.Cartesian(origin, x, y).toLatLon()

# To x, y coord given origin, lat and lon
x, y = coordinate.LatLon(origin, offLat, offLon).toCartesian()

Using approximation: 
    - (Second Answer) https://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters

'''

# Radius of Earth m
# _R = 6378137
_R = 6371000

class Origin():
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

class Cartesian():
    def __init__(self, origin, x=None, y=None, z=0):
        '''
        - origin : coordinate.Origin(lat, lon) object
        - x : Offset in x direction (meters)
        - y : Offset in y direction (meters)
        - z : Offset in z direction (meters)
        '''
        self.origin = origin
        self.x = x
        self.y = y
        self.z = z
    
    def toLatLon(self):
        '''
        - Get the lat/lon given cartesian offsets from an origin (lat/lon) 
        '''
        # dLat = self.y/_R
        # dLon = self.x/(_R*math.cos(math.radians(self.origin.lat)))
        # lat = self.origin.lat + dLat * 180/math.pi
        # lon = self.origin.lon + dLon * 180/math.pi

        # #Conversion 
        # lat = math.asin(self.z / _R)
        # lon = math.atan2(self.y, self.x)

        # # Convert to degrees
        # lat = math.degrees(lat)
        # lon = math.degrees(lon)

        return self.toLat(), self.toLon()

    def toLon(self):
        '''
        - Returns the longitude given an "x" meter offset from the coordinate.Origin(lat,lon)
        '''
        dLon = self.x/(_R*math.cos(math.radians(self.origin.lat)))
        lon = self.origin.lon + dLon * 180/math.pi

        return lon

    def toLat(self):
        '''
        - Returns the latitude given an "y" meter offset from the coordinate.Origin(lat,lon)
        '''
        dLat = self.y/_R
        lat = self.origin.lat + dLat * 180/math.pi

        return lat

class LatLon():
    def __init__(self, origin, lat=None, lon=None):
        self.origin = origin
        self.lat = lat
        self.lon = lon

    def toCartesian(self):
        '''
        - Get the cartesian (x,y) offsets given a lat/lon, from an origin (lat/lon)
        
        Returns:
            - x : offset in meters
            - y : offset in meters
        '''
        lat_rad = math.radians((self.lat - self.origin.lat))
        lon_rad = math.radians((self.lon - self.origin.lon))

        y = lat_rad * _R
        x = lon_rad * (_R*math.cos(math.radians(self.origin.lat)))
        # lat_rad = math.radians(self.lat)
        # lon_rad = math.radians(self.lon)

        # # Convesion
        # x = _R * math.cos(lat_rad) * math.cos(lon_rad)
        # y = _R * math.cos(lat_rad) * math.sin(lon_rad)
        # z = _R * math.sin(lat_rad)

        return x,y

if __name__ == "__main__":
    print(Cartesian(Origin(43.001932358569476, -78.78695011138917), -80, -220).toLatLon())
    print(LatLon(Origin(43.001932358569476, -78.78695011138917), 42.99995385103645, -78.78793387603166).toCartesian())

    # origin = Origin(43.002302238527115, -78.78954908497354)
    # nodes = [
    #     [43.00409918490101, -78.79395903826722],
    #     [43.0074121779378, -78.792818472642],
    #     [43.00741740899428, -78.78808347922447],
    #     [43.00502987481641, -78.78525608303715],
    #     [43.00299070042055, -78.78667201024965],
    #     [43.00510028846681, -78.79026501096949],
    #     [43.00488060224134, -78.78851978740701],
    # ]
    # print('Red drone nodes:')
    # for n in nodes:
    #     print(LatLon(origin, n[0], n[1]).toCartesian())

    
    # blueNodes = [
    #     [43.00899697229597, -78.79020779007394],
    #     [43.00584303051747, -78.7902721630903]
    # ]
    # print('Blue drone nodes:')
    # for n in blueNodes:
    #     print(LatLon(origin, n[0], n[1]).toCartesian())

    # polyRiskOrigin = Origin(43.006614111441664, -78.78630730105068)
    # polyRisk = [
    #     [43.00614355065728, -78.78562078961731],
    #     [43.00535927227957, -78.78772323611965],
    #     [43.00731471780538, -78.7855564265516]
    # ]

    # print('Polyhedral Risk Region:')
    # print('Reference: ', LatLon(origin, polyRiskOrigin.lat, polyRiskOrigin.lon).toCartesian())
    # for r in polyRisk:
    #     print(LatLon(polyRiskOrigin, r[0], r[1]).toCartesian())

    
    # sphereRiskOrigin = Origin(42.998966, -78.798637)