# -*- coding: utf-8 -*
from odoo.http import request
from openerp.addons.bus.controllers.main import BusController
from odoo import api, http, SUPERUSER_ID
from openerp.addons.web.controllers.main import ensure_db, Home, Session, WebClient
from openerp.addons.point_of_sale.controllers.main import PosController
from openerp.addons.base.ir.ir_qweb import AssetsBundle
import json
import logging
import base64
import werkzeug.utils

_logger = logging.getLogger(__name__)
