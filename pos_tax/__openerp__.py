# -*- coding: utf-8 -*-
{
    'name': "POS Tax",
    'version': '1.0.0',
    'category': 'Point of Sale',
    'author': 'TL Technology',
    'live_test_url': 'http://posodoo.com/web/signup',
    'price': '49',
    'website': 'http://posodoo.com',
    'sequence': 0,
    'depends': [
        'pos_base'
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/parameter_data.xml',
        'template/import_library.xml',
        'views/pos_config.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    "currency": 'EUR',
    "external_dependencies": {
        "python": [],
        "bin": []
    },
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    # "license": "OPL-1",
    'installable': True,
    'application': True,
    'post_init_hook': 'auto_action_after_install',
}
