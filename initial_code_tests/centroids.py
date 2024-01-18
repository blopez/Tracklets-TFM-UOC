import cv2
import numpy as np

yolo_weights = './_opencv_test/yolov3.weights'
yolo_config = './_opencv_test/yolov3.cfg'
yolo_classes = './_opencv_test/coco.names'

video = './_opencv_test/video.mp4'

def load_yolo():
    net = cv2.dnn.readNet(yolo_weights, yolo_config)
    classes = []
    with open(yolo_classes, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    layers_names = net.getLayerNames()
    output_layers = [layers_names[i - 1] for i in net.getUnconnectedOutLayers()]
    return net, classes, output_layers

def detect_cars(net, classes, output_layers, img):
    height, width, channels = img.shape
    blob = cv2.dnn.blobFromImage(img, scalefactor=0.00392, size=(416, 416), mean=(0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # Adjust the confidence threshold as needed
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])
    return class_ids, confidences, boxes

def get_centroid(box):
    x, y, w, h = box
    center_x = x + w // 2
    center_y = y + h // 2
    return (center_x, center_y)

def draw_labels_and_boxes(img, class_ids, confidences, boxes, classes):
    for i in range(len(class_ids)):
        class_id = class_ids[i]
        confidence = confidences[i]
        x, y, w, h = boxes[i]
        label = f"{classes[class_id]}: {confidence:.2f}"
        color = (0, 0, 255)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.putText(img, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img

def detectCars(filename):
    net, classes, output_layers = load_yolo()
    vc = cv2.VideoCapture(filename)

    if not vc.isOpened():
        return

    car_count = 0
    tracked_centroids = {}
    img = cv2.imread('./_opencv_test/c.png')

    while True:
        rval, frame = vc.read()
        if not rval:
            break
       

        frame = cv2.resize(img, (800, 600))
        class_ids, confidences, boxes = detect_cars(net, classes, output_layers, frame)

        new_centroids = set()
        for i in range(len(class_ids)):
            obj_id = class_ids[i]
            box = boxes[i]
            confidence = confidences[i]
            if confidence > 0.5:  # Adjust the confidence threshold as needed
                centroid = get_centroid(box)
                print(centroid)
                if centroid not in tracked_centroids:
                    tracked_centroids[centroid] = obj_id
                    new_centroids.add(centroid)

        # Count only when a new car is detected
        if len(new_centroids) > 0:
            car_count += 1

        frame = draw_labels_and_boxes(frame, class_ids, confidences, boxes, classes)
        cv2.putText(frame, f'Car Count: {car_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow("Result", frame)

        if cv2.waitKey(33) == ord('q'):
            break

    vc.release()
    cv2.destroyAllWindows()

detectCars(video)