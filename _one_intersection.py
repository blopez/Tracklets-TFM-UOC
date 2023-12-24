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
    image.convert(cc.Raw)
    image.save_to_disk(f'_out/{cameraId}_{image.frame_number}')
    
def spawn_camera(cameraId, world, camera_bp, x, y, z, pitch, yaw, generate_images=True):
        
    spawnpoint = carla.Transform(carla.Location(x=x,y=y,z=z),carla.Rotation(pitch=pitch,yaw=yaw,roll=0.000017))
    camera = world.spawn_actor(camera_bp, spawnpoint)
    camera_list.append(camera)
    
    if generate_images:
        camera.listen(lambda image: process_img(image, cameraId))

actor_list = []
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
        spectator = world.get_actors().filter('spectator')[0]
        
        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor

        # blueprints for actors (cars, etc)
        blueprint_library = world.get_blueprint_library()
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        
        # should specify image specs?
        camera_bp.set_attribute('image_size_x', '1280')
        camera_bp.set_attribute('image_size_y', '720')
        camera_bp.set_attribute('fov', '75') # field of view (degrees)
        
        # spawning Camera1 by position
        spawn_camera(cameraId=1, world=world, camera_bp=camera_bp, x=-60.423583, y=123.316581, z=7.886553, pitch=-40, yaw=-20, generate_images=True)
        
        # spawning Camera2 by position
        spawn_camera(cameraId=2, world=world, camera_bp=camera_bp, x=-34.661411, y=123.436012, z=5.335992, pitch=-34.902976989746094, yaw=-168.395263671875, generate_images=True)
        
        # fixed walker(s)
        batch = []
        blueprintsWalkers = world.get_blueprint_library().filter("walker.pedestrian.*")
        walker_bp = random.choice(blueprintsWalkers)
        walker_transform = carla.Transform(carla.Location(-44.00669860839844,119.00493621826172,0.801214873790741))
        
        walker = SpawnActor(walker_bp, walker_transform)
        batch.append(walker)
        results = client.apply_batch_sync(batch, True)
        for i in range(len(results)):
            if results[i].error:
                print(results[i].error)
            else:
                actor_list.append(results[i].actor_id)
        
        # make the walker walk to the end of the zebra crossing
        move = True
        if (move):            
            end_transform = carla.Transform(carla.Location(x=-55.61404800415039, y=118.53377532958984), carla.Rotation())
            
            walker_instance = world.get_actor(actor_list[-1])
            direction = end_transform.location - walker_instance.get_location()
                        
            walker_instance.apply_control(carla.WalkerControl(direction=direction, speed=0.1))
        
        #spawnpoint = carla.Transform(carla.Location(x=-60.423583,y=123.316581,z=7.886553),carla.Rotation(pitch=-40,yaw=-20,roll=0.000017))
        #camera = world.spawn_actor(camera_bp, spawnpoint)
        #camera_list.append(camera)
        
        #camera.listen(process_img)
        
        # spawning camera
        #transform = carla.Transform(carla.Location(x=0.8, z=1.7))
        
        
        #camera = world.spawn_actor(camera_bp, world.get_actors().filter('spectator')[0].get_transform())
        #camera.listen(process_img)
        
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
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        if (camera_list):
            for camera in camera_list:
                camera.destroy()
        print('done.')


if __name__ == '__main__':

    main()
