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

# External imports
import os
import uuid
import cv2
import ast
# Internal imports
import scene
import utils

class Sample(object):
    """Represents a dataset sample image"""

    def __init__(self, context):
        self.context = context
        self.image_data = scene.get_random_bg(self.context)
        self.id = str(uuid.uuid4()).upper()
        self.objects = []

    #TODO: Might want to have an option to non-overlap objects
    def add_image_object(self, image_object):
        """Adds an object to the sample in a random position"""
        x1, y1, x2, y2 = scene.get_random_position(image_object.image_data.shape[1], image_object.image_data.shape[0], 
                                                    self.image_data.shape[1], self.image_data.shape[0])
        self.image_data = utils.add_image(image_object.image_data, (x1, y1, x2, y2), self.image_data)
        image_object.set_position((x1, y1, x2, y2))
        self.objects.append(image_object)


    def save_image(self, output_path):
        """Saves sample as image to disk"""
        save_path = os.path.join(output_path, self.get_filename())
        save_data = self.image_data
        # Eliminate alpha channel to optimize storage
        if save_data.shape[2] == 4:
            save_data = cv2.cvtColor(save_data, cv2.COLOR_RGBA2RGB)
        #TODO: Draw bounding boxes if needed
        #if self.context.getBoolean("Image", "draw_bboxes"):
        #    save_data = self.draw_all_bboxes()
        cv2.imwrite(save_path, save_data)

        return save_data


    def get_filename(self):
        return "{0}.jpg".format(self.id)


class ImageObject(object):
    """Represents a detectable object inside and image"""

    def __init__(self, label, image_data, context):
        """Constructor"""
        self.label = label
        self.image_data = self.random_rescale(image_data, context)
        self.position = None
        # Add alpha channel to loaded image
        if self.image_data.shape[2] == 3:
            self.image_data = cv2.cvtColor(self.image_data, cv2.COLOR_RGB2RGBA)
        
        

    #region Common methods
    def random_rescale(self, image_data, context):
        """Resize image object by a scale factor"""
        object_scales = ast.literal_eval(context.getConfig('Image', 'object_scales'))
        sizes = object_scales[type(self).__name__]
        return utils.random_rescale(image_data, sizes)


    def set_position(self, position):
        self.position = position
    
    #endregion

    #region Virtual methods
    def get_annotation(self):
        """Virtual function to get the object annotation"""
        raise NotImplementedError


    def auto_generate(self):
        """Virtual function to auto-generate an image object"""
        raise NotImplementedError

    #endregion

#TODO: Make configurable?
class StandardFormatMap():
    FILENAME = 'filename'
    XMIN = 'xmin'
    XMAX = 'xmax'
    YMIN = 'ymin'
    YMAX = 'ymax'
    LABEL = 'label'


class StandardObject(ImageObject):
    """Represents a standard image object with the most common attributes"""
    
    def __init__(self, annotation, context):
        label = annotation[StandardFormatMap.LABEL]
        image_data = self.auto_generate(annotation)
        super(StandardObject, self).__init__(label, image_data, context)


    #TODO: Image operations (cv2) may be extracted to utility
    def auto_generate(self, annotation):
        """Returns object image_data from standard annotation"""
        filename = annotation[StandardFormatMap.FILENAME]
        image_data = cv2.imread(filename) #TODO: Catch non-existing files
        # Get annotation bounding box
        xmin, ymin = int(annotation[StandardFormatMap.XMIN]), int(annotation[StandardFormatMap.YMIN])
        xmax, ymax = int(annotation[StandardFormatMap.XMAX]), int(annotation[StandardFormatMap.YMAX])
        # Get the exact frame of the object from bounding box
        image_data = image_data[ymin:ymax,xmin:xmax,:]

        return image_data
