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
import glob

import plate
import context
import jsonutil
import perspective
import scene
import utils
import annotations


if __name__ == "__main__":
    # Initialize settings
    appContext = context.Context('configuration.cfg')
    templates = jsonutil.deserializeJson('templates.json')

    dataset_size = int(appContext.getConfig('General', 'dataset_size'))
    output_path = appContext.getConfig('General', 'output_path')
    annotator_type = appContext.getConfig('General', 'annotation_type')
    annotator = annotations.AnnotatorFactory.get_annotator(annotator_type)
    
    # Create output directory or clean it
    clear_output = appContext.getBoolean('General', 'clear_output')
    if not os.path.exists(output_path): 
        os.makedirs(output_path)
    elif clear_output:
        files = glob.glob(os.path.join(output_path, '*'))
        for f in files:
            os.remove(f)

    
    for i in range(dataset_size):
        # Generate from random template
        plate_type = utils.get_random_item(templates)
        new_plate = plate.Plate(appContext, plate_type, templates[plate_type])
    
        # Change perspective, size and background
        new_plate.random_resize()
        new_plate.image_data, new_plate.bounding_boxes = perspective.warp_image_random(new_plate.image_data, new_plate.bounding_boxes, appContext)
        new_plate.image_data, new_plate.bounding_boxes = scene.add_backgroud(new_plate.image_data, new_plate.bounding_boxes, appContext)

        # Generate annotation and image file
        annotator.append_annotation(new_plate)
        new_plate.save_image(output_path)

    # Save annotations
    annotator.save_annotations(output_path)

