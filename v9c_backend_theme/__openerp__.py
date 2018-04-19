# -*- coding: utf-8 -*-
# Copyright 2016 Openworx, LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Material/United Backend Theme",
    "summary": "Odoo 9.0 community backend theme",
    "version": "9.0.6",
    "category": "Themes/Backend",
    "website": "http://www.openworx.nl",
	"description": """
                Backend theme for Odoo 9.0 community edition.
                The app dashboard is based on the module web_responsive from LasLabs Inc and the theme on Bootstrap United
    """,
        'images':[
        'images/screen.png'
        ],
    "author": "Openworx",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web',
    ],
    "data": [
        'views/assets.xml',
        'views/web.xml',
        'views.xml',
    ],
    'qweb': ['static/src/xml/base.xml'],
}

