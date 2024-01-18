import cv2
import numpy as np
from matplotlib import pyplot as plt

fullBodyCascPath = "./_opencv_test/haarcascade_fullbody.xml"
fullBodyCascade = cv2.CascadeClassifier(fullBodyCascPath)

# Load the image
gray = cv2.imread('./_opencv_test/c.png', 0)
#plt.figure(figsize=(12,8))
#plt.imshow(gray, cmap='gray')
#plt.show()

# Detect faces
faces = fullBodyCascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,flags=cv2.CASCADE_SCALE_IMAGE)

# For each face, Draw rectangle around the face
for (x, y, w, h) in faces:
    cv2.rectangle(gray, (x, y), (x+w, y+h), (255, 255, 255), 3)
    
plt.figure(figsize=(12,8))
plt.imshow(gray, cmap='gray')
plt.show()


# now with yolo
print("trying yolo")
img = cv2.imread('./_opencv_test/c.png')

# Load YOLO file/
net = cv2.dnn.readNet("./_opencv_test/yolov3.weights", "./_opencv_test/yolov3.cfg")
classes = []

# Load class names from coco file
with open("./_opencv_test/coco.names", "r") as f:
    classes = f.read().strip().split("\n")
    
blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
net.setInput(blob)  # Set the input blob for the neural network
outs = net.forward(net.getUnconnectedOutLayersNames()) # Forward pass the input blob through the network to get detections

# Process YOLO output
for out in outs:
    for detection in out:
        scores = detection[5:]
        class_id = np.argmax(scores)        
        confidence = scores[class_id]
        if confidence > 0.5:  # Filter detections by confidence threshold
                
            #print(class_id)
            #print(scores)
        
            center_x = int(detection[0] * img.shape[1])
            center_y = int(detection[1] * img.shape[0])
            width = int(detection[2] * img.shape[1])
            height = int(detection[3] * img.shape[0])

            x = int(center_x - width / 2)
            y = int(center_y - height / 2)

            # Draw  box and label on the frame
            cv2.rectangle(img, (x, y), (x + width, y + height), (0, 255, 0), 2)
            label = f"{classes[class_id]}: {confidence:.2f}"
            cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Display the frame with detections
cv2.imshow(" DISPLAYING : FRAME |  Detections", img)
cv2.waitKey(0)  #continue.