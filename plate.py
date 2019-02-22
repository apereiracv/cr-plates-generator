#!/usr/bin/python
import os
import cv2
import rstr
import PIL.Image, PIL.ImageFont, PIL.ImageDraw
import numpy
import random

class Plate(object):
    """Represents a Plate and holds all its attributes"""

    def __init__(self, context, type, template):
        """Constructor"""
        # Base attributes
        self.context = context
        self.type = type
        self.base_file = None
        self.plate_number = None
        self.image_data = None     

        self.__autogenerate(template)


    def __autogenerate(self, template):
        """Generates plate based on template provided"""
        # Open base image template 
        self.base_file = self.get_random_item(template["base-image"])
        image_path = os.path.join(self.context.getConfig("General", "templates_folder"), self.base_file)
        self.image_data = PIL.Image.open(image_path)

        # Generate & draw plate number
        plate_template = self.get_random_item(template["plate-number"])
        self.plate_number = self.draw_regex(plate_template)

        # Draw extra text, if any
        if "extra-text" in template.keys():
            for text_template in template["extra-text"]:
                self.draw_regex(text_template)

        # Will use CV2 for the rest of image operations
        self.image_data = self.pil_to_cv2(self.image_data)


    def draw_regex(self, text_template):
        """Draws text on plate image based on a template object"""
        draw = PIL.ImageDraw.Draw(self.image_data)
        font_path = os.path.join(self.context.getConfig("General", "templates_folder"), text_template["font"])
        text_font = PIL.ImageFont.truetype(font_path, text_template["size"])
        text = rstr.xeger(text_template["regex"])
        draw.text(text_template["position"], text, font=text_font, fill=text_template["color"])

        return text

    
    def save_image(self, path=None):
        """Saves plate image to disk"""
        savePath = path if path is not None else self.context.getConfig("General", "output_path")
        filename, ext = os.path.splitext(self.base_file)
        savePath = os.path.join(savePath, self.plate_number + ext)
        cv2.imwrite(savePath, self.image_data)


    def pil_to_cv2(self, image):
        return cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)



    # TODO: Move to utilities module
    def get_random_item(self, list):
        index = random.randrange(len(list))
        return list[index]
