# -*- coding: utf-8 -*-
"""Dataset preprocessing.ipynb

Automatically generated by Colaboratory.
"""

'''
Move the images to the corresponding folders.

Preprocessing for the use of Keras.
'''

"""## Food / Non-Food"""

train_path = "drive/My Drive/MSc dataset/food5k-subset/training"
eval_path = "drive/My Drive/MSc dataset/food5k-subset/validation"
test_path = "drive/My Drive/MSc dataset/food5k-subset/evaluation"

import shutil
import os


def preprocess_dataset(dir_path):
    # process
    for f in os.listdir(dir_path):
        img_path = os.path.join(dir_path, f)
        if (not os.path.isdir(img_path) and img_path.endswith('jpg')):
            if (f[0] == '0'):
                new_path = os.path.join(dir_path + "/non-food", f)
            elif (f[0] == '1'):
                new_path = os.path.join(dir_path + "/food", f)
            shutil.move(img_path, new_path)
    # validate operation
    count = 0
    for f in os.listdir(dir_path):
        img_path = os.path.join(dir_path, f)
        if (not os.path.isdir(img_path) and img_path.endswith('jpg')):
            count += 1
    assert count == 0
    print(f'preprocess_dataset "{dir_path}" done!')



preprocess_dataset(train_path)
preprocess_dataset(eval_path)
preprocess_dataset(test_path)

"""## Whole Food / Refined Food"""

#! unzip "drive/My Drive/MSc dataset/Food-11.zip" -d "drive/My Drive/MSc dataset/food11"

import shutil
import os


def preprocess_dataset(dir_path):
    # process
    for f in os.listdir(dir_path):
        img_path = os.path.join(dir_path, f)
        if (not os.path.isdir(img_path) and img_path.endswith('jpg')):
            if (f[0] in ['3', '5', '8', '9'] or f[:2] == '10'):
                new_path = os.path.join(dir_path + "/whole food", f)
            else:
                new_path = os.path.join(dir_path + "/refined food", f)
            shutil.move(img_path, new_path)
    # validate operation
    count = 0
    for f in os.listdir(dir_path):
        img_path = os.path.join(dir_path, f)
        if (not os.path.isdir(img_path) and img_path.endswith('jpg')):
            count += 1
    assert count == 0
    print(f'preprocess_dataset "{dir_path}" done!')
    
    
    
def correct_misplaced_img(dir_path):
    whole_food = dir_path + "/whole food"
    refined_food = dir_path + "/refined food"
    count = 0
    for f in os.listdir(refined_food):
        img_path = os.path.join(refined_food, f)
        if (not os.path.isdir(img_path) and img_path.endswith('jpg')):
            if (f[:2] == '10'):
                new_path = os.path.join(whole_food, f)
                shutil.move(img_path, new_path)
                count += 1
    print(f'{count} images corrected!')