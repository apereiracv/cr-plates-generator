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
import ast
import copy
import cv2
import rstr
import numpy as np
import PIL.Image, PIL.ImageFont, PIL.ImageDraw

# Internal imports
import perspective
import utils
import sample

RGB_GREEN = (0, 255, 0)
RGBA_GREEN = (0, 255, 0, 0)
PLATE_ANNOTATION = {'filename': None, 'class': None, 'bboxes': []}
BBOX_ANNOTATION = {'class': None, 'cx': None, 'cy': None, 'w': None, 'h': None, 'angle': 0}
SPECIAL_CHARS = ['-']


class PlateObject(sample.ImageObject):
    """Represents a Plate and holds all its attributes"""

    def __init__(self, templates, context):
        """Constructor"""
        # Base attributes
        self.plate_number = None
        self.bounding_boxes = None #TODO: these will be characters only
        self.image_data = None
        self.context = context #TODO: Is this needed?
        
        image_data = self.auto_generate(templates, context)
        super(PlateObject, self).__init__(self.label, image_data, context)


    def auto_generate(self, templates, context):
        """Generates plate based on template provided"""
        self.label = utils.get_random_item(templates)
        template = templates[self.label]

        # Open base image template 
        base_file = utils.get_random_item(template["base-image"])
        image_path = os.path.join(self.context.getConfig("General", "templates_path"), base_file)
        image_data = PIL.Image.open(image_path)

        # Generate & draw plate number
        plate_template = utils.get_random_item(template["plate-number"])
        image_data, self.plate_number, self.bounding_boxes = self.draw_regex(plate_template, image_data)

        # Draw extra text, if any
        if "extra-text" in template.keys():
            for text_template in template["extra-text"]:
                image_data, _ , _ = self.draw_regex(text_template, image_data)

        # Will use CV2 for the rest of image operations
        image_data = self.pil_to_cv2(image_data)

        # Do random perspective transform
        warp_perspective = context.getBoolean('Perspective', 'warp_perspective')
        if warp_perspective:
            image_data, self.bounding_boxes = perspective.warp_image_random(image_data, self.bounding_boxes, context)

        return image_data


    def draw_regex(self, text_template, image_data):
        """Draws text on plate image based on a template object"""
        draw = PIL.ImageDraw.Draw(image_data)
        font_path = os.path.join(self.context.getConfig("General", "templates_path"), text_template["font"])
        text_font = PIL.ImageFont.truetype(font_path, text_template["size"])
        text = rstr.xeger(text_template["regex"])
        ascent, descent = text_font.getmetrics()
        # Draw each character and calculate its bounding box
        bbox_padding = ast.literal_eval(self.context.getConfig("Image", "bbox_padding"))
        bounding_boxes = []
        last_pos_x = 0
        for char in text:
            (width, baseline), (offset_x, offset_y) = text_font.font.getsize(char)
            height = ascent - offset_y # Some fonts can contain an offset in height (accounted for ascent)
            char_pos_x = text_template["position"][0] + last_pos_x
            char_pos_y = text_template["position"][1]
            if char == '-': # Dash character is offsetted further
                char_pos_x += offset_x / 2
                char_pos_y += offset_y / 2
            # Draw character in desired position
            draw.text((char_pos_x - offset_x, char_pos_y - offset_y), char, font=text_font, fill=text_template["color"])
            new_bbox = copy.copy(BBOX_ANNOTATION)
            x1 = (char_pos_x - bbox_padding[0])
            y1 = (char_pos_y - bbox_padding[1])
            x2 = (char_pos_x + width + bbox_padding[0])
            y2 = (char_pos_y + height + bbox_padding[1])
            # Don't add dash as a "detectable" character
            if char != '-':
                new_bbox['class'] = char
                new_bbox['cx'], new_bbox['cy'], new_bbox['w'], new_bbox['h'] = perspective.coords_to_bbox([x1,y1,x2,y2])
                bounding_boxes.append(new_bbox)
            last_pos_x = last_pos_x + width + text_template["spacing"]

        return image_data, text, bounding_boxes


    def draw_all_bboxes(self):
        """Returns image_data with drawn bounding boxes of plate & characters"""
        assert(len(self.bounding_boxes) > 0)

        result_image = copy.copy(self.image_data)
        for bbox in self.bounding_boxes:
            self.draw_bbox(result_image, bbox)

        return result_image


    def draw_bbox(self, image, bbox):
        """Draws a single bbox"""
        # TODO: This function should be moved elsewhere
        vertices = perspective.get_bbox_vertices(bbox)
        pts = np.array([vertices], np.int32)
        cv2.polylines(image, [pts], True, self.get_color(), 2)


    def random_rescale(self):
        plate_scales = ast.literal_eval(self.context.getConfig('Image', 'plate_scales'))
        scale_factor = utils.get_random_item(plate_scales)
        self.rescale_image(scale_factor)


    def rescale_image(self, scale_factor):
        """Scale plate image by a scale factor"""
        interpol = cv2.INTER_CUBIC if scale_factor > 1 else cv2.INTER_AREA
        self.image_data = cv2.resize(self.image_data, None, fx=scale_factor, fy=scale_factor, interpolation=interpol)
        self.rescale_bboxes(scale_factor)


    def resize_image(self, new_width):
        scale_factor = new_width / self.image_data.shape[1]
        self.rescale_image(scale_factor)


    def pad_image(self, size):
        """Pads plate image to a specific size [width, height]"""
        assert size[0] >= self.image_data.shape[1] and size[1] >= self.image_data.shape[0]
        delta_w = size[0] - self.image_data.shape[1]
        delta_h = size[1] - self.image_data.shape[0]
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)
        color = (0, 0, 0)
        self.image_data = cv2.copyMakeBorder(self.image_data, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        self.pad_bboxes(top, left)


    def pad_bboxes(self, top, left):
        """Re-calculates bounding boxes according to a top/left padding"""
        for bbox in self.bounding_boxes:
            bbox['cx'] = bbox['cx'] + left
            bbox['cy'] = bbox['cy'] + top


    def rescale_bboxes(self, scale_factor):
        """Re-calculates bounding boxes according to a scale factor"""
        for bbox in self.bounding_boxes:
            bbox['cx'] = bbox['cx'] * scale_factor
            bbox['cy'] = bbox['cy'] * scale_factor
            bbox['w'] = bbox['w'] * scale_factor
            bbox['h'] = bbox['h'] * scale_factor


    # def save_image(self, path=None):
    #     """Saves plate image to disk"""
    #     savePath = path if path is not None else self.context.getConfig("General", "output_path")
    #     savePath = os.path.join(savePath, self.get_filename())
    #     savePath = savePath.lower()
    #     save_data = self.image_data
    #     # Eliminate alpha channel to optimize storage
    #     if save_data.shape[2] == 4:
    #         save_data = cv2.cvtColor(save_data, cv2.COLOR_RGBA2RGB)
    #     # Draw bounding boxes if needed
    #     if self.context.getBoolean("Image", "draw_bboxes"):
    #         save_data = self.draw_all_bboxes()

    #     cv2.imwrite(savePath, save_data)
    #     return savePath


    def get_characters_as_image_objects(self):
        """Returns a list of ImageObjects representing each character in the plate"""
        characterObjects = []
        for bbox in self.bounding_boxes:
            xmin, ymin, xmax, ymax = perspective.bbox_to_coords(bbox)
            annotation = {sample.StandardFormatMap.FILENAME: '',
                          sample.StandardFormatMap.LABEL: bbox['class'],
                          sample.StandardFormatMap.XMIN: xmin,
                          sample.StandardFormatMap.YMIN: ymin,
                          sample.StandardFormatMap.XMAX: xmax,
                          sample.StandardFormatMap.YMAX: ymax}
            characterObject = sample.StandardObject(annotation, self.context)
            characterObject.position = (xmin, ymin, xmax, ymax)
            characterObjects.append(characterObject)

        return characterObjects


#region Utility functions
    def pil_to_cv2(self, image):
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


    def get_color(self):
        if self.image_data.shape[2] == 3:
            return RGB_GREEN
        else:
            return RGBA_GREEN


    def get_filename(self):
        return "{0}_{1}.jpg".format(self.label, self.plate_number)
#endregion