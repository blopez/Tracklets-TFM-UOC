#!/usr/bin/env python

import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import random
import time
import argparse
from carla import ColorConverter as cc

def main():

    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '--asynch',
        action='store_true',
        help='Activate asynchronous mode execution')
        
    args = argparser.parse_args()
    
    synchronous_master = False
    
    try:
        # getting client
        client = carla.Client('127.0.0.1', 2000)
        client.set_timeout(2.0)

        # getting world
        world = client.get_world()
        spectator = world.get_actors().filter('spectator')[0]
                
        while True:
            if not args.asynch and synchronous_master:
                world.tick()
            else:
                world.wait_for_tick()
                
                # descomentar para ver las coordenadas actuales del spectator
                t = spectator.get_transform()
                coordinate_str = "(x,y,z; pitch,yaw,roll) = ({},{},{}; {},{},{})".format(t.location.x, t.location.y, t.location.z, t.rotation.pitch, t.rotation.yaw, t.rotation.roll)
                print (coordinate_str)

    finally:

        print('ending')
        print('done.')


if __name__ == '__main__':

    main()
