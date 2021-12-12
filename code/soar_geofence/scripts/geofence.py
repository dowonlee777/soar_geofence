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
import veroviz as vrv

class Geofence():
    def __init__(self, nodes, maxAGL=20, minAGL=5, closeToFenceDist=2, takeOverDist=1, cornerDist=1):
        '''
        coords: [
                    [[lat, lon], [lat, lon]],
                    ...
                ]
        '''
        self.nodes = nodes
        self.fences = self.init_fence(nodes)
        self.max_alt = maxAGL
        self.min_alt = minAGL
        self.closeToFenceDist = closeToFenceDist
        self.takeOverDist = takeOverDist
        self.cornerDist = cornerDist

    def init_fence(self, nodes):
            
        fences = []
        fences.append(Fence([nodes[-1], nodes[0]], vrv.getHeading(nodes[-1], nodes[0]), id=0))
        for i in range(0, len(nodes)-1):
            heading = vrv.getHeading(nodes[i], nodes[i+1])
            fences.append(Fence([nodes[i], nodes[i+1]], heading, id=i+1))

        return fences
    
    def monitor(self, lat, lon, altAGL, vx, vy, vz, heading):
        # if self.isInFence(lat, lon):
        sorted_dist_fence = self.dist_to_fences(lat, lon)
            
        if sorted_dist_fence[0][0] < self.closeToFenceDist:
            fence_1 = sorted_dist_fence[0][1]
            safe_angles_1 = fence_1.adjust_safe_headings(heading)
            intoFence, vel_angle = fence_1.is_vel_into_fence(fence_1.vels_heading(vx, vy, heading), safe_angles_1)

            if sorted_dist_fence[1][0] < self.closeToFenceDist:
                # corner, acceptable velocities should be away from both fences
                fence_2 = sorted_dist_fence[1][1]
                safe_angles_2 = fence_2.adjust_safe_headings(heading)
                intoFence_2, vel_angle_2 = fence_2.is_vel_into_fence(fence_2.vels_heading(vx, vy, heading), safe_angles_2)

                if intoFence or intoFence_2:
                    print('In corner')
                    vx = 0
                    vy = 0

            else:
                if intoFence:
                    print('Going into fence %d | Velocity Heading: %d | Safe Angles: %s' % (fence_1.id, vel_angle, fence_1.safe_headings) )
                    vx *= 0.8
                    vy *= 0.8

                    if sorted_dist_fence[0][0] < self.takeOverDist:

                        vx_unit, vy_unit = fence_1.slide_fence_vels(vel_angle, safe_angles_1)
                        
                        magnitude = math.sqrt(vx**2 + vy**2)
                        vx = vx_unit * magnitude
                        vy = vy_unit * magnitude
                        print('Goal Heading: %s | Velocity Heading: %f' % (fence_1.safe_headings, fence_1.vels_heading(vx, vy, heading)))
                        # print('vx: %f | vy: %f | vel_heading: %f' % (vx, vy, vel_angle))
                        print(vel_angle, vx, vy)

        if vz > 0:
            if altAGL < self.min_alt:
                vz = 0

        if vz < 0:
            if altAGL > self.max_alt:
                vz = 0

        # else:
        #     print('WARNING: Outside geofence')
        
        return vx, vy, vz

    def isInFence(self, lat, lon):
        return vrv.isPointInPoly(loc=[lat, lon], poly=self.nodes)

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

    def getHeading(self, latCurDeg, lonCurDeg, latGoalDeg, lonGoalDeg):
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

    def dist_to_fences(self, latCur, lonCur):
        dist_fence = []
        for fence in self.fences:
            pos, dist = vrv.closestPointLoc2Path(loc=[latCur, lonCur], path=fence.coords)
            dist = self.getGPSdistance(latCur, lonCur, pos[0], pos[1])
            dist_fence.append([dist, fence])
            # if dist < 3:
            #     return True, fence, dist

        return sorted(dist_fence, key = lambda x: x[0])

        # return False, None, None

