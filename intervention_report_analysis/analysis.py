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
    DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare)


_logger = logging.getLogger(__name__)

class account_analytic_account(orm.Model):
    ''' Add extra info for account
    '''
    _inherit = 'account.analytic.account'

    def onchange_cost_parameter(self, cr, uid, ids, hour_cost, total_amount, 
            total_hours, field='hour_cost', context=None):
        ''' Calculate 2 value depend on change element         
        '''
        if field == 'total_amount':
            if total_hours: 
                hour_cost = total_amount / total_hours
            elif hour_cost:
                total_hours = total_amount / hour_cost
            else: # hour_cost = 0
                total_hours = 0
        elif field == 'total_hours':
            if hour_cost:
                total_amount = hour_cost * total_hours
            else: # no hour_cost
                if total_hours:
                    hour_cost = total_amount / total_hours
                else:
                    hour_cost = 0
        else: # 'hour_cost':
            if total_hours:
                total_amount = total_hours * hour_cost
            else:
                if hour_cost:
                    total_hours = total_amount / hour_cost
                else:
                    total_hours = 0  
        return {
            'value': {
                'total_amount': total_amount,
                'total_hours': total_hours,
                'hour_cost': hour_cost,
                },
            }

    # -------------------------------------------------------------------------
    # Function fields:
    # -------------------------------------------------------------------------
    def _get_done_hour_total(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        ts_pool = self.pool.get('hr.analytic.timesheet')
        ts_ids = ts_pool.search(cr, uid, [
            ('account_id', 'in', ids),
            ], context=context)
        for ts in ts_pool.browse(cr, uid, ts_ids, context=context):
            invoiced_hour = 0.0
            account_id = ts.account_id.id
            if account_id in res:
                res[account_id] += invoiced_hour 
            else:  
                res[account_id] = invoiced_hour         
        return res
        
    _columns = {
        # Amount:
        'total_amount': fields.float('Total amount', 
            digits=(16, 2), 
            help='Total amount of contract'), 
        'hour_cost': fields.float('Hour cost', 
            digits=(16, 2),
            help='Hour cost (total / number of hours)'), 
        'hour_cost_customer': fields.related(
            'partner_id', 'hour_cost', type='float', digits=(16, 2), 
            string='Customer hour cost', 
            help='Remember starndar customer hour cost'),

        'hour_done': fields.function(
            _get_done_hour_total, method=True,
            type='float', string='Done hour', store=False), 
                        
        # Date period:
        'from_date': fields.date('From'),
        'to_date': fields.date('To'),
        }

class account_analytic_account_distribution(orm.Model):
    ''' Distribution of hour
    '''
    _name = 'account.analytic.account.distribution'
    _description = 'User distribution for contract'
    _rec_name = 'user_id'
    
    _columns = {
        'user_id': fields.many2one('res.users', 'Users', required=True),
        'account_id': fields.many2one(
            'account.analytic.account', 'Account'),
        'percentual': fields.float('% of hours', 
            digits=(8, 2), help='Percentual on total hour'), 
        }

class account_analytic_account_invoice(orm.Model):
    ''' Invoice for account
    '''
    _name = 'account.analytic.account.invoice'
    _description = 'Invoice extra for contract'
    _rec_name = 'name'
    
    _columns = {
        'name': fields.char('Invoice ref.', size=40),
        'hour': fields.float('Hour', digits=(16, 2),
            help='Number of hours'), 
        'hour_cost': fields.float('Hour cost', digits=(16, 2),
            help='Number of hours'), 
        'total_amount': fields.float('Total amount', digits=(16, 2)), 

        'account_id': fields.many2one('account.analytic.account', 'Account', 
            required=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        #'date_invoice': fields.related(
        #    'invoice_id', 'date_invoice', 'Invoice date', type='date'),
        }

class account_analytic_account(orm.Model):
    ''' Add *many relation
    '''
    _inherit = 'account.analytic.account'
    
    _columns = {
        'distribution_ids': fields.one2many(
            'account.analytic.account.distribution', 'account_id', 
            'Distribution'),
        'invoice_ids': fields.one2many(
            'account.analytic.account.invoice', 'account_id', 
            'Invoice'),      
        }
        
class account_invoice(orm.Model):
    ''' Add *many relation
    '''
    _inherit = 'account.invoice'
    
    _columns = {
        'analytic_invoice_ids': fields.one2many(
            'account.analytic.account.invoice', 'invoice_id', 
            'Analytic Invoice'),
        }        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
