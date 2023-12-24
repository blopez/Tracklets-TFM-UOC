import carla

def create_tracklet(world, vehicle):
    # Create a new actor for the tracklet (barrier)
    tracklet_blueprint = world.get_blueprint_library().find('static.prop.barrel')
    tracklet_transform = vehicle.get_transform()

    # Offset the tracklet slightly above the vehicle
    tracklet_transform.location.z += 2.0

    tracklet_actor = world.spawn_actor(tracklet_blueprint, tracklet_transform, attach_to=vehicle)

    # Attach the tracklet to the vehicle
    tracklet_actor.set_simulate_physics(False)  # Make the tracklet static

    print(f"Created tracklet for vehicle {vehicle.id}")

if __name__ == "__main__":
    # Connect to the CARLA server
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # Get the world
    world = client.get_world()

    # Get a blueprint for a vehicle
    vehicle_blueprint = world.get_blueprint_library().find('vehicle.audi.tt')

    # Spawn a vehicle
    spawn_location = carla.Location(x=100, y=100, z=2)
    vehicle = world.spawn_actor(vehicle_blueprint, carla.Transform(spawn_location))

    try:
        # Create a tracklet for the vehicle
        create_tracklet(world, vehicle)

        while True:
            # Run your simulation logic here
            world.wait_for_tick()

    finally:
        print("Destroying actors")

        # Destroy all actors in the world
        for actor in world.get_actors():
            actor.destroy()

