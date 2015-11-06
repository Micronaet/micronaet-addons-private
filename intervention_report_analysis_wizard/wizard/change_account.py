# -*- coding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
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
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class intervention_status_account_wizard(osv.osv_memory):
    ''' Wizard for change account
    '''    
    _name = 'hr.intervent.account.wizard'
    _description = 'Intervention analysis wizard'

    def action_change(self, cr, uid, ids, context=None):
        ''' Force changing of account
        ''' 
        
        wiz_proxy = self.browse(cr, uid, ids)[0]

        domain = []

        # Text:
        if wiz_proxy.name:
            domain.append(
                ('name', 'ilike', wiz_proxy.name))

        # Date:
        if wiz_proxy.from_date:
            domain.append(
                ('intervent_date', '>=', '%s 00:00:00' % wiz_proxy.from_date))

        if wiz_proxy.to_date:
            domain.append(
                ('intervent_date', '<', '%s 23:59:59' % wiz_proxy.to_date))

        # Selection:
        if wiz_proxy.mode:
            domain.append(
                ('mode', '<', wiz_proxy.mode))

        # Relation:
        if wiz_proxy.user_id:
            domain.append(
                ('user_id', '<', wiz_proxy.user_id.id))

        if wiz_proxy.account_id:
            domain.append(
                ('account_id', '<', wiz_proxy.account_id.id))
                
        if wiz_proxy.intervent_partner_id:
            domain.append(
                ('intervent_partner_id', '<', wiz_proxy.intervent_partner.id))

        # Search list of 
        intervent_pool = self.pool.get('hr.analytic.timesheet')
        
        # Return on list updated record:
        return {
            # TODO
            }
        
    _columns = {
        'name': fields.char('Name', size=256), 
    
        'from_date': fields.date('From date >='),
        'to_date': fields.date('To date <'),
        
        'mode': fields.selection(, 'Mode'),
            
        'user_id': fields.many2one('res.users', 'User'),
        'account_id': fields.many2one('account.analytic.account', 'Account'),
        'intervent_partner_id': fields.many2one('res.partner', 'Partner'),

        'new_account_id': fields.many2one('account.analytic.account', 
            'Force to Account', required=True),
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
