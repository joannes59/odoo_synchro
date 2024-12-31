
#pip install onvif-zeep wsdiscovery
from odoo import models, fields, api
import os
import numpy as np
import base64
import cv2
import time
import urllib.request
from wsdiscovery.discovery import ThreadedWSDiscovery
from onvif import ONVIFCamera

class CartoonCamera(models.Model):
    _name = 'cartoon.camera'
    _description = 'Onvif Camera'

    name = fields.Char(string='Name')
    uuid = fields.Char(string='uuid')
    ip = fields.Char(string='IP Address')
    port = fields.Integer(string='Port', default=8899)
    http = fields.Char(string='HTTP Protocol', default="http://")
    user = fields.Char(string='User', default='admin')
    password = fields.Char(string='Password', default='1234567890')
    snap_path = fields.Char(string='Snapshot Path', default="/webcapture.jpg?command=snap")
    ping = fields.Integer(string='Ping (ms)', default=0.0)
    fps = fields.Float(string='FPS', default=0.0)
    flip = fields.Boolean(string='Flip Image', default=False)
    token = fields.Char(string='Token', default="000")
    velocity_h = fields.Float(string='Horizontal Velocity', default=0.1)
    velocity_v = fields.Float(string='Vertical Velocity', default=0.1)
    height = fields.Integer(string='Height', default=720)
    width = fields.Integer(string='Width', default=640)
    nb_height = fields.Integer(string='Grid Rows', default=2)
    nb_width = fields.Integer(string='Grid Columns', default=1)
    profile = fields.Text('Profile')
    frame = fields.Binary(string="Image Frame", attachment=True)
    state = fields.Selection([('draft', 'draft'), ('online', 'online'), ('enabled', 'enabled'),
                              ('error', 'error'), ('disabled', 'disabled')],
                             string='State', default='draft')

    def toggle_state(self):
        for record in self:
            if record.state not in ['disabled', 'draft']:
                record.state = 'disabled'
            elif record.state in ['disabled', 'draft', 'error', 'online']:
                record.state = 'enabled'

    def discovery(self):
        """
        Discover ONVIF-compatible cameras on the network.
        """
        ws_discovery = ThreadedWSDiscovery()
        ws_discovery.start()
        services = ws_discovery.searchServices()
        ws_discovery.stop()

        for service in services:
            try:
                xaddr = service.getXAddrs()[0]
                ip = xaddr.split("//")[-1].split(":")[0]
                uuid = service.getEPR().split(':')[-1]
                #service.getInstanceId())
                #service.getMessageNumber())
                #service.getMetadataVersion())
                #service.getScopes() [onvif://www.onvif.org/type/video_encoder, onvif://www.onvif.org/type/audio_encoder, onvif://www.onvif.org/hardware/IPC-model, onvif://www.onvif.org/location/country/china, onvif://www.onvif.org/name/NVT, onvif://www.onvif.org/Profile/Streaming, onvif://www.onvif.org/A1C2B3/mac/4c:60:ba:af:56:57, onvif://www.onvif.org/Profile/T]
                #service.getTypes()) [http://www.onvif.org/ver10/network/wsdl:NetworkVideoTransmitter, http://www.onvif.org/ver10/device/wsdl:Device]
                vals = {
                    'uuid': uuid,
                    'ip': ip,
                }
                camera_ids = self.search([('uuid', '=', uuid)])
                if camera_ids:
                    camera_ids.write(vals)
                else:
                    camera_ids.create(vals)
            except Exception as e:
                continue

    def get_wsdl_path(self):
        """ return local wsdl path """
        module_path = os.path.dirname(os.path.abspath(__file__))
        wsdl_path = module_path.replace('cartoon_camera/models', 'cartoon_camera/wsdl')
        return wsdl_path

    def get_camera_info(self):
        """ Get information on camera """
        wsdl_path = self.get_wsdl_path()

        for camera in self:
            text_profile = ''
            # Connexion à la caméra ONVIF
            onvif_camera = ONVIFCamera(camera.ip, camera.port, camera.user, camera.password,
                                       wsdl_dir=wsdl_path)
            # Service de gestion des médias
            media_service = onvif_camera.create_media_service()

            # Récupérer les profils disponibles
            profiles = media_service.GetProfiles()
            if len(profiles) >= 1:
                camera.token = profiles[0].token

            for profile in profiles:
                # URI pour les captures d'images (Snapshot URI)
                snapshot_uri = media_service.GetSnapshotUri({'ProfileToken': profile.token})
                text_profile += f"{profile.token};{profile.Name};{snapshot_uri.Uri}\n"
            camera.profile = text_profile

    def get_snapshot(self):
        """ Get image snapshot """
        for camera in self:
            time_start = time.time()
            try:
                snapshot_url = f"{camera.http}{camera.ip}{camera.snap_path}"
                img = urllib.request.urlopen(snapshot_url, timeout=2)
                img_array = np.array(bytearray(img.read()), dtype=np.uint8)
                frame = cv2.imdecode(img_array, -1)
                camera.state = 'online'
            except:
                frame = np.zeros((camera.height, camera.width, 3), dtype=np.uint8)
                camera.state = 'error'
                return False

            if camera.flip:
                frame = cv2.flip(frame, 0)

            # Encoder l'image en Base64
            _, buffer = cv2.imencode('.jpg', frame)
            encoded_image = base64.b64encode(buffer).decode('utf-8')

            # Mettre à jour les champs
            height, width, _ = frame.shape
            camera.height = height
            camera.width = width
            camera.frame = encoded_image
            camera.ping = int((time.time() - time_start) * 100.0)
        return True

    def pantilt(self):
        """ move the camera """
        wsdl_path = self.get_wsdl_path()
        pan_x = self.env.context.get('pan_x', 0.0)
        pan_y = self.env.context.get('pan_y', 0.0)
        #pan_z = self.env.context.get('pan_z', 0.0)

        for camera in self:
            onvif_camera = ONVIFCamera(camera.ip, camera.port, camera.user, camera.password,
                                       wsdl_dir=wsdl_path)

            ptz_service = onvif_camera.create_ptz_service()
            request = ptz_service.create_type('ContinuousMove')
            request.ProfileToken = camera.token

            # Déplacement relatif Pan-Tilt-Zoom
            if camera.flip:
                pan_y = - pan_y

            request.Velocity = {'PanTilt': {'x': pan_x * camera.velocity_v, 'y': pan_y * camera.velocity_h}}
            #                                'Zoom': {'x': pan_z}}

            # Exécution de la commande
            ptz_service.ContinuousMove(request)
            time.sleep(0.5)
            ptz_service.Stop({'ProfileToken': camera.token})
            camera.get_snapshot()
