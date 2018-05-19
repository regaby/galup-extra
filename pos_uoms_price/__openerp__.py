{
    'name': 'POS UOMs Price',
    'sequence': 0,
    'version': '1.4',
    'author': 'TL Technology',
    'description': 'Multi Uoms(Prices) on POS',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        '__import__/template.xml',
        'view/pos_uoms_price.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
    'price': '50',
    'website': 'http://bruce-nguyen.com',
    "currency": 'EUR',
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'support': 'thanhchatvn@gmail.com'
}
