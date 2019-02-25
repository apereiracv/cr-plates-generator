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

import plate
import context
import jsonutil
import perspective
import scene

appContext = context.Context('configuration.cfg')
templates = jsonutil.deserializeJson('templates.json')
plate1 = plate.Plate(appContext, 'car-old', templates['car-old'])
plate2 = plate.Plate(appContext, 'car-new', templates['car-new'])
plate3 = plate.Plate(appContext, 'small-truck', templates['small-truck'])
plate4 = plate.Plate(appContext, 'taxi', templates['taxi'])

plate1.image_data = perspective.warp_image_random(plate1.image_data, appContext)
plate1.image_data = scene.add_backgroud(plate1.image_data, appContext)

ouput_path = appContext.getConfig('General', 'output_path')
plate1.save_image(ouput_path)
# plate2.save_image(path)
# plate3.save_image(path)
# plate4.save_image(path)
