import carla
from carla import ColorConverter as cc

actor_list = []
camera_list = []
    
def spawn_car_with_autopilot_and_camera(world):

    # vehicle blueprint
    vehicle_blueprint = world.get_blueprint_library().find('vehicle.audi.tt')

    # autopilot
    vehicle_blueprint.set_attribute('role_name', 'autopilot')

    # location to spawn
    spawn_location = carla.Location(x=100, y=100, z=2)  # Adjust the location as needed
    spawn_transform = carla.Transform(spawn_location)

    # spawn
    vehicle = world.spawn_actor(vehicle_blueprint, spawn_transform)
    vehicle.set_autopilot(True)
    actor_list.append(vehicle)

    # RGB camera to the vehicle
    camera_blueprint = world.get_blueprint_library().find('sensor.camera.rgb')
    camera_blueprint.set_attribute('image_size_x', '1920')
    camera_blueprint.set_attribute('image_size_y', '1080')
    camera_blueprint.set_attribute('fov', '90')

    # spawn camera
    camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))  # Adjust the offset as needed
    camera = world.spawn_actor(camera_blueprint, camera_transform, attach_to=vehicle)
    camera_list.append(camera)

    # Register a callback function to process camera images
    camera.listen(lambda image: process_image(image))

    print(f"Spawned vehicle {vehicle.id} with autopilot and attached camera {camera.id}")

def process_image(image):
    # Process the camera image if needed
    #pass
    image.convert(cc.Raw)
    image.save_to_disk('_out/%08d' % image.frame_number)

if __name__ == "__main__":
    # Connect to the CARLA server
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # Get the world
    world = client.get_world()

    # Spawn a car with autopilot and attach a camera
    spawn_car_with_autopilot_and_camera(world)

    try:
        while True:
            # Run your simulation logic here
            world.wait_for_tick()
    finally:
        print("Destroying actors")
        if (camera_list):
            for camera in camera_list:
                camera.destroy()
        client.apply_batch([carla.command.DestroyActor(x) for x in actor_list])
        #client.disconnect()