class Fence():
    def __init__(self, coords, heading, id=None):
        self.coords = coords
        self.heading = heading
        self.id = id
        if heading >= 180:
            a2 = heading - 180
            # self.safe_headings = (a2, heading)
        else:
            a2 = heading + 180
        
        self.safe_headings = (a2, heading)
    

    def adjust_safe_headings(self, headCur):
        # 
        safe = list(self.safe_headings)

        if headCur >= 180:
            # rotation is CCW from north
            safe[0] += 360-headCur
            safe[1] += 360-headCur
            if safe[0] > 360:
                safe[0] -= 360
            if safe[1] > 360:
                safe[1] -= 360

            # if safe[0] > safe[1]:
            #     # switch
            #     temp = safe[1]
            #     safe[1] = safe[0]
            #     safe[0] = temp
        else:
            # rotation is CW from north
            safe[0] -= headCur
            safe[1] -= headCur
            if safe[0] < 0:
                safe[0] += 360
            if safe[1] < 0:
                safe[1] += 360

            # if safe[0] > safe[1]:
            #     temp = safe[1]
            #     safe[1] = safe[0]
            #     safe[0] = temp        
            
        return safe

    def is_vel_into_fence(self, vel_angle, safe_angles):
        # print(vel_angle)
        if vel_angle is not None:
            if self.safe_headings[0] < self.safe_headings[1]:
                if vel_angle > self.safe_headings[0] and vel_angle < self.safe_headings[1]:
                    return False, None
            elif self.safe_headings[0] > self.safe_headings[1]:
                if vel_angle > self.safe_headings[0] or vel_angle < self.safe_headings[1]:
                    return False, None
                
            return True, vel_angle
        else:
            return False, vel_angle
    
    def vels_heading(self, vx, vy, heading):
        if vx != 0 or vy != 0:
            angle = heading
            if vx != 0:
                theta = math.atan(vy/vx) * (180/math.pi)
                if vy > 0 and vx > 0:
                    # positive theta
                    angle = heading + theta
                elif vy > 0 and vx < 0:
                    # negative theta
                    angle = heading + theta - 180
                elif vy < 0 and vx > 0:
                    # negative theta
                    angle = heading + theta
                elif vy < 0 and vx < 0:
                    # positive theta
                    angle = heading + theta + 180
            elif vy > 0:
                angle = 90 + heading
            elif vy < 0:
                angle = heading - 90

            angle = self.validate_heading(angle)
        
            return angle
        else:
            return None
    
    def slide_fence_vels(self, vel_angle, safe_angles):

        theta1 =  vel_angle - self.safe_headings[0]
        theta2 = vel_angle - self.safe_headings[1]

        if theta1 < 0:
            theta1 = 360 - (theta1 + 360)
        if theta2 < 0:
            theta2 = 360 - (theta2 + 360)
    
        if theta1 < theta2:
            print(vel_angle, safe_angles[0])
            return self.vels_along_fence_relative(safe_angles[0])
        else:
            print(vel_angle, safe_angles[1])
            return self.vels_along_fence_relative(safe_angles[1])
    
    def vels_along_fence_relative(self, goal_angle):
        if goal_angle <= 90:
            vx = math.cos(goal_angle * (math.pi/180))
            vy = math.sin(goal_angle * (math.pi/180))
        elif goal_angle <= 180:
            vx = -math.cos( (180-goal_angle) * (math.pi/180))
            vy = math.sin( (180-goal_angle) * (math.pi/180))
        elif goal_angle <= 270:
            vx = -math.cos( (270-goal_angle) * (math.pi/180))
            vy = -math.sin( (270-goal_angle) * (math.pi/180))
        elif goal_angle <= 360:
            vx = math.cos( (360-goal_angle) * (math.pi/180))
            vy = -math.sin( (360-goal_angle) * (math.pi/180))
    

        return vx, vy

    def validate_heading(self, a):
        if a > 360:
            return a - 360
        elif a < 0:
            return a + 360
        else:
            return a

if __name__ == "__main__":

    nodes = [[42.99559635044619, -78.79735971011293, 181.28],
                [42.99531277502557, -78.79685522306578, 180.59],
                [42.99551134918702, -78.79665526993782, 180.9],
                [42.99579492459777, -78.79715975860931, 181.44]
            ]
        
    gf = Geofence(nodes, maxAGL=22, minAGL=2)

    [print(fence.safe_headings) for fence in gf.fences]
    fence = gf.fences[0]
    print(fence.safe_headings, fence.is_vel_into_fence(310, (0, 0)))
    print(gf.getHeading(42.99559635044619, -78.79735971011293, 42.99579492459777, -78.79715975860931))