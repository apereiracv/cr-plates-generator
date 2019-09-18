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
import copy
import pandas as pd
import sys
import csv

# TODO: We could have a generic factory
class AnnotatioReaderFactory(object):
    """Factory class for annotation readers"""

    @staticmethod
    def getReader(prefix):
        """Factory method to create annotation readers according to the prefix"""
        classSuffix = AnnotationReader.__name__
        readerClassName = "{}{}".format(prefix.upper(), classSuffix)
        reader = getattr(sys.modules[__name__], readerClassName)()
        return reader


class AnnotatioWriterFactory(object):
    """Factory class for annotation writers"""
    @staticmethod
    def getWriter(prefix):
        """Factory method to create annotation writers according to the prefix"""
        classSuffix = AnnotationWriter.__name__
        writerClassName = "{}{}".format(prefix.upper(), classSuffix)
        writer = getattr(sys.modules[__name__], writerClassName)()
        return writer


class AnnotationWriter(object):
    """Defines a generic annotation writer"""

    def __init__(self):
        self.annotations = None


    def get_annotation(self, plate):
        raise NotImplementedError()

    
    def save_annotations(self, output_path):
        raise NotImplementedError()


    def append_annotations(self, sample):
        new_anotation = self.get_annotation(sample)
        self.annotations.append(new_anotation)


class JSONAnnotationWriter(AnnotationWriter):
    """Reader implementation for original JSON format
        Bounding box format: cx, cy, w, h, angle
    """

    def __init__(self):
        self.plate_annotation = {'filename': None, 'class': None, 'bboxes': []}
        self.bbox_annotation = {'class': None, 'cx': None, 'cy': None, 'w': None, 'h': None, 'angle': 0}
        self.annotations = []
        self.extension = "json"
        super(JSONAnnotationWriter, self).__init__()


    def get_annotation(self, plate):
        annotation = copy.copy(self.plate_annotation)
        annotation['filename'] = plate.get_filename()
        annotation['class'] = plate.type

        for bbox in plate.bounding_boxes:
            annotation['bboxes'].append(copy.copy(bbox))

        return annotation


    def save_annotations(self, output_path):
        with open(output_path, 'w') as f:
            f.write(str(self.annotations))


class TFAnnotationWriter(AnnotationWriter):
    """Writer implementation for Tensorflow .csv format
        Format: filename, img_width, img_height, class, xmin, ymin, xmax, ymax
    """
       
    def __init__(self):
        super(TFAnnotationWriter, self).__init__()
        self.columns = ['filename', 'width', 'height',
                        'class', 'xmin', 'ymin', 'xmax', 'ymax']
        self.annotations = []
        self.extension = "csv"


    def get_annotation(self, plate):
        plate_bbox = plate.bounding_boxes[-1] # Last bbox is plate bbox
        annotation = (
            plate.get_filename(), # filename
            plate.image_data.shape[1], # width
            plate.image_data.shape[0], # height
            plate.type, # class
            plate_bbox['cx'] - (plate_bbox['w'] / 2), # xmin
            plate_bbox['cy'] - (plate_bbox['h'] / 2), # ymin
            plate_bbox['cx'] + (plate_bbox['w'] / 2), # xmax
            plate_bbox['cy'] + (plate_bbox['h'] / 2) # ymax
        )

        return annotation

    
    def save_annotations(self, output_path):
        dataframe = pd.DataFrame(self.annotations, columns=self.columns)
        output_file = os.path.join(output_path, "annotations.{0}".format(self.extension))
        dataframe.to_csv(output_file, index=None)



class AnnotationReader(object):
    """Defines a generic annotation reader"""

    def __init__(self):
        self.annotations = None
        self.current = 0

    #region Virtual methods
    def read_annotations(self, file_path):
        raise NotImplementedError()

    #endregion

    #region Concrete methods
    def __next__(self):
        """Self iterable function"""
        result = None
        if not self.annotations:
            raise StopIteration
        elif self.current >= len(self.annotations):
            self.current = 0
            result = self.annotations[self.current]
        else:
            result = self.annotations[self.current]
            self.current += 1
        
        return result


        def __iter__(self):
            return self
    #endregion


class CSVAnnotationReader(AnnotationReader):
    """Reader implementation for stanford car dataset .csv format
        Format: filename, xmin, ymin, xmax, ymax, class
    """
    def __init__(self):
        self.format_map = ['filename', 'xmin', 'ymin', 'xmax', 'ymax', 'label'] 
        super(CSVAnnotationReader, self).__init__()


    #TODO: Extract full filename
    def read_annotations(self, file_path):
        """Reads annotations into dictionary with format_map as keys"""
        data = []
        with open(file_path) as csvFile:
            data = csv.reader(csvFile, delimiter=',')
            # Each row will be {filename: "filename.jpg", 'xmin': xmin, 'ymin': ymin, ...}
            self.annotations = [{self.format_map[i]:value for i, value in enumerate(row)} for row in data]
        
        # Add full path to all filenames
        dataset_path = os.path.dirname(file_path)
        for annotation in self.annotations:
            annotation['filename'] = os.path.join(dataset_path, annotation['filename'])

