import cv2

from enum import Enum
class Movement(Enum):
    NONE = 0
    APPROACHING = 1
    LEAVING = 2

class Actor():
    """
    Represents each object found in an image, processed by a single camera.

    Attributes
    ----------
    id : int
        unique identifier, assigned by the camera image recognition
    type : str
        the type of entity, according to the COCO dataset (car, person, bike, etc)
    color : str
        the name of the identified color of the object
    size : double
        the normalized area of the recognized object, within the context of the full image (optional for the common objects)
    movement: Enum(Movement)
        indicates if the object is moving towards this camera (APPROACHING), or is getting away (LEAVING)
    last_step: int
        step number in which this Actor was last seen (optional for the common objects)
    commonCamerasIds: {}
        if this is a common object: dictionary of the ids of this common object in the different cameras
    """
    def __init__(self, id, type, color, size=0, creation_step=0):
        self.id = id
        self.type = type
        self.color = color
        self.size = size
        self.movement = "Approaching"
        self.last_step = creation_step
        self.commonCamerasIds = {}
        
    def plotCommon(self):
    
        # Returns the common actors in a readable format (string)
        result = ""
        where = ""
        if self.commonCamerasIds:
            for cameraId in self.commonCamerasIds:
                objId = self.commonCamerasIds[cameraId]
                where += f"CAM{cameraId} id {objId} "
                
        result += f"[CommonId={self.id}, Type={self.type}, Color={self.color}, From={where} - "
        
        return result
        
class Camera():
    """
    Current data of a given camera.

    Attributes
    ----------
    name : str
        name of the camera
    actors : {}
        dictionary of int, Actor. Contains the detected objects by this camera
    """
    def __init__(self, name):
        self.name = name
        self.actors = {}
        
    def plot(self):
    
        # Returns the actors in a readable format (string)
        result = ''
        if self.actors and len(self.actors) > 0:
            for actorId in self.actors.keys():
                actor = self.actors[actorId]
                result += f"[Id={actor.id}, Type={actor.type}, Color={actor.color}, Size={actor.size}, Dir={actor.movement}, Last={actor.last_step}] - "
        
        return result

class Group():
    """
    Current data of a given group.

    Attributes
    ----------
    name : str
        name of the group (e.g. Group1)
    cameras : {}
        dictionary of int, Camera. Contains all the info of the cameras
    common: []
        structure of common identified objects among all the cameras
    dangers: []
        structure of dangers identified from the common objects
    __common_id: int
        identifier of a new identified common object (auto-incremental)
    """
    def __init__(self, name):
        self.name = name
        self.cameras = {}  
        self.common = []
        self.dangers = []
        self.__common_id = 0
        
    def getNewCommonId(self):
        self.__common_id += 1
        return self.__common_id

