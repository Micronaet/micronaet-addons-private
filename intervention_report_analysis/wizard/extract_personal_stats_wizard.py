# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class AccountAnalyticAccount(orm.Model):
    """ Model name: Account 
    """    
    _inherit = 'account.analytic.account'
    
    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def get_account_distribution(self, user_id, from_date, to_date, account):
        ''' Check account total for user passed
        '''
        total = account.total_hours
        if not total:
            _logger.error('No total hour in account!')
            return 0.0 # Nothing todo
        
        # Wizard period:    
        from_dt = datetime.strptime(
            from_date, DEFAULT_SERVER_DATE_FORMAT)
        to_dt = datetime.strptime(
            to_date, DEFAULT_SERVER_DATE_FORMAT)
        # start day yet included    
        days = (to_dt - from_dt).days 

        # Account period:
        if not account.from_date or not account.to_date:
            return 0.0

        account_from_dt = datetime.strptime(
            account.from_date, DEFAULT_SERVER_DATE_FORMAT)
        account_to_dt = datetime.strptime(
            account.to_date, DEFAULT_SERVER_DATE_FORMAT)
        # start day yet included
        account_days = (account_to_dt - account_from_dt).days + 1 # start day
        
        if not account_days:
            _logger.error('No period in account!')            
            return 0.0
        
        if user_id:
            my = 0.0
            for distribution in account.distribution_ids:
                if user_id == distribution.user_id.id:
                    my += distribution.percentual # if more than one user_id
        else:
            my = 100.0 # no user filter all todo            
                
        account_todo = total * days / account_days
        return account_todo * my / 100.0 # return my hours

class AccountDistributionStatsWizard(orm.TransientModel):
    ''' Wizard for extra distribution stats
    '''
    _name = 'account.distribution.stats.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_print(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        # ---------------------------------------------------------------------
        # UTILITY:
        # ---------------------------------------------------------------------
        def widget_float_time(value):
            ''' Change float in HH:MM format
            '''
            approx = 0.001            
            if not value:
                return ''#'0:00'
            
            hour = int(value)
            minute = int((value - hour + approx) * 60.0)    
            return '%s:%02d' % (hour, minute)
                
        if context is None: 
            context = {}        
        
        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        ts_pool = self.pool.get('hr.analytic.timesheet')
        account_pool = self.pool.get('account.analytic.account')

        # Parameters:        
        from_date = wiz_browse.from_date
        to_date = wiz_browse.to_date
        
        user_id = wiz_browse.user_id.id or False  
        user_name = wiz_browse.user_id.name or _('Nessuno')
        
        account_id = wiz_browse.account_id.id or False    
        account_name = wiz_browse.account_id.name or _('Nessuno')
        
        partner_id = wiz_browse.partner_id.id or False    
        partner_name = wiz_browse.partner_id.name or _('Nessuno')
        
        contract = wiz_browse.contract
        
        res = {}
        domain = []
        # Period:
        if from_date:
            domain.append(
                ('date_start', '>=', '%s 00:00:00' % from_date))
        if to_date:
            domain.append(
                ('date_start', '<', '%s 00:00:00' % to_date))
        if user_id:
            domain.append(
                ('user_id', '=', user_id))
        if account_id:
            domain.append(
                ('account_id', '=', account_id))
        if partner_id:
            domain.append(
                ('intervent_partner_id', '=', partner_id))
        if contract:         
            account_ids = account_pool.search(cr, uid, [
                ('distribution_ids', '!=', False),
                ('state', 'in', ('draft', 'open')),
                ], context=context)         
            for account in account_pool.browse(
                    cr, uid, account_ids, context=context):
                # for user filter check if user is in distribution:
                todo = account_pool.get_account_distribution(
                    user_id, from_date, to_date, account)
                if user_id and user_id not in [
                        item.user_id.id for item in account.distribution_ids]:
                    continue
                res[account] = [
                    todo,
                    0.0, # done pay
                    0.0, # done gratis
                    0.0, # invoiced                    
                    ]
        
        # ---------------------------------------------------------------------        
        # Collect statistics:
        # ---------------------------------------------------------------------        
        my_total = 0.0
        ts_ids = ts_pool.search(cr, uid, domain, context=context)
        for intervent in ts_pool.browse(cr, uid, ts_ids, context=context):
            account = intervent.account_id
            if account not in res:
                todo = account_pool.get_account_distribution(
                    user_id, from_date, to_date, account)
                # Total hour, todo
                res[account] = [
                    todo,
                    0.0, 
                    0.0, 
                    0.0, 
                    ]
            if intervent.to_invoice.factor == 100:
                res[account][1] += intervent.unit_amount # Total hour invoiced
                my_total += intervent.unit_amount
            else:    
                res[account][2] += intervent.unit_amount # Total hour gratis
            res[account][3] += intervent.extra_invoiced_total # Extra invoiced
            my_total += intervent.extra_invoiced_total
            
        WS_name = _('Statistiche')
        excel_pool.create_worksheet(WS_name)

        # ---------------------------------------------------------------------
        #                               EXCEL:
        # ---------------------------------------------------------------------
        # Layout setup:        
        excel_pool.column_width(WS_name, [40, 25, 10, 10, 10])

        # Title:
        row = 0
        excel_pool.write_xls_line(WS_name, row, [
            'Report: Data [%s - %s]' % (from_date, to_date),  
            ])
        row += 1    
        excel_pool.write_xls_line(WS_name, row, [
            'Utente: %s Conto: %s  - Contratti: %s' % (
                user_name, 
                account_name,
                'SI' if contract else 'NO',
                ),
            ])
        row += 1    
        excel_pool.write_xls_line(WS_name, row, [
            'Totale a pagamento: %s' % my_total,
            ])
        
        # Header:
        row += 2
        excel_pool.write_xls_line(WS_name, row, [
            'Conto analitico', 
            'Cliente',
            'H. tot.',
            'Fabbisogno',
            'Ore pag.',             
            'Ore grat.',
            'Ore fatt.',
            ])

        
        # Write data:
        for account in sorted(
                res, key=lambda x: (
                    0 if res[x][1] else 1, 
                    x.partner_id.name,
                    x.name,
                    )):
            row += 1
            data = res[account]
            excel_pool.write_xls_line(WS_name, row, [
                account.name, 
                account.partner_id.name,
                account.total_hours,
                widget_float_time(data[0]), # account todo
                widget_float_time(data[1]), 
                widget_float_time(data[2]), 
                widget_float_time(data[3]), 
                ])
                
        return excel_pool.return_attachment(
            cr, uid, 'Statistiche', version='7.0', 
            context=context)

    _columns = {
        'contract': fields.boolean('With contract', 
            help='Always add also contract with distribution'),
        'float_hour': fields.boolean('Formatted hour', 
            help='If checked print hour in HH:MM format'),
        'from_date': fields.date('From date >= ', required=True),
        'to_date': fields.date('To date <', required=True),
        'account_id': fields.many2one(
            'account.analytic.account', 'Account'),
        'user_id': fields.many2one(
            'res.users', 'User'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner'),
        }
        
    _defaults = {
        'contract': lambda *x: True,
        'float_hour': lambda *x: True,
        'user_id': lambda s, cr, uid, ctx: uid,
        'from_date': lambda *x: datetime.now().strftime('%Y-%m-01'),
        'to_date': lambda *x: (
            datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


