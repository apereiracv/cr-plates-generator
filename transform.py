#!/usr/bin/python
# Code adapted from: https://nbviewer.jupyter.org/github/manisoftwartist/perspectiveproj/blob/master/perspective.ipynb

import numpy as np
import cv2
from functools import reduce

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
    # TODO: This transformation might not be needed
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

def warp_matrix(width, height, theta, phi, gamma, scale, field_vision):
    
    # M is to be estimated
    #M = np.eye(4, 4)
    
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
    P[0,0]  = 1.0/np.tan(fv_half)
    P[1,1]  = P[0,0]
    P[2,2]  = -(f+n)/(f-n)
    P[2,3]  = -(2.0*f*n)/(f-n)
    P[3,2]  = -1.0
    
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

    return M33, side_length


def warp_image(image, theta, phi, gamma, scale, fovy):
    height, width, _ = image.shape
    matrix, side_length = warp_matrix(width, height, theta, phi, gamma, scale, fovy); #Compute warp matrix
    side_length = int(side_length)
    print('Output image dimension = {}'.format(side_length))
    result = cv2.warpPerspective(image,matrix, (side_length, side_length)); #Do actual image warp
    return result
