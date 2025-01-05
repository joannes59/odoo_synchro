import odoorpc
import cv2
import time
import urllib.request
import numpy as np
import threading
import os
import json

# pip install odoorpc opencv-python numpy


class RemoteCamera:
    """ Remote camera """
    def __init__(self, ip):
        self.snap_path = '/webcapture.jpg?command=snap'
        self.name = '?'
        self.img = False
        self.id = 0
        self.flip = False
        self.odoo = False

    def get_snapshot(self):
        """ Get image snapshot 15-20 ms """
        try:
            snapshot_url = self.snap_path
            self.img = urllib.request.urlopen(snapshot_url, timeout=1)
        except:
            self.img = False

    def save_snapshot(self):
        """ Save image to file """
        if self.img:
            img_array = np.array(bytearray(self.img.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_array, -1)
            if self.flip:
                frame = cv2.flip(frame, 0)

class CameraManager:
    """ manage pool of camera """
    def __init__(self, config_path='config.json'):
        self.cameras = []
        self.config_path = config_path
        self.odoo = False

    def get_configuration(self):
        """ return odoorpc connection """
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        host =config['database']['host']
        port = config['database']['port']
        db_name = config['database']['db_name']
        username = config['database']['username']
        password = config['database']['password']

        odoo = odoorpc.ODOO(host, port)
        odoo.login(db_name, username, password)
        self.odoo = odoo

    def multi_snapshot(self):
        """ get snapshot off all camera """
        # create queue to save image
        process = {}

        # Create thread
        for camera in self.cameras:
            process[camera.name + '_save'] = threading.Thread(
                target=camera.save_snapshot,
                args=(),
                name=camera.name + '_save')
            process[camera.name] = threading.Thread(
                target=camera.get_snapshot,
                args=(),
                name=camera.name)

        # start process
        for camera in self.cameras:
            process[camera.name + '_save'].start()
        for camera in self.cameras:
            process[camera.name].start()

        # wait end of process
        time.sleep(0.01)
        for camera in self.cameras:
            process[camera.name + '_save'].join()
        for camera in self.cameras:
            process[camera.name].join()

