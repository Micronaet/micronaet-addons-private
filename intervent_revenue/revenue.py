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

class HrInterventUserMode(orm.Model):
    """ Model name: InterventUserMode
    """
    
    _name = 'hr.intervent.user.mode'
    _description = 'Intervent user mode'
    _rec_name = 'name'
    _order = 'name'
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'list_price': fields.float(
            'List price', digits=(16, 2), required=True),
        }

class HrInterventUserModeMap(orm.Model):
    """ Model name: InterventUserMode
    """
    
    _name = 'hr.intervent.user.mode.map'
    _description = 'Intervent user mode mapping'
    _order = 'user_id desc' # User map before
    
    _columns = {
        # ---------------------------------------------------------------------
        # Mapping details:
        # ---------------------------------------------------------------------
        'from_id': fields.many2one(
            'hr.intervent.user.mode', 'From category', required=True),
        'to_id': fields.many2one(
            'hr.intervent.user.mode', 'To category', required=True),
        'user_id': fields.many2one('res.users', 'User'),
            
        # ---------------------------------------------------------------------
        # Linked objects:    
        # ---------------------------------------------------------------------        
        'partner_id': fields.many2one(
            'res.partner', 'Partner case'),
        'operation_id': fields.many2one(
            'hr.analytic.timesheet.operation', 'Operation case'),
        }

class ResPartnerModeRevenue(orm.Model):
    """ Model name: Partner particular mode revenue
    """
    
    _name = 'res.partner.mode.revenue'
    _description = 'Partner mode revenue'
    
    _columns = {
        'partner_id': fields.many2one(
            'res.partner', 'Partner case'),
        'mode_id': fields.many2one('hr.intervent.user.mode', 'Mode'),
        'list_price': fields.float(
            'List price', digits=(16, 2), required=True),
        }

class ResPartner(orm.Model):
    """ Model name: ResPartner
    """
    
    _inherit = 'res.partner'
    
    _columns = {
        'mode_map_ids': fields.one2many(
            'hr.intervent.user.mode.map', 'partner_id', 'Partner map'),
        'mode_revenue_ids': fields.one2many(
            'res.partner.mode.revenue', 'partner_id', 'Partner revenue'),    
        }

class HrAnalyticTimesheetOperation(orm.Model):
    """ Model name: HrAnalyticTimesheetOperation
    """
    
    _inherit = 'hr.analytic.timesheet.operation'
    
    _columns = {
        'mode_map_ids': fields.one2many(
            'hr.intervent.user.mode.map', 'operation_id', 'Operation map'),
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
