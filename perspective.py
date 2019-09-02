# Code adapted from: https://nbviewer.jupyter.org/github/manisoftwartist/perspectiveproj/blob/master/perspective.ipynb

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

import math
import random
import copy
import ast
from functools import reduce

import numpy as np
import cv2

def get_rotation_matrix(rotation_angles):
    
    rotation_angles = list(map(lambda x : np.deg2rad(x), rotation_angles))
    
    phi = rotation_angles[0] # around x
    gamma = rotation_angles[1] # around y
    theta = rotation_angles[2] # around z
    
    # X rotation matrix
    rot_matrix_phi = np.eye(4,4)
    sp = np.sin(phi)
    cp = np.cos(phi)
    rot_matrix_phi[1,1] = cp
    rot_matrix_phi[2,2] = rot_matrix_phi[1,1]
    rot_matrix_phi[1,2] = -sp
    rot_matrix_phi[2,1] = sp
    
    # Y rotation matrix
    rot_matrix_gamma = np.eye(4,4)
    sg = np.sin(gamma)
    cg = np.cos(gamma)
    rot_matrix_gamma[0,0] = cg
    rot_matrix_gamma[2,2] = rot_matrix_gamma[0,0]
    rot_matrix_gamma[0,2] = sg
    rot_matrix_gamma[2,0] = -sg
    
    # Z rotation matrix (in-image-plane)
    rot_matrix_theta = np.eye(4,4)
    st = np.sin(theta)
    ct = np.cos(theta)
    rot_matrix_theta[0,0] = ct
    rot_matrix_theta[1,1] = rot_matrix_theta[0,0]
    rot_matrix_theta[0,1] = -st
    rot_matrix_theta[1,0] = st
    
    rotation_matrix = reduce(lambda x,y : np.matmul(x,y), [rot_matrix_phi, rot_matrix_gamma, rot_matrix_theta]) 
    
    return rotation_matrix


def get_perspective_transform_estimation(pts_in, pts_out, width, height, side_length):
    pts_in_2D = pts_in[0,:]
    pts_out_2D = pts_out[0,:]

    pts_out_2D_list = []
    pts_in_2D_list = []
    for i in range(0,4): # TODO: use len
        pts_out_2D_list.append([pts_out_2D[i,0], pts_out_2D[i,1]])
        pts_in_2D_list.append([pts_in_2D[i,0], pts_in_2D[i,1]])
    
    pin  =  np.array(pts_in_2D_list) + [width/2., height/2.]
    pout = (np.array(pts_out_2D_list) + [1., 1.]) * (0.5*side_length)
    pin  = pin.astype(np.float32)
    pout = pout.astype(np.float32)
    
    return pin, pout


def get_warp_matrix(width, height, theta, phi, gamma, scale, field_vision):
    
    fv_half = np.deg2rad(field_vision / 2.)
    d = np.sqrt(width*width + height*height)
    side_length = scale * (d / np.cos(fv_half))
    h = d / (2.0*np.sin(fv_half))
    n = h - (d/2.0)
    f = h + (d/2.0)
    
    # Translation along Z-axis by -h
    T = np.eye(4,4)
    T[2,3] = -h
    
    # Rotation matrices around x,y,z
    rotation_matrix = get_rotation_matrix([phi, gamma, theta])
    
    # Projection Matrix 
    P = np.eye(4,4)
    P[0,0] = 1.0/np.tan(fv_half)
    P[1,1] = P[0,0]
    P[2,2] = -(f+n)/(f-n)
    P[2,3] = -(2.0*f*n)/(f-n)
    P[3,2] = -1.0
    
    # pythonic matrix multiplication
    F = reduce(lambda x,y : np.matmul(x,y), [P, T, rotation_matrix]) 
    
    # shape should be 1,4,3 for ptsIn and ptsOut since perspectiveTransform() expects data in this way. 
    # In C++, this can be achieved by Mat ptsIn(1,4,CV_64FC3);
    pts_in = np.array([[
                 [-width/2., height/2., 0.],[ width/2., height/2., 0.],[ width/2.,-height/2., 0.],[-width/2.,-height/2., 0.]
                 ]])
    pts_out  = np.array(np.zeros((pts_in.shape), dtype=pts_in.dtype))
    pts_out  = cv2.perspectiveTransform(pts_in, F)
    
    pts_in_pt2f, pts_out_pt2f = get_perspective_transform_estimation(pts_in, pts_out, width, height, side_length)
    
    # check float32 otherwise OpenCV throws an error
    assert(pts_in_pt2f.dtype  == np.float32)
    assert(pts_out_pt2f.dtype == np.float32)
    M33 = cv2.getPerspectiveTransform(pts_in_pt2f, pts_out_pt2f)

    return M33, int(side_length)


