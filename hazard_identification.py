from ultralytics import YOLO
import cv2
import numpy as np
import glob
import re
import time
from pathlib import Path
import os.path
from ccs import CentralCameraSystem
from ccs import Actor
import json

from codecarbon import OfflineEmissionsTracker
tracker = OfflineEmissionsTracker(country_iso_code="ESP")
tracker.start()

# load yolov8 models for the different cameras
model = YOLO('yolov8n.pt')
model2 = YOLO('yolov8n.pt')
model3 = YOLO('yolov8n.pt')

# parameters for the yolo tracking (ref https://docs.ultralytics.com/modes/predict/#working-with-results)
conf = 0.5 # confidence threshold for object detection
show_labels = False
show_conf = False
classes = [0, 1, 2, 3, 5, 6, 7, 16] # filter results by class, i.e. classes=0, or classes=[0,2,3]

# helper to get classNames from ids
coco_classes = {0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck', 8: 'boat', 9: 'traffic light', 10: 'fire hydrant', 11: 'stop sign', 12: 'parking meter', 13: 'bench', 14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow', 20: 'elephant', 21: 'bear', 22: 'zebra', 23: 'giraffe', 24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase', 29: 'frisbee', 30: 'skis', 31: 'snowboard', 32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove', 36: 'skateboard', 37: 'surfboard', 38: 'tennis racket', 39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich', 49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza', 54: 'donut', 55: 'cake', 56: 'chair', 57: 'couch', 58: 'potted plant', 59: 'bed', 60: 'dining table', 61: 'toilet', 62: 'tv', 63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster', 71: 'sink', 72: 'refrigerator', 73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush'}

def coco_class_to_string(classId):
    if classId in coco_classes:
        return coco_classes[classId]
    else:
        return 'unknown'

def calculate_area(xywhn):
    if xywhn is not None:
        return round(float(xywhn[2] * xywhn[3]), 6)
    else:
        return 0

def calculate_color(img):

    hsvFrame = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # ranges dict: first is upper range and second is lower range
    color_dict_HSV = {'black': [[180, 255, 30], [0, 0, 0]],
              'white': [[180, 18, 255], [0, 0, 231]],
              'red1': [[180, 255, 255], [159, 50, 70]],
              'red2': [[9, 255, 255], [0, 50, 70]],
              'green': [[89, 255, 255], [36, 50, 70]],
              'blue': [[128, 255, 255], [90, 50, 70]],
              'yellow': [[35, 255, 255], [25, 50, 70]],
              'purple': [[158, 255, 255], [129, 50, 70]],
              #'orange': [[24, 255, 255], [10, 50, 70]],
              'gray': [[180, 18, 230], [0, 0, 40]]}

    colors_result = {}
    for color_name in color_dict_HSV:
    
        # for each HSV color range, getting the mask to obtain the number of pixels within each range
        mask = cv2.inRange(hsvFrame, np.array(color_dict_HSV[color_name][1], np.uint8), np.array(color_dict_HSV[color_name][0], np.uint8))
        pixels_inrange = np.sum(mask==255)
        colors_result[color_name] = pixels_inrange
    
    # getting most probable color
    #print(colors_result)
    most_probable_color = max(colors_result, key=colors_result.get)    
    
    # handling red1-red2
    if most_probable_color == 'red1' or most_probable_color == 'red2':
        most_probable_color = 'red'
    
    #print(most_probable_color)
    return most_probable_color

def postprocess_yolo_results(cameraId, yoloResults, showLabels=True, showConf=True):
    
    if yoloResults:

        # CCS data for camera
        objects = []                       

        # plot results to obtain objects boxes and so on
        frame = yoloResults[0].plot(labels=showLabels, conf=showConf)

        for r in yoloResults:
            boxes = r.boxes.cpu().numpy()
            if boxes and boxes.id is not None:
                i = 0
                for id in boxes.id:
                
                    # Step 1: extracting the color each detected object
                    
                    # getting the corner points of the detected object
                    r = boxes.xyxy[i].astype(int)
                    
                    # building sub image of the detected object, from the original frame
                    subImage = frame[r[1]:r[3], r[0]:r[2]]
                    
                    # only debugging => saving this img to disk
                    #cv2.imwrite(f'_test/{i}.png', subImage)
                    
                    # finally getting the most probable color of each object
                    itemColor = calculate_color(subImage)
            
                    # using normalize xywhn to obtain relative area within image
                    catName = coco_class_to_string(boxes.cls[i])
                    n_size = calculate_area(boxes.xywhn[i])
                    print(f"[CAM{cameraId}] Object id {int(id)} is a {catName} with color={itemColor} and n_area={n_size}")
                    
                    # appending object to CCS structure
                    objects.append(Actor(id=int(id), type=catName, color=itemColor, size=n_size ))
                    
                    i+=1
            
            #print("IDS " + str(boxes.id))
            #print("Classes " + str(boxes.cls))
            #print(boxes.cls)
    
        # updating CCS for camera 1
        ccs.updateCamera(groupId=1, cameraId=cameraId, objects=objects)
    return frame

numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

path_to_files = './test_yolo_multicamera/1'
path_to_second = './test_yolo_multicamera/2'
path_to_third = './test_yolo_multicamera/3'
files = sorted(glob.glob(f"{path_to_files}/*.png"), key=numericalSort)
if files:

    # integrating CCS (Central Camera System) as the central unit
    ccs = CentralCameraSystem()
    
    # creating 3 cameras within the same group
    ccs.updateCamera(groupId=1, cameraId=1)
    ccs.updateCamera(groupId=1, cameraId=2)
    ccs.updateCamera(groupId=1, cameraId=3)

    print(f"{len(files)} files in directory")
    for img in files:
        
        fileName = Path(img).name
        
        # looking for frame in second camera
        secondCameraFile = f"{path_to_second}/{fileName}"
        if (os.path.isfile(secondCameraFile)):
        
            # same frame exist in both cameras => we can continue
            time.sleep(0.1)
            
            if ccs.n_step == 8 or ccs.n_step == 29 or ccs.n_step == 33:
                cv2.waitKey(0)
            
            # first camera
            frame1 = cv2.imread(img)                    
            results1 = model.track(frame1, persist=True, conf=conf, classes=classes)
            
            # second camera
            frame2 = cv2.imread(secondCameraFile)                    
            results2 = model2.track(frame2, persist=True, conf=conf, classes=classes)
            
            # third camera (if exists)
            frame3 = None
            results3 = None            
            thirdCameraFile = f"{path_to_third}/{fileName}"
            if (os.path.isfile(thirdCameraFile)):
                frame3 = cv2.imread(thirdCameraFile)
                results3 = model3.track(frame3, persist=True, conf=conf, classes=classes)
            
            # processing frame 1
            postprocessed_frame1 = postprocess_yolo_results(cameraId=1, yoloResults=results1, showLabels=show_labels, showConf=show_conf)
            
            # postprocessing frame 2
            postprocessed_frame2 = postprocess_yolo_results(cameraId=2, yoloResults=results2, showLabels=show_labels, showConf=show_conf)
            
            # postprocessing frame 3 (if camera3)
            if results3:
                postprocessed_frame3 = postprocess_yolo_results(cameraId=3, yoloResults=results3, showLabels=show_labels, showConf=show_conf)
            
            # stepping in CCS
            ccs.step()
            
            # analyze dangers
            ccs.identify_dangers()
            
            # VISUALIZATION
            
            # building visualization (2 or 3 columns) depending on the feed
            if results3:
                horizontal_stack = np.hstack((postprocessed_frame1, postprocessed_frame2, postprocessed_frame3 ))
                bottom_image = np.zeros((200, 1920, 3), dtype=np.uint8)   
            else:
                horizontal_stack = np.hstack((postprocessed_frame1, postprocessed_frame2, ))
                bottom_image = np.zeros((200, 1280, 3), dtype=np.uint8)   
            
            # CCS text: items by camera
            bottom_image = cv2.putText(bottom_image, f"Step: {ccs.n_step}", (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1, cv2.LINE_AA)
            bottom_image = cv2.putText(bottom_image, f"CAM1 ({len(ccs.data[1].cameras[1].actors)}) " + ccs.data[1].cameras[1].plot(), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            bottom_image = cv2.putText(bottom_image, f"CAM2 ({len(ccs.data[1].cameras[2].actors)}) " + ccs.data[1].cameras[2].plot(), (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            bottom_image = cv2.putText(bottom_image, f"CAM3 ({len(ccs.data[1].cameras[3].actors)}) " + ccs.data[1].cameras[3].plot(), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            
            # CCS text: common stuff
            cv2.putText(bottom_image, "----------------", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(bottom_image, f"COMMON ({len(ccs.data[1].common)})", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            #ccsText = f"COMMON ({len(ccs.data[1].common)}) " + json.dumps(ccs.data[1].common, default=lambda __o: __o.__dict__)
            
            label_y = 110
            if len(ccs.data[1].common) > 0:
                            
                for commonObj in ccs.data[1].common:
                    #cv2.putText(bottom_image, json.dumps(commonObj, default=lambda __o: __o.__dict__), (10, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.putText(bottom_image, commonObj.plotCommon(), (10, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
                    label_y += 15
           
            # Dangers if any
            danger_y = 95
            if ccs.data[1].dangers and len(ccs.data[1].dangers) > 0:
                
                cv2.putText(bottom_image, f"DANGERS ({len(ccs.data[1].dangers)})", (640, danger_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1, cv2.LINE_AA)
                danger_y += 15
                
                for danger in ccs.data[1].dangers:
                    cv2.putText(bottom_image, danger, (640, danger_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1, cv2.LINE_AA)
                    danger_y += 15
                
            # final ui stack
            vertical_stack = np.vstack((horizontal_stack, bottom_image))            
            cv2.imshow('Intersection cameras', vertical_stack)
            
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break        
                
tracker.stop()