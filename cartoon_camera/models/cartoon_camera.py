
#pip install onvif-zeep wsdiscovery
from odoo import models, fields, api
import os
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
    time_start = fields.Float(string='Start Time', default=0.0)
    time_end = fields.Float(string='End Time', default=0.0)
    fps = fields.Float(string='FPS', default=0.0)
    flip = fields.Boolean(string='Flip Image', default=False)
    token = fields.Char(string='Token', default="000")
    velocity_h = fields.Float(string='Horizontal Velocity', default=0.1)
    velocity_v = fields.Float(string='Vertical Velocity', default=0.1)
    height = fields.Integer(string='Height', default=720)
    width = fields.Integer(string='Width', default=640)
    nb_height = fields.Integer(string='Grid Rows', default=2)
    nb_width = fields.Integer(string='Grid Columns', default=1)


    def discovery(self):
        """
        Discover ONVIF-compatible cameras on the network.
        """
        ws_discovery = ThreadedWSDiscovery()
        ws_discovery.start()
        services = ws_discovery.searchServices()
        ws_discovery.stop()

        cameras = []
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

    def get_camera_info(self):
        """ Get information on camera """
        module_path = os.path.dirname(os.path.abspath(__file__))
        wsdl_path = module_path.replace('cartoon_camera/models', 'cartoon_camera/wsdl')

        for camera in self:

            # Connexion à la caméra ONVIF
            onvif_camera = ONVIFCamera(camera.ip, camera.port, camera.user, camera.password,
                                       wsdl_dir=wsdl_path)
            # Service de gestion des médias
            media_service = onvif_camera.create_media_service()

            # Récupérer les profils disponibles
            profiles = media_service.GetProfiles()

            for profile in profiles:
                print(f"Profile: {profile.Name}")
                print(dir(profile))

                # Résolution vidéo
                video_config = profile.VideoEncoderConfiguration
                if video_config:
                    print(f"Resolution: {video_config.Resolution.Width}x{video_config.Resolution.Height}")

                # URI pour les captures d'images (Snapshot URI)
                snapshot_uri = media_service.GetSnapshotUri({'ProfileToken': profile.token})
                print(f"Snapshot URI: {snapshot_uri.Uri}")


