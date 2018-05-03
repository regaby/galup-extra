# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from openerp import models, fields, api, exceptions, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import except_orm, UserError, ValidationError
from openerp import tools


class HrAttendanceView(models.Model):
    _name = "hr.attendance.view"
    _description = "Attendance View"
    _order = "check_in desc"
    _auto = False


    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id", readonly=True)
    check_in = fields.Datetime(string="Check In", readonly=True)
    check_out = fields.Datetime(string="Check Out", readonly=True)
    worked_hours = fields.Float(string='Worked Hours', readonly=True)
    state = fields.Selection([('draft', 'Borrador'),
                               ('validated', 'Validado')],
                              'Estado', readonly=True)
    user_id = fields.Many2one('res.users', string='Validado por', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_attendance_view')
        cr.execute("""
            create or replace view hr_attendance_view AS 
            select id, employee_id, check_in, check_out, worked_hours, state, user_id
                from hr_attendance  hr
            """)
