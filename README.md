# cr-plates-generator
Costa Rica license plate generator for computer vision

### Features
  - Plate formats: car, motorcycle, trucks, taxi, disabled drivers.
  - Perspective rotations, size and random backgrounds.
  - Annotations with character bounding boxes (class, cx, cy, w, h)
  - ```configuration.cfg``` and ```templates.json``` files for customization.
  
### Examples
[Pending]

## Getting Started
### Prerequisites
 - Python >= 3.6.0
 - Modules on *requirements.txt*
 ```pip3 install -r requirements.txt```

### Running sample code
 1. Add some images to *./backgrounds* directory, these will work as random backgrounds for the plates. [SUN Database](https://vision.princeton.edu/projects/2010/SUN/) is recommended.
 
 2. Run the main file
 ```python ./main.py``` 
3. Random plates will be generated on *./output* directory

## Settings
### ```configuration.cfg```
The following is a description of all the settings on this file.

|Setting|Description|Value
|--|--|--|
|**[General]**|||
| dataset_size | Quantity of images to generate | int|
| templates_path | Path to directory containing base plate images | string|
| templates_config | Path to JSON configuration for each type of plate | string|
|**[Image]**|||
| resize_plate| Apply resizing to the base plate images setting | bool|
| plate_scales| List of scaling factors to be used | list|
| resize_bg| Apply resizing to background images to a fixed size | bool|
| image_sizes| List of target (width,height) pairs to resize bgs| list|
| draw_bboxes| Whether to draw bounding boxes (Use for testing only)| bool|
| bbox_padding| Spacing between bbox and inner object (px)| int|
|**[Perspective]**|||
| theta_range|Maximum angle (degrees) to rotate plate over z-plane | float|
| phi_range| Maximum angle (degrees) to rotate plate over y-plane | float|
| gamma_range| Maximum angle (degrees) to rotate plate over x-plane | float|


### ```templates.cfg```
[Pending]

## Authors
* **Alejandro Pereira** - [Home Page](https://github.com/alejopc03)

## License
This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE.md](https://github.com/alejopc03/cr-plates-generator/blob/master/LICENSE) file for details

## References

 - Perspective transformations: https://nbviewer.jupyter.org/github/manisoftwartist/perspectiveproj/blob/master/perspective.ipynb
 - Another plate generator: https://matthewearl.github.io/2016/05/06/cnn-anpr/
 - SUN Database: [https://vision.princeton.edu/projects/2010/SUN/](https://vision.princeton.edu/projects/2010/SUN/)