class CentralCameraSystem():

    # data structure to store the entities identified by each camera group
    # key = groupId
    # value = {
    #   key = cameraId
    #   value = Camera Object, that contains a Dictionary of Actor objects
    #}
    data = None
    
    # step number, to determine where an object is no longer in presence
    n_step = 0

    def __init__(self):
    
        # initialization
        self.initialized = True
        self.data = {}
    
    def plotCommon(self):
    
        # Returns the common actors in a readable format (string)
        result = ''
        if self.data and self.data.common and len(self.data.common) > 0:
            for actorId in self.data.common.keys():
                actor = self.data.common[actorId]
                where = ""
                if actor.commonCamerasIds:
                    for cameraId in actor.commonCamerasIds:
                        objId = actor.commonCamerasIds[cameraId]
                        where += f"CAM{cameraId} id {objId} "
                result += f"[CommonId={actor.id}, Type={actor.type}, Color={actor.color}, Size={actor.size}, Dir={actor.movement}, From={where}, Last={actor.last_step}] - "
        
        return result
    
    def updateCamera(self, groupId, cameraId, objects=None):
        
        # step 1: getting data structure groupId-cameraId (either getting or appending if not appended yet)
        groupData = None        
        if groupId not in self.data.keys():
            
            # non existing group yet => adding with the ongoing camera
            groupData = Group(f"group-{groupId}")
            self.data[groupId] = groupData
            
        else:
            
            # the group already exists in the dictionary => update the camera
            groupData = self.data[groupId]
            
        # getting cameraData after having the groupData
        cameraData = None
        if cameraId not in groupData.cameras.keys():
            
            # camera does not exist => creating and appending to group
            cameraData = Camera(f"CAM-{cameraId}")
            groupData.cameras[cameraId] = cameraData
            
        else:
        
            # camera exists => getting it
            cameraData = groupData.cameras[cameraId]
                        
        # step 2: updating the given camera
        if cameraData:
            
            # appending or updating objects to camera info
            if objects:
                for obj in objects:
                
                    if obj.id not in cameraData.actors.keys():
                        
                        # appending new object to camera data
                        actor = Actor(obj.id, obj.type, obj.color, obj.size, self.n_step)
                        cameraData.actors[obj.id] = actor
                        
                    else:
                        
                        # updating object
                        actor = cameraData.actors[obj.id]
                        actor.type = obj.type
                        actor.color = obj.color
                        actor.last_step = self.n_step
                        
                        # tracking: keep track of whether the object is getting bigger or smaller
                        if obj.size > actor.size:
                            #actor.movement = Movement.APPROACHING
                            actor.movement = "Approaching"
                        elif obj.size < actor.size:
                            #actor.movement = Movement.LEAVING
                            actor.movement = "Leaving"
                        
                        actor.size = obj.size                         
             
            # todo: also remove from camera_data those object not present in the current camera frame (n_step - last_step > n)
            if cameraData.actors:
            
                objectIdsToDelete = []
                for objectId in cameraData.actors:
                    object = cameraData.actors[objectId]
                    if self.n_step - object.last_step > 2:
                        objectIdsToDelete.append(objectId)
                        
                if objectIdsToDelete:
                    for objectId in objectIdsToDelete:
                        del cameraData.actors[objectId]
            
        else:
        
            # login or raise error
            print("ERROR: Camera data not found")       
        
    def step(self):
        self.n_step += 1
        
        # for each step, we identify common objects along the group cameras
        if self.data:
            for groupId in self.data.keys():
                
                # evaluating each group (e.g. group1)
                group = self.data[groupId]
                
                previousCommon = group.common
                group.common = []
                if group.cameras:
                    
                    # evaluating each camera (e.g. camera1)
                    for cameraId in group.cameras.keys():
                        camera = group.cameras[cameraId]
                        if camera.actors:
                        
                            # evaluating each camera object (e.g. red car with id 55) 
                            for objectId in camera.actors.keys():
                                obj = camera.actors[objectId]
                                
                                # searching for the same objects in the other cameras (not identified yet as common)
                                same_objects = self.search_similar_objects(currentObject=obj, cameras=group.cameras, currentCameraId=cameraId, common=group.common)
                                if same_objects and len(same_objects) > 0:
                                    
                                    # same objects found in other cameras => prepare and add to common structure
                                    
                                    # preparing common actor (previous common_id or new one)
                                    commonId = 0
                                    if previousCommon:
                                        for previousCommonObj in previousCommon:
                                            if self.same_objects(previousCommonObj, obj):
                                                commonId = previousCommonObj.id
                                    if commonId == 0:
                                        commonId = group.getNewCommonId()
                                    commonActor = Actor(commonId, obj.type, obj.color)
                                    
                                    # adding object id in current camera
                                    commonActor.commonCamerasIds[cameraId] = objectId
                                    
                                    # adding object id in the other cameras
                                    for cameraIdForSameObj in same_objects.keys():
                                        if not cameraIdForSameObj in commonActor.commonCamerasIds:
                                            commonActor.commonCamerasIds[cameraIdForSameObj] = same_objects[cameraIdForSameObj].id
        
                                    # adding to common structure
                                    group.common.append(commonActor)
    
    def identify_dangers(self):
    
        # for each group, we identify possible dangers within the common objects already identified
        if self.data:
            for groupId in self.data.keys():
                
                # evaluating each group (e.g. group1)
                group = self.data[groupId]
                group.dangers = []
                if group.common:
                
                    # for each common object, check the heuristics to identify dangers
                    
                    # in the case of group 1: 
                    #   if !person in CAM3 is approaching, and 
                    #   person in CAM1 or person in CAM2
                    #       => DANGER
                    
                    # search for !person in CAM3
                    treatedCommonIds = {}
                    for commonObj in group.common:
                        if not commonObj.id in treatedCommonIds and commonObj.commonCamerasIds and 3 in commonObj.commonCamerasIds and commonObj.type != 'person':
                            
                            objInCam3 = group.cameras[3].actors[commonObj.commonCamerasIds[3]]
                            
                            # !person found in CAM3 => let's check the approaching
                            if objInCam3.movement == "Approaching":
                            
                                # !person found in CAM3 approaching => let's check if person in CAM1 or in CAM2
                                for commonObj2 in group.common:
                                    if commonObj2.type == 'person' and commonObj2.commonCamerasIds and (2 in commonObj2.commonCamerasIds or 1 in commonObj2.commonCamerasIds) :
                                    
                                        # person in CAM1 or in CAM2 => danger!
                                        group.dangers.append(f"DANGER: CommonId {commonObj.id} in CAM3 and CommonId {commonObj2.id} in CAM1 or CAM2")
                                        
                                        # mark common object as danger, to avoid repetition
                                        if not commonObj.id in treatedCommonIds:
                                            treatedCommonIds[commonObj.id] = True
                                        if not commonObj2.id in treatedCommonIds:
                                            treatedCommonIds[commonObj2.id] = True
    
    def same_objects(self, object1, object2):
    
        # simple checking: same object type and color (just same type in the case of person)
        if object1.type == 'person' and object2.type == 'person':
            return True
            
        return object1.type == object2.type and object1.color == object2.color
    
    def search_similar_objects(self, currentObject, cameras, currentCameraId, common):
    
        # first of all, check if this object has already been marked as common => this way we'll skip it
        if common and len(common) > 0:
            for commonObj in common:
                if commonObj.commonCamerasIds and currentCameraId in commonObj.commonCamerasIds:
                    if commonObj.commonCamerasIds[currentCameraId] == currentObject.id:
                        # current object already found marked as common => break and skip
                        return
                    
        
        # structure: {cameraId, object}
        result = {}
        if cameras:
            for cameraId in cameras.keys():
            
                # avoiding current camera again
                if cameraId != currentCameraId:
                   camera = cameras[cameraId]
                   if camera.actors:
                   
                        # for each object in a different camera, let's evaluate if it's the same actor
                        for objectId in camera.actors.keys():
                            object = camera.actors[objectId]
                            
                            # simple checking: same object type and color
                            if self.same_objects(object, currentObject):
                                if not cameraId in result:
                                    result[cameraId] = object
        return result
        
    def sync(self):
        """
        Looks for same entities in different cameras, within the same group. 
        """
        
        print("Syncing")
        
        print("Sync done")