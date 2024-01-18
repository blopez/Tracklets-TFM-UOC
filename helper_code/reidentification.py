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

def process_img(image, cameraId):
    #print("img received")
    #print(cameraId)
    if image.frame_number % 10 == 0:
        image.convert(cc.Raw)
        image.save_to_disk(f'_out/{cameraId}/{image.frame_number}')
    
def spawn_camera(cameraId, world, camera_bp, x, y, z, pitch, yaw, generate_images=True):
        
    spawnpoint = carla.Transform(carla.Location(x=x,y=y,z=z),carla.Rotation(pitch=pitch,yaw=yaw,roll=0.000017))
    camera = world.spawn_actor(camera_bp, spawnpoint)
    camera_list.append(camera)
    
    if generate_images:
        camera.listen(lambda image: process_img(image, cameraId))
    return camera

pedestrian_list = []
vehicle_list = []
camera_list = []
    
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
        #spectator = world.get_actors().filter('spectator')[0]
        
        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor

        # blueprints for actors (cars, etc)
        blueprint_library = world.get_blueprint_library()
        
        # white model 3
        bp = blueprint_library.filter('model3')[0]
        bp.set_attribute('color', '255,255,255')  # RGB values for yellow color
        spawnPoint = carla.Transform(carla.Location(x=-51.79,y=85.99, z=0.598), carla.Rotation(pitch=0.0, yaw=90.0, roll=0.000000))
        model3 = world.spawn_actor(bp, spawnPoint)
        vehicle_list.append(model3)
        
        # charger
        bp = blueprint_library.filter('charger_2020')[0]
        bp.set_attribute('color', '0,0,0')  # RGB values for black color
        spawnPoint = carla.Transform(carla.Location(x=-48.51,y=93.67, z=0.598), carla.Rotation(pitch=0.0, yaw=90.0, roll=0.000000))
        vehicle = world.spawn_actor(bp, spawnPoint)
        vehicle_list.append(vehicle)
        
        # let white model 3 move
        model3.set_autopilot()
        
        while True:
            if not args.asynch and synchronous_master:
                world.tick()
            else:
                world.wait_for_tick()
                
                # descomentar para ver las coordenadas actuales del spectator
                #t = spectator.get_transform()
                #coordinate_str = "(x,y,z; pitch,yaw,roll) = ({},{},{}; {},{},{})".format(t.location.x, t.location.y, t.location.z, t.rotation.pitch, t.rotation.yaw, t.rotation.roll)
                #print (coordinate_str)

    finally:

        print('ending')
        client.apply_batch([carla.command.DestroyActor(x) for x in pedestrian_list])
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicle_list])
        if (camera_list):
            for camera in camera_list:
                camera.destroy()
        print('done.')


if __name__ == '__main__':

    main()
