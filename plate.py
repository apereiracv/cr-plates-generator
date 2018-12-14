#!/usr/bin/python
import os
import cv2
import xeger
import PIL
import numpy

class Plate(object):
    """Represents a Plate and holds all its attributes"""

    def __init__(self, template, context):
        # Base attributes
        self.type = None
        self.plate_number = None
        self.image_data = None
        self.context = context

        self.__construct(template)


    def __construct(self, template):
        """Constructs plate based on template provided"""

        self.type = template["type"]
        image_path = os.path.join(self.context.get("General", "template_path"), self.type)
        self.image_data = PIL.Image.open(image_path)

        # Generate & draw plate number
        self.plate_number = self.draw_regex(template["plate-number"])

        # Draw extra text
        for extra_text in template["extra-text"]:
            self.draw_regex(extra_text)

        # Will use CV2 for the rest of image operations
        self.image_data = self.pil_to_cv2(self.image_data)


    def draw_regex(self, text_template):
        draw = PIL.ImageDraw.Draw(self.image_data)
        font_path = os.path.join(self.context.get("General", "templates_path"), text_template["font"])
        text_font = PIL.ImageFont.truetype(font_path, text_template["size"])
        text = xeger.xeger(text_template["regex"])
        draw.text(text_template["position"], text, font=text_font, fill=text_template["color"])

        return text


    def pil_to_cv2(self, image):
        return cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR) 