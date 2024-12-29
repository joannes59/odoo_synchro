{
    'name': 'Cartoon Camera',
    'version': '1.0',
    'author': 'joannes landy',
    'website': 'https://ateliersdelahalle.fr',
    'category': 'Tools',
    'summary': 'Management of IP cameras',
    'description': 'Management of IP cameras.',
    'depends': ['base'],
    'python': ['onvif-zeep', 'wsdiscovery', 'opencv-python'],
    'data': [
        'security/ir.model.access.csv',
        'views/cartoon_camera_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
