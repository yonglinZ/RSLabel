# -*- coding:utf-8 -*-
# !/usr/bin/env python

import argparse
import json
import numpy as np
import glob
import functools


def map2img(geoTrans, x, y):
    u = (x - geoTrans[0]) / geoTrans[1]
    v = (geoTrans[3] - y) / -geoTrans[5]
    return u, v


def map2img_p(geoTrans, p):
    u = (p[0] - geoTrans[0]) / geoTrans[1]
    v = (geoTrans[3] - p[1]) / -geoTrans[5]
    return u, v


def img2map(geoTrans, x, y):
    u = geoTrans[0] + geoTrans[1]*x
    v = geoTrans[3] + geoTrans[5]*y
    return [u, v]


def img2map_p(geoTrans, p):
    u = geoTrans[0] + geoTrans[1]*p[0]
    v = geoTrans[3] + geoTrans[5]*p[1]
    return u, v

def offset(tileSz, row, col, x, y):
    u = x - col * tileSz
    v = (row + 1) * tileSz - y 
    return u, v

def offset_p(tileSz, row, col, p):
    u = p[0] - col * tileSz
    v = (row + 1) * tileSz - p[1]
    return u, v


class labelme2coco(object):
    def __init__(self, labelme_json=[], save_json_path='./new.json'):
        '''
        :param labelme_json: labelme json list
        :param save_json_path: output coco json file 
        '''
        self.labelme_json = labelme_json
        self.save_json_path = save_json_path
        self.images = []
        self.categories = []
        self.annotations = []
        # self.data_coco = {}
        self.labels = []
        self.annID = 1
        self.height = 0
        self.width = 0
        self.save_json()

    def data_transfer(self):
        for num, json_file in enumerate(self.labelme_json):
            with open(json_file, 'r') as fp:
                data = json.load(fp)  #
                self.images.append(self.image(data, num))
                otherData = {}
                keys = [
                    'imageData',
                    'imagePath',
                    'lineColor',
                    'fillColor',
                    'shapes',  # polygonal annotations
                    'flags',   # image level flags
                    'imageHeight',
                    'imageWidth', ]
                for key, value in data.items():
                    if key not in keys:
                        otherData[key] = value
                geoTrans = otherData['geoTrans']
                mapfunc = functools.partial(map2img_p, geoTrans)
                for shape in data['shapes']:
                    label = shape['label'].split('_')
                    if(len(label) == 2):  # *
                        if label[1] not in self.labels:
                            self.categories.append(self.categorie(label))
                            self.labels.append(label[1])
                    else:
                        if label[0] not in self.labels:
                            self.categories.append(self.categorie(label))
                            self.labels.append(label[0])
                    points = shape['points']
                    # convert to image coord
                    points = list(map(mapfunc, points))
                    self.annotations.append(
                        self.annotation(points, label, num))
                    self.annID += 1

    def image(self, data, num):
        image = {}
        height, width = data['imageHeight'], data['imageWidth']
        image['height'] = height
        image['width'] = width
        image['id'] = num+1
        image['file_name'] = data['imagePath'].split('/')[-1]
        self.height = height
        self.width = width
        return image

    def categorie(self, label):
        categorie = {}
        if(len(label) == 2):
            categorie['supercategory'] = label[0]
            categorie['id'] = len(self.labels)+1  #
            categorie['name'] = label[1]
        else:
            categorie['supercategory'] = None
            categorie['id'] = len(self.labels)+1  #
            categorie['name'] = label[0]
        return categorie

    def annotation(self, points, label, num):
        annotation = {}
        annotation['segmentation'] = [list(np.asarray(points).flatten())]
        annotation['iscrowd'] = 0
        annotation['image_id'] = num+1
        annotation['bbox'] = list(map(int, self.getbbox(points)))
        annotation['category_id'] = self.getcatid(label)
        annotation['id'] = self.annID
        return annotation

    def getcatid(self, label):
        for categorie in self.categories:
            if(len(label) == 2):
                if label[1] == categorie['name']:
                    return categorie['id']
            elif(len(label) == 1):
                if label[0] == categorie['name']:
                    return categorie['id']
        return -1

    def getbbox(self, points):
        polygons = points
        array = np.array(polygons).reshape(-1, 2)
        print('* getbbox', array)
        left_top_c, left_top_r = np.min(array, 0)[0], np.min(array, 0)[1]
        right_bottom_c, right_bottom_r = np.max(
            array, 0)[0], np.max(array, 0)[1]
        print('*bbox: {},{},{},{}'.format(left_top_c,
                                          left_top_r, right_bottom_c, right_bottom_r))
        return [left_top_c, left_top_r, right_bottom_c-left_top_c, right_bottom_r-left_top_r]

    def mask2box(self, polygons):
        index = np.argwhere(mask == 1)
        rows = index[:, 0]
        clos = index[:, 1]
        left_top_r = np.min(rows)  # y
        left_top_c = np.min(clos)  # x
        right_bottom_r = np.max(rows)
        right_bottom_c = np.max(clos)

    def data2coco(self):
        data_coco = {}
        data_coco['images'] = self.images
        data_coco['categories'] = self.categories
        data_coco['annotations'] = self.annotations
        return data_coco

    def save_json(self):
        self.data_transfer()
        self.data_coco = self.data2coco()
        json.dump(self.data_coco, open(self.save_json_path, 'w'),
                  indent=4)
