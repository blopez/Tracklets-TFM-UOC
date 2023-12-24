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

def process_img(image):
    #print("img received")
    image.convert(cc.Raw)
    image.save_to_disk('_out/%08d' % image.frame_number)
    
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
    
    actor_list = []
    camera_list = []

    try:
        # getting client
        client = carla.Client('127.0.0.1', 2000)
        client.set_timeout(2.0)

        # getting world
        world = client.get_world()

        # blueprints for actors (cars, etc)
        blueprint_library = world.get_blueprint_library()
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        
        # should specify image specs?
        camera_bp.set_attribute('image_size_x', '640')
        camera_bp.set_attribute('image_size_y', '360')
        camera_bp.set_attribute('fov', '90') # field of view (degrees)
        
        # getting traffic lights
        traffic_lights = world.get_actors().filter('traffic.traffic_light')
        print(len(traffic_lights))
        
        for traffic_light in traffic_lights:
        
            # getting reference to the traffic light transform
            tl_transform = traffic_light.get_transform()
       
            # offset from the traffic light
            camera_location = carla.Location(x=0, y=0, z=2)
            camera_transform = carla.Transform(tl_transform.location + camera_location, tl_transform.rotation)

            camera = world.spawn_actor(camera_bp, camera_transform, attach_to=traffic_light)
            camera_list.append(camera)
            
            # only one at the moment
            camera.listen(process_img)
            #break
        
        # spawning camera
        #transform = carla.Transform(carla.Location(x=0.8, z=1.7))
        
        
        #camera = world.spawn_actor(camera_bp, world.get_actors().filter('spectator')[0].get_transform())
        #camera.listen(process_img)
        
        while True:
            if not args.asynch and synchronous_master:
                world.tick()
            else:
                world.wait_for_tick()

    finally:

        print('ending')
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        if (camera_list):
            for camera in camera_list:
                camera.destroy()
        print('done.')


if __name__ == '__main__':

    main()
