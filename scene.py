#######################################################################
# Copyright (c) 2019 Alejandro Pereira

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>

#######################################################################
#!/usr/bin/python

import os
import cv2
import random
import copy
import ast

import utils


def get_random_bg(context):
    """Returns a random background image from configured path"""

    bg_path = context.getConfig('General', 'backgrounds_path')
    bg_list = os.listdir(bg_path)
    selected_bg = bg_list[random.randrange(len(bg_list))]
    bg_image = cv2.imread(os.path.join(bg_path, selected_bg))

    # Resize image according to the list of configured sizes
    sizes = ast.literal_eval(context.getConfig('Image', 'bg_sizes'))
    size = utils.get_random_item(sizes)
    bg_image = utils.resize_image(bg_image, size)

    # Add alpha channel to image if not present, this is to add foreground
    if bg_image.shape[2] == 3:
        bg_image = cv2.cvtColor(bg_image, cv2.COLOR_RGB2RGBA)
    
    return bg_image


def get_random_position(image_width, image_height, bg_width, bg_height):
    """Calculates a random position for an image inside another"""
    
    assert(bg_width > image_width)
    assert(bg_height > image_height)

    max_width = bg_width - image_width
    max_height = bg_height - image_height

    x1 = random.randrange(max_width)
    y1 = random.randrange(max_height)
    x2 = x1 + image_width
    y2 = y1 + image_height

    return x1, y1, x2, y2


def add_backgroud(image, bboxes, context):
    result_image = get_random_bg(context)
    x1, y1, x2, y2 = get_random_position(image.shape[1], image.shape[0], result_image.shape[1], result_image.shape[0])
    
    # Add images by alpha channel
    alpha_image = image[:, :, 3] / 255.0
    alpha_bg = 1.0 - alpha_image
    for channel in range(0, 3):
        result_image[y1:y2, x1:x2, channel] = (alpha_image * image[:, :, channel] + alpha_bg * result_image[y1:y2, x1:x2, channel])

    # Modify bounding boxes to match new position within the image
    result_bboxes = None
    if bboxes:
        result_bboxes = []
        for bbox in bboxes:
            new_bbox = copy.copy(bbox)
            new_bbox['cx'] += x1
            new_bbox['cy'] += y1
            result_bboxes.append(new_bbox)

    return result_image, result_bboxes


