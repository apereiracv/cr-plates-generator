import os
import plate
import context
import jsonutil

appContext = context.Context('configuration.cfg')
templates = jsonutil.deserializeJson('templates.json')
plate1 = plate.Plate(appContext, 'car-old', templates['car-old'])
plate2 = plate.Plate(appContext, 'car-new', templates['car-new'])
plate3 = plate.Plate(appContext, 'small-truck', templates['small-truck'])
plate4 = plate.Plate(appContext, 'taxi', templates['taxi'])

path = "./plates"
plate1.save_image(path)
plate2.save_image(path)
plate3.save_image(path)
plate4.save_image(path)
