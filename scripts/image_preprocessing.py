import base64
import json
import mimetypes
import os
import sys
from collections import defaultdict
import argparse
import cv2
import numpy as np

# Enter root path
root_path = "../"

parser = argparse.ArgumentParser(description='Prepare uniform directory structure')
parser.add_argument('-fp', '--folder_path', help='The path of folder_path', required=True)
args = vars(parser.parse_args())
# folder_path = 'datastore/QP_Odisha NTSE Stage 1 2017-18) MAT'

# folder paths needed
folder_path =os.path.join('datastore',args['folder_path'])
ss_folder_path = os.path.join(root_path,folder_path,'screenshots')
new_ss_folder_path = os.path.join(root_path,folder_path,'merged_screenshots')

if not os.path.isdir(new_ss_folder_path):
    os.makedirs(new_ss_folder_path, exist_ok=True)


image_dict = defaultdict(list)
for q_img in os.listdir(ss_folder_path):
    parsed_filename = q_img.split('_')
    qc_no = parsed_filename[0]
    c_no = ''
    key = qc_no + '.png'
    if len(parsed_filename) > 2 : #context present
        c_no = parsed_filename[-1]
        key = qc_no + '_' + c_no
    key = key.replace('.png.png','.png')
    image_dict[key].append(q_img)

# final_image_dict = dict()
for key,img_list in image_dict.items() :
    images = []
    #read images
    for img_path in sorted(img_list) :
        img = cv2.imread(ss_folder_path + '/' + img_path)
        images.append(img)
        
    # Find the maximum width among all images
    max_width = max(image.shape[1] for image in images)
    
    # Pad images to have the same width
    padded_images = []
    for image in images:
        height, width, _ = image.shape
        pad_width = max_width - width
        # Pad the image on the right side
        padded_image = np.pad(image, ((0, 0), (0, pad_width), (0, 0)), constant_values=255)
        padded_images.append(padded_image)
    merged_img = np.concatenate(padded_images, axis=0)
    cv2.imwrite(os.path.join(new_ss_folder_path,key), merged_img)