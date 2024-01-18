import carla

def add_camera_to_traffic_lights(world):
    # Get all traffic lights in the simulation
    traffic_lights = world.get_actors().filter('traffic.traffic_light')

    for traffic_light in traffic_lights:
        # Get the transform of the traffic light
        transform = traffic_light.get_transform()

        # Offset the camera from the traffic light
        camera_location = carla.Location(x=0, y=0, z=2)  # Adjust the offset as needed
        camera_transform = carla.Transform(transform.location + camera_location, transform.rotation)

        # Create RGB camera blueprint
        camera_blueprint = world.get_blueprint_library().find('sensor.camera.rgb')
        camera_blueprint.set_attribute('image_size_x', '1920')
        camera_blueprint.set_attribute('image_size_y', '1080')
        camera_blueprint.set_attribute('fov', '90')

        # Create and attach the camera to the traffic light
        camera = world.spawn_actor(camera_blueprint, camera_transform, attach_to=traffic_light)

        # Register the camera with the CARLA server
        camera.listen(lambda image: process_image(image))

        # Print camera information
        print(f"Added camera to traffic light {traffic_light.id}")

def process_image(image):
    # Process the camera image if needed
    pass

if __name__ == "__main__":
    # Connect to the CARLA server
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # Get the world
    world = client.get_world()

    # Add cameras to traffic lights
    add_camera_to_traffic_lights(world)

    try:
        while True:
            # Run your simulation logic here
            world.tick()
    finally:
        print("Destroying actors")
        client.disconnect()