def get_random_angles(theta_range, phi_range, gamma_range, step):
    theta = random.randrange(theta_range[0], theta_range[1], step)
    phi = random.randrange(phi_range[0], phi_range[1], step)
    gamma = random.randrange(gamma_range[0], gamma_range[1], step)

    return (theta, phi, gamma)


def cut_warped_image(warped_image, source_width, source_height, matrix):
    """Returns a cropped version of the image, containing the minimum size required to contain the image"""
    # Find coordinates position of warped image
    image_coords = np.array([[
                    [0,0], 
                    [source_width, 0], 
                    [0, source_height], 
                    [source_width, source_height]]], dtype='float32')

    warped_coords = cv2.perspectiveTransform(image_coords, matrix)[0]

    # Find the minimum rect bouding box that fits the warped image. p = [x, y]
    p1 = np.min(warped_coords, axis=0).astype(int)
    p2 = np.max(warped_coords, axis=0).astype(int)
    
    # Crop image
    result = warped_image[p1[1]:p2[1], p1[0]:p2[0]]

    return result, [p1, p2]


def warp_bboxes(bboxes, matrix, crop_points=None, rotate_bboxes=False):
    """Re-calculates new bounding boxes based on transformation matrix used for an image"""
    warped_bboxes = []
    for bbox in bboxes:
        bbox_coords = bbox_to_coords(bbox)
        bbox_points = np.array([[
            [bbox_coords[0], bbox_coords[1]],
            [bbox_coords[2], bbox_coords[1]],
            [bbox_coords[0], bbox_coords[3]],
            [bbox_coords[2], bbox_coords[3]]
        ]], dtype='float32')

        # Find the new rectangle bbox that fits the warped bbox
        warped_coords = cv2.perspectiveTransform(bbox_points, matrix)[0]
        new_bbox = copy.copy(bbox)
        if rotate_bboxes:
            # minAreaRect = (cx,cy),(w,h),angle
            bbox_rect = cv2.minAreaRect(warped_coords)
            new_bbox['cx'], new_bbox['cy'] = bbox_rect[0][0], bbox_rect[0][1]
            new_bbox['w'], new_bbox['h'] = bbox_rect[1][0], bbox_rect[1][1]
            new_bbox['angle'] = bbox_rect[2]
        else:
            # boundingRect = (x1,y1),(w,h)
            bbox_rect = cv2.boundingRect(warped_coords)
            new_bbox['w'], new_bbox['h'] = bbox_rect[2], bbox_rect[3]
            # cx = x1 + w/2, cy = x2 + h/2
            new_bbox['cx'], new_bbox['cy'] = bbox_rect[0] + (bbox_rect[2]/2), bbox_rect[1] + (bbox_rect[3]/2)
            new_bbox['angle'] = 0
        
        # Apply cropping to bbox if points provided
        if crop_points:
            new_bbox['cx'] -= crop_points[0][0]
            new_bbox['cy'] -= crop_points[0][1]
        
        warped_bboxes.append(new_bbox)

    return warped_bboxes


