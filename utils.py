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
import cv2
import random

def get_random_item(collection):
    """Returns a random item from a list or dict"""
    if isinstance(collection, list):
        index = random.randrange(len(collection))
        return collection[index]
    elif isinstance(collection, dict):
        index = random.randrange(len(collection.keys()))
        return list(collection.keys())[index]
    else:
        return None

def rescale_image(image, scale_factor):
    """Scales image by a scale factor i.e: 1.5"""
    interpol = cv2.INTER_CUBIC if scale_factor > 1 else cv2.INTER_AREA
    result = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=interpol)
    return result

    
def resize_image(image, size):
    """Resize image to a specific size [width, height]"""
    if size[0] < image.shape[1] or size[1] < image.shape[0]:
        interpol = cv2.INTER_AREA
    else:
        interpol = cv2.INTER_CUBIC
    result = cv2.resize(image, (size[0], size[1]), interpolation=interpol)
    return result