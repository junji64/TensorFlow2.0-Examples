#! /usr/bin/env python
# coding=utf-8
#================================================================
#   Copyright (C) 2019 * Ltd. All rights reserved.
#
#   Editor      : VIM
#   File name   : test.py
#   Author      : YunYang1994
#   Created date: 2019-10-19 17:21:54
#   Description :
#
#================================================================

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image
from rpn import RPNplus

def compute_ious(boxes1, boxes2):
    """(xmin, ymin, xmax, ymax)
    boxes1 shape:  [-1, 4], boxes2 shape: [-1, 4]
    """
    left_up = np.maximum(boxes1[..., :2], boxes2[..., :2], )
    right_down = np.minimum(boxes1[..., 2:], boxes2[..., 2:])
    inter_wh = np.maximum(right_down - left_up, 0.0)
    inter_area = inter_wh[..., 0] * inter_wh[..., 1]

    boxes1_area = (boxes1[..., 2] - boxes1[..., 0]) * (boxes1[..., 3] - boxes1[..., 1])
    boxes2_area = (boxes2[..., 2] - boxes2[..., 0]) * (boxes2[..., 3] - boxes2[..., 1])

    union_area = boxes1_area + boxes2_area - inter_area
    ious = inter_area / union_area
    return ious

def plot_boxes_on_image(show_image_with_boxes, boxes, color=[0, 0, 255], thickness=2):
    for box in boxes:
        cv2.rectangle(show_image_with_boxes,
                pt1=(int(box[0]), int(box[1])),
                pt2=(int(box[2]), int(box[3])), color=color, thickness=thickness)
    show_image_with_boxes = cv2.cvtColor(show_image_with_boxes, cv2.COLOR_BGR2RGB)
    return

wandhG = [[ 74., 149.],
          [ 34., 149.],
          [ 86.,  74.],
          [109., 132.],
          [172., 183.],
          [103., 229.],
          [149.,  91.],
          [ 51., 132.],
          [ 57., 200.]]
iou_thresh = 0.5
wandhG = np.array(wandhG)

image_path = "/Users/yangyun/synthetic_dataset/image/1.jpg"
raw_image = cv2.imread(image_path)
input_image = np.expand_dims(raw_image, 0) / 255.

model = RPNplus()
score, boxes = model(input_image)

# def decode(score, boxes):
score = tf.nn.softmax(score)
score = tf.reshape(score, shape=[45, 60, 9, 2]).numpy()
boxes = tf.reshape(boxes, shape=[45, 60, 9, 4]).numpy()
pred_boxes = np.zeros(shape=[45, 60, 9, 4])

for i in range(45):
    for j in range(60):
        for k in range(9):
            center_x = j * 16 + 8
            center_y = i * 16 + 8

            pred_x = boxes[i, j, k, 0] * wandhG[k, 0] + center_x
            pred_y = boxes[i, j, k, 1] * wandhG[k, 1] + center_y
            pred_w = tf.exp(boxes[i, j, k, 2]) * wandhG[k, 0]
            pred_h = tf.exp(boxes[i, j, k, 3]) * wandhG[k, 1]
            xmin = pred_x - 0.5 * pred_w
            ymin = pred_y - 0.5 * pred_h
            xmax = pred_x + 0.5 * pred_w
            ymax = pred_y + 0.5 * pred_h
            pred_boxes[i, j, k] = np.array([xmin, ymin, xmax, ymax])

pred_mask = np.argmax(score, axis=-1).astype(np.bool)
pred_boxes = pred_boxes[pred_mask].reshape(-1, 4)
pred_score = score[..., 1][pred_mask].reshape(-1,)

selected_boxes = []
while len(pred_boxes) > 0:
    max_idx = np.argmax(pred_score)
    selected_box = pred_boxes[max_idx]
    selected_boxes.append(selected_box)
    pred_boxes = np.concatenate([pred_boxes[:max_idx], pred_boxes[max_idx+1:]])
    pred_score = np.concatenate([pred_score[:max_idx], pred_score[max_idx+1:]])
    ious = compute_ious(selected_box, pred_boxes)
    iou_mask = ious > iou_thresh
    pred_boxes = pred_boxes[iou_mask]
    pred_score = pred_score[iou_mask]

selected_boxes = np.array(selected_boxes)
plot_boxes_on_image(raw_image, selected_boxes)
Image.fromarray(raw_image).show()