def warp_image(image, theta, phi, gamma, scale, fovy, bboxes=None, rotate_bboxes=False):
    """Changes the perspective of an image according to x,y,z angles"""
    height, width, _ = image.shape
    matrix, side_length = get_warp_matrix(width, height, theta, phi, gamma, scale, fovy) # Compute warp matrix
    transparent_bg = (0,0,0,0)
    result_image = image
    if image.shape[2] == 3:
        result_image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)
    result_image = cv2.warpPerspective(result_image, matrix, (side_length, side_length), borderValue=transparent_bg) # Do actual image warp
    result_image, crop_points = cut_warped_image(result_image, image.shape[1], image.shape[0], matrix)
    result_bboxes = None
    if bboxes: 
        result_bboxes = warp_bboxes(bboxes, matrix, crop_points=crop_points, rotate_bboxes=rotate_bboxes)

    return result_image, result_bboxes


def warp_image_random(image, bboxes, context):
    """Changes the perspective viewing angles of an image by a random number"""
    theta_range = ast.literal_eval(context.getConfig("Perspective", "theta_range"))
    phi_range   = ast.literal_eval(context.getConfig("Perspective", "phi_range"))
    gamma_range = ast.literal_eval(context.getConfig("Perspective", "gamma_range"))
    step = int(context.getConfig("Perspective", "rotation_step"))
    fov = int(context.getConfig("Perspective", "field_of_view"))
    scale = float(context.getConfig("Perspective", "scale"))
    rotate_bboxes = context.getBoolean("Image", "rotate_bboxes")
    theta, phi, gamma = get_random_angles(theta_range, phi_range, gamma_range, step)

    result_image, result_bboxes = warp_image(image, theta, phi, gamma, scale, fov, bboxes, rotate_bboxes)
    return result_image, result_bboxes


#region bounding box operations
# TODO: Move bbox functions to utility?

def coords_to_bbox(coords):
    """Converts (x1,y1,x2,y2) rectangular coordinates to bounding box representation (cx,xy,w,h)"""
    width = (coords[2] - coords[0]) # w = x2 - x1
    height = (coords[3] - coords[1]) # h = y2 - y1 
    center_x = coords[0] + (width / 2) 
    center_y = coords[1] + (height / 2)
    return (center_x, center_y, width, height)


def bbox_to_coords(bbox):
    """Converts bounding box representation (cx,xy,w,h) to (x1,y1,x2,y2) coordinates"""
    cx, cy, w, h = bbox['cx'], bbox['cy'], bbox['w'], bbox['h']
    x1 = cx - w/2
    y1 = cy - h/2
    x2 = x1 + w
    y2 = y1 + h

    return (int(x1), int(y1), int(x2), int(y2))


def get_bbox_vertices(bbox):
    """Returns a clock-wise ordered list of vertices of a bbox, accounting for rotation"""
    bbox_coords = bbox_to_coords(bbox)
    bbox_vertices = [
        [bbox_coords[0], bbox_coords[1]],
        [bbox_coords[2], bbox_coords[1]],
        [bbox_coords[2], bbox_coords[3]],
        [bbox_coords[0], bbox_coords[3]]
    ]
    cx, cy, w, h = bbox['cx'], bbox['cy'], bbox['w'], bbox['h']
    angle = np.deg2rad(bbox['angle']) # Calculations need to be done in radians
    if angle != 0: # Calculate new coordinates if bbox is rotated
        for vertex in bbox_vertices:
            temp_x = vertex[0] - cx
            temp_y = vertex[1] - cy
            rot_x = (temp_x * math.cos(angle)) - (temp_y * math.sin(angle)) + cx
            rot_y = (temp_x * math.sin(angle)) + (temp_y * math.cos(angle)) + cy
            vertex[0] = rot_x
            vertex[1] = rot_y

    return bbox_vertices

def get_centroid(vertices):
    """Calculates polygon centroid from a list of vertices"""
    verts_x = [v[0] for v in vertices]
    verts_y = [v[1] for v in vertices]
    centroid_x = sum(verts_x) / len(vertices)
    centroid_y = sum(verts_y) / len(vertices)
    
    return [centroid_x, centroid_y]

#endregion
