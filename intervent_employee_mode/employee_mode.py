#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class HrEmployeeMode(orm.Model):
    """ Model name: HrEmployeeMode
    """
    
    _name = 'hr.employee.mode'
    _description = 'Employee mode'
    _rec_name = 'name'
    _order = 'name'
    
    _columns = {
        'name': fields.char(
            'Name', size=64, required=True, 
            ),
        'note': fields.text('Note'),    
        }

class ResPartnerHrModeRel(orm.Model):
    """ Model name: Res Partner Mode Rel
    """
    
    _inherit = 'res.partner.hr.mode.rel'
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'mode_id': fields.many2one('hr.employee.mode', 'Mode'),
        'revenue': fields.float('Revenue', digits=(16, 2), required=False),
        }

    _sql_constraints = [
        ('name_uniq', 'unique(partner_id, mode_id)', 
            'Parter - Mode must be unique!'),
        
        ]

class ResPartner(orm.Model):
    """ Model name: Res Partner
    """
    
    _inherit = 'res.partner'
    
    _columns = {
        'hr_ids': fields.one2many(
            'res.partner.hr.mode.rel', 'partner_id', 'HR mode'),
        }

class ResUsers(orm.Model):
    """ Model name: Res Users
    """
    
    _inherit = 'res.users'
    
    _columns = {
        'mode_id': fields.many2one('hr.employee.mode', 'Mode'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
