# -*- coding: utf-8 -*-
"""cam-localisation-test.ipynb

Automatically generated by Colaboratory.

"""

"""
'''
Compute the localisation performance of class activatio mapping on the test set.
"""

import cv2
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy import ndimage
import time

import keras
from keras.layers import Dense,GlobalAveragePooling2D
from keras.applications import ResNet50, InceptionV3, inception_v3, resnet50, mobilenet_v2, MobileNetV2
from keras.preprocessing import image
# from keras.applications.resnet50 import preprocess_input, decode_predictions
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Model
from keras.optimizers import Adam, RMSprop
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint
from keras.models import load_model
from keras import backend as K

import random
import cv2
import tensorflow as tf
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# from google.colab import drive
# drive.mount('/content/drive')

filepath="drive/My Drive/MSc dataset/food5k/Food-5K/models/resnet50_last_6_256.best.hdf5"
model = load_model(filepath)

def get_intermediate_results(model):
    last_conv_activation_layer = model.layers[-3]
    final_dense = model.layers[-1]
    weights = final_dense.get_weights()[0]
    #print(f'weigths shape: {weights.shape}')
    conv_out_func = K.function([model.input], [last_conv_activation_layer.output])
    return weights, conv_out_func

def visualizeCAM(img_path, weights, conv_out_func, preprocess_func, class_index, return_cam=False, visualize=True, input_shape=(256, 256)):
    img = image.load_img(img_path) # height, width, channel
    img = image.img_to_array(img)
    #img = cv2.imread(img_path) 
    ori_img = img.copy()
    #print(ori_img.shape)
    img = cv2.resize(img, input_shape)
    # preprocess the image
    x = np.expand_dims(img, axis=0)
    x = preprocess_func(x)
    # prediction
    #pred = model.predict(x)[0]
    #print(f'Prediction: {pred}')
    conv_out = conv_out_func([x])[0][0]
    #print(f'conv shape: {conv_out.shape}')  # validate the shape
    # create heap map
    cam = returnCAM(conv_out, weights, class_index)
    # resize: (width, height)
    cam = cv2.resize(cam, (ori_img.shape[1], ori_img.shape[0]))
    #print('Resized cam shape:', cam.shape)
    if visualize:
        heatmap = cv2.applyColorMap(cam, cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        result = heatmap * 0.5 + ori_img * 0.6
        plt.imshow(result / 255)
        plt.show()
        #cv2.imwrite('CAM.jpg', result)
    if return_cam:
        return cam
    

def returnCAM(feature_conv, weight_softmax, class_idx):
    # feature_conv : width * height * channel
    cam = feature_conv.dot(weight_softmax[:, class_idx])
    #Create the class activation map.
    #print('np min:', np.min(cam))
    cam = cam - np.min(cam)
    cam_img = cam / np.max(cam)
    cam_img = np.uint8(255 * cam_img)
    #output_cam = cv2.resize(cam_img, (256, 256))
    #print(f'output cam shape: {output_cam.shape}')
    return cam_img


def find_bounding_boxes(labeled, num_of_objects, shape=(256, 256)):
    max_h, max_w = shape
    rows, cols = labeled.shape
    
    bboxes = np.zeros([num_of_objects, 4])
    top, left, bottom, right = max_h, max_w, 0, 0
    
    for i in range(num_of_objects):
        bboxes[i] = left, top, right, bottom
    
    for r in range(rows):
        for c in range(cols):
            if (labeled[r][c] != 0):
                idx = labeled[r][c] - 1;
                # top
                if (r < bboxes[idx][1]):
                    bboxes[idx][1] = r
                # left
                if (c < bboxes[idx][0]):
                    bboxes[idx][0] = c
                # bottom
                if (r > bboxes[idx][3]):
                    bboxes[idx][3] = r
                # right
                if (c > bboxes[idx][2]):
                    bboxes[idx][2] = c
                    
    return bboxes.astype(int)


def compute_IoU(box_pred, box_gt):
    # comput the intersection area
    left = max(box_pred[0], box_gt[0])
    top = max(box_pred[1], box_gt[1])
    right = min(box_pred[2], box_gt[2])
    bottom = min(box_pred[3], box_gt[3])
    inter_area = max(0, right - left) * max(0, bottom - top)
    # comput the union area
    pred = (box_pred[2] - box_pred[0]) * (box_pred[3] - box_pred[1])
    gt = (box_gt[2] - box_gt[0]) * (box_gt[3] - box_gt[1])
    union = pred + gt - inter_area
    return inter_area / union



def compute_localisation_score(dataset_dir, bbox_info, model, preprocess_input, thresh, log=False, find_len=10):
    '''
    Compute the localisation performance of class activatio mapping.

    The performance is measured by the mean IoU.
    '''
    if log: # save some images for visualization
        good_index = []
        bad_index = []

    iou_results = []
    count = 0
    start = time.time()
    weights, conv_out_func = get_intermediate_results(model)

    for f in os.listdir(dataset_dir):
        img_path = os.path.join(dataset_dir, f)
        if (not os.path.isdir(img_path) and img_path.endswith('.jpg')):
            # get the ground truth
            img_index = int(f[:-4])
            gt_box = np.array(bbox_info.loc[img_index])
            if (gt_box.shape[0] != 4):
                # ignore the case where there are multiple gt boxes
                continue
            # get cam result
            cam = visualizeCAM(img_path, weights, conv_out_func, preprocess_input, 0, return_cam=True, visualize=False)
            # find connected components
            threshold = thresh * np.max(cam)
            labeled, num_of_objects = ndimage.label(cam > threshold) 
            bboxes = find_bounding_boxes(labeled, num_of_objects)
            # find the best predicted region
            temp = []
            max_iou = 0
            for box in bboxes:
                try:
                    iou = compute_IoU(box, gt_box)
                except:
                    print(img_index)
                    raise
                else:
                    if iou > max_iou:
                        max_iou = iou
            if log:
                if max_iou > 0.4:  # Assume predicted results with iou over 0.4 are good.
                    good_index.append(img_index)
                if max_iou < 0.2:  # Assume predicted results with iou lower than 0.2 are bad.
                    bad_index.append(img_index)
                temp.append(iou)
            iou = 0 if len(temp) == 0 else np.max(temp)
            iou_results.append(iou)
            count += 1
            if (log and len(good_index) > find_len and len(bad_index) > find_len):
                return good_index, bad_index
            if (count % 20 == 0):
                print('Count:', count)
                print('Average IoU: %.3f' % np.mean(iou_results))

    print('[Result] Average IoU: %.3f' % np.mean(iou_results))
    print('time elapsed: %.2f s' % (time.time() - start))

dataset_dir = 'drive/My Drive/MSc dataset/localisation-test/mixed'
info = "drive/My Drive/MSc dataset/localisation-test/mixed/bb_info.txt"
bbox_info = pd.read_csv(info, sep=" ", index_col=0)

# for t in np.arange(0.2, 0.29, 0.05):
#     print('\nThreshold: ', t)
#     compute_localisation_score(dataset_dir, bbox_info, model, resnet50.preprocess_input, thresh=t)

good_index, bad_index = compute_localisation_score(dataset_dir, bbox_info, model, resnet50.preprocess_input, thresh=0.5, log=True)

print(good_index)
print(bad_index)