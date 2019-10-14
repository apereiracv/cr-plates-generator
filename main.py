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
import glob

# Internal imports
import plate
import context
import jsonutil
import annotations
import sample

def clear_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        files = glob.glob(os.path.join(path, '*'))
        for f in files:
            os.remove(f)


def create_vehicle_plate_dataset(appContext, templates):
    dataset_size = int(appContext.getConfig('General', 'dataset_size'))
    output_path = appContext.getConfig('General', 'output_path')
    car_annotations_path = appContext.getConfig('General', 'car_annotations_path')
    annotation_writer_type = appContext.getConfig('General', 'annotation_writer_type')
    annotation_reader_type = appContext.getConfig('General', 'annotation_reader_type')
    annotationWriter = annotations.AnnotatioWriterFactory.getWriter(annotation_writer_type)
    annotationReader = annotations.AnnotatioReaderFactory.getReader(annotation_reader_type)

    # Create output directory or clean it
    clear_output = appContext.getBoolean('General', 'clear_output')
    if clear_output:
        clear_directory(output_path)

    # Read car annotations
    annotationReader.read_annotations(car_annotations_path)

    for i in range(dataset_size):
        # Instantiate a sample with random bg
        new_sample = sample.Sample(appContext, True)
        # Add random plate and car objects
        # TODO: template = annotation (logically)
        new_car = sample.StandardObject(next(annotationReader), appContext)
        new_car.random_rescale_relative(new_sample.image_data, appContext)
        new_plate = plate.PlateObject(templates, appContext)
        new_plate.random_rescale_relative(new_sample.image_data, appContext)
        new_sample.add_image_object(new_car)
        new_sample.add_image_object(new_plate)

        # Generate annotation and image file
        annotationWriter.append_annotations(new_sample)
        new_sample.save_image(output_path)
        # time.sleep(0.5) # TODO: Find solution for random images that are not written to disk

    # Save annotations
    annotationWriter.save_annotations(output_path)


def create_plate_text_dataset(appContext, templates):
    dataset_size = int(appContext.getConfig('General', 'dataset_size'))
    output_path = appContext.getConfig('General', 'output_path')
    annotation_writer_type = appContext.getConfig('General', 'annotation_writer_type')
    annotationWriter = annotations.AnnotatioWriterFactory.getWriter(annotation_writer_type)

    # Create output directory or clean it
    clear_output = appContext.getBoolean('General', 'clear_output')
    if clear_output:
        clear_directory(output_path)

    for i in range(dataset_size):
        # Instantiate a sample without background image
        new_sample = sample.Sample(appContext, False)
        # Add random plate and character objects
        new_plate = plate.PlateObject(templates, appContext)
        character_objects = new_plate.get_characters_as_image_objects()
        new_sample.image_data = new_plate.image_data
        new_sample.objects.extend(character_objects)

        # Generate annotation and image file
        annotationWriter.append_annotations(new_sample)
        new_sample.save_image(output_path)
        # time.sleep(0.5) # TODO: Find solution for random images that are not written to disk

    # Save annotations
    annotationWriter.save_annotations(output_path)


if __name__ == "__main__":
    # Initialize settings
    appContext = context.Context('configuration.cfg')
    templates = jsonutil.deserializeJson('templates.json')

    dataset_type = appContext.getConfig('General', 'dataset_type')

    if dataset_type == 'vehicle-plate':
        create_vehicle_plate_dataset(appContext, templates)
    elif dataset_type == 'plate-text':
        create_plate_text_dataset(appContext, templates)
