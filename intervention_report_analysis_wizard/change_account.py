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

class intervention_status_account_wizard(osv.osv):
    ''' Force operation object
    '''    
    _name = 'hr.intervent.account.force'
    _description = 'Force intervention analysis'

    def get_domain(self, cr, uid, ids, context=None):
        ''' Utility for get name of domain from selected element in record:
        '''
        item_proxy = self.browse(cr, uid, ids)[0]

        domain = []

        # Text:
        if item_proxy.description:
            domain.append(
                ('name', 'ilike', item_proxy.description))

        # Date:
        if item_proxy.from_date:
            domain.append(
                ('date_start', '>=', '%s 00:00:00' % item_proxy.from_date))

        if item_proxy.to_date:
            domain.append(
                ('date_start', '<', '%s 23:59:59' % item_proxy.to_date))

        # Selection:
        #if item_proxy.mode:
        #    domain.append(
        #        ('mode', '<', item_proxy.mode))

        # Relation:
        if item_proxy.user_id:
            domain.append(
                ('user_id', '<', item_proxy.user_id.id))

        if item_proxy.account_id:
            domain.append(
                ('account_id', '<', item_proxy.account_id.id))
                
        if item_proxy.intervent_partner_id:
            domain.append(
                ('intervent_partner_id', '<', item_proxy.intervent_partner.id))
        
        return domain        
        
    def action_find(self, cr, uid, ids, context=None):
        ''' Find record of selected elements:
        ''' 
        domain = self.get_domain(cr, uid, ids, context=context)

        # Search list of record with domain passed: 
        # TODO
        intervent_pool = self.pool.get('hr.analytic.timesheet')
        return True
        
    def action_change(self, cr, uid, ids, context=None):
        ''' Force changing of account
        ''' 
        domain = self.get_domain(cr, uid, ids, context=context)

        # TODO
        return True
        
        
    _columns = {
        # Log fields:
        'name': fields.char('Name of operation', size=256, required=True),
        'new_account_id': fields.many2one('account.analytic.account', 
            'Force to Account', required=True),
        'log_date': fields.datetime('Log date for operation'),
        'note': fields.text('Note'),
    
        # Filter fields:
        'description': fields.char('Description', size=256),

        'from_date': fields.date('From date >='),
        'to_date': fields.date('To date <'),
        
        #'mode': fields.selection('Mode'),
            
        'user_id': fields.many2one('res.users', 'User'),
        'account_id': fields.many2one('account.analytic.account', 'Account'),
        'intervent_partner_id': fields.many2one('res.partner', 'Partner'),
        }
        
    _defaults = {    
        'log_date': lambda *x: datetime.now().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT),
        }    
    
class hr_analytic_timesheet(osv.osv):
    ''' Add reference for forced elements:
    '''
    _inherit = 'hr.analytic.timesheet'
    
    _columns = {
        'force_operation_id': fields.many2one('hr.intervent.account.force', 
            'Force operation', ondelete='set null'),
        }

class intervention_status_account_wizard(osv.osv):
    ''' *many fields
    '''    
    _inherit = 'hr.intervent.account.force'
    
    _columns = {
        'intervent_ids': fields.many2one('hr.analytic.timesheet', 
            'force_operation_id', 'Intervent'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
