import odoorpc
import cv2
import time
import urllib.request
import numpy as np
import threading
import os

# pip install odoorpc opencv-python numpy


class RemoteCamera:
    """ Remote camera """
    def __init__(self, ip):
        self.snap_path = '?'
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
    def __init__(self):
        self.cameras = []

    def get_odoo(self):
        """ return odoorpc connection """
        odoo = odoorpc.ODOO('localhost', port=8069)
        db_name = 'projet'
        user = 'camera'
        passwd = 'camera'
        odoo.login(db_name, user, passwd)

    def multi_snapshot(self):
        """ get snapshot off all camera """
        # create queue to save image
        process = {}

        # Create thread
        for camera in self.cameras:
            process[camera.name] = threading.Thread(
                target=camera.get_snapshot,
                args=(),
                name=camera.name)

            process[camera.name + '_save'] = threading.Thread(
                target=camera.save_snapshot,
                args=(),
                name=camera.name + '_save')

        # start process
        for camera in self.cameras:
            process[camera.name].start()
        for camera in self.cameras:
            process[camera.name + '_save'].start()

        # wait end of process
        time.sleep(0.01)
        for camera in self.cameras:
            process[camera.name + '_save'].join()
        for camera in self.cameras:
            process[camera.name].join()





camera_ids = odoo.env['cartoon.camera'].search([])

cameras = []
for camera_id in camera_ids:
    cameras.append(odoo.env['cartoon.camera'].browse(camera_id))

camera_id = camera_ids[0]
for i in range(10):
    start = time.time()
    res = odoo.execute('cartoon.camera', 'get_snapshot', [3])
    print(time.time() - start)

print('-------------------------')
for i in range(10):
    start = time.time()
    snapshot_url = f"http://192.168.0.200/webcapture.jpg?command=snap"
    img = urllib.request.urlopen(snapshot_url, timeout=1)
    print(time.time() - start)



