# -*- coding: utf-8 -*-
{
    'name': 'POS Fields Partner',
    'version': '0.1',
    'author': 'Galup Sistemas',
    'license': 'LGPL-3',
    'category': 'Point Of Sale',
    'website': 'www.galup.com.ar',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_fields_partner.xml',
        'views/report_receipt.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
}
