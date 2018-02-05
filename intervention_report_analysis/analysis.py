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

    # Utility: extract Excel account intervent block:    
    def extract_excel_status(self, cr, uid, month, year, account,
            context=None):
        ''' Extract XLS status for intervent for this month and for
            this account analitic
        '''
        # Pool used:
        ts_pool = self.pool.get('hr.analytic.timesheet')        
        
        # ---------------------------------------------------------------------
        # Excel setup:
        # ---------------------------------------------------------------------
        WS_name = _('Fatturazione extra')
        WS_header = [
            'ID', 'Cliente', 'Data', 
            'Numero', 'Utente', 'Oggetto', 'Descrizione',
            'Fatturazione', 'H tot.', 'H fatt.', # da inserire
            ]
        WS_header_width = [
            1, 30, 20,
            10, 20, 30, 50,
            20, 10, 10,
            ]

        # ---------------------------------------------------------------------
        # Date filter for intervent selection:            
        # ---------------------------------------------------------------------
        # Start or end month:
        from_date = '%s-%s-01' % (year, month)
        date_dt = datetime.strptime(from_date, DEFAULT_SERVER_DATE_FORMAT)
        date_dt += relativedelta(months=1)
        to_date = '%s01' % date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)[:8]
        
        domain = [
            ('date_start', '>=', from_date),
            ('date_start', '<', to_date),
            ]
        if account:
            domain.append(
                ('account_id', '=', account.id)
                )

        # Read extract folder:                
        config_pool = self.pool.get('ir.config_parameter')
        config_ids = config_pool.search(cr, uid, [
            ('key', '=', 'intervention_export_root_folder')], context=context)
        if config_ids:
            config_browse = config_pool.browse(cr, uid, config_ids, 
                context=context)[0]    
            root_folder = config_browse.value
        month_folder = os.path.expanduser(
            os.path.join(root_folder, '%s_%s' % (
                year, month)))
        os.system('mkdir -p %s' % month_folder)

        ts_ids = ts_pool.search(cr, uid, domain, context=context)
        last_account = False
        for intervent in sorted(
                ts_pool.browse(cr, uid, ts_ids, context=context),
                key=lambda x: (
                    x.account_id.name,
                    x.intervent_partner_id.name,
                    x.date_start,                      
                    x.user_id.name,
                    )
                ):
            this_account = intervent.account_id
            if last_account == False or last_account != this_account:                
                if last_account != False: # previous exist:                
                    # Close and save previous:
                    excel_pool.save_file_as(os.path.join(
                        month_folder, 
                        excel_pool.clean_filename(last_account.name),
                        ))
                last_account = this_account
                
                # Create pool for every Excel file:
                excel_pool = self.pool.get('excel.writer')
                # Add header once:
                excel_pool.create_worksheet(WS_name)
                excel_pool.write_xls_line(WS_name, 0, WS_header)
                excel_pool.column_width(WS_name, WS_header_width)
                row = 0
            row += 1
            excel_pool.write_xls_line(WS_name, row, [
                intervent.id, 
                intervent.intervent_partner_id.name,
                intervent.date_start, 
                intervent.ref, 
                intervent.user_id.name,
                intervent.name,
                intervent.intervention,
                intervent.to_invoice.name,
                intervent.intervent_total,
                '', # insert from file (for reimport)
                ])
                
        if last_account != False:
            if account:        
                return excel_pool.return_attachment(
                    cr, uid, 'Interventi da valutare', 
                    'intervent.xlsx', version='7.0', context=context)
            else:
                # Close and save previous:
                excel_pool.save_file_as(os.path.join(
                    month_folder,
                    excel_pool.clean_filename(last_account.name),
                    ))                
        return True

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
        res = dict.fromkeys(ids, 0)
        
        ts_pool = self.pool.get('hr.analytic.timesheet')
        ts_ids = ts_pool.search(cr, uid, [
            ('account_id', 'in', ids),
            ], context=context)

        # Calculate intervent marked hours:
        for ts in ts_pool.browse(cr, uid, ts_ids, context=context):
            invoiced_hour = ts_pool.get_total_h_2_invoice(ts, no_factor=True)
            account_id = ts.account_id.id
            res[account_id] += invoiced_hour 
            
        # Remove invoiced hours:    
        for account in self.browse(cr, uid, ids, context=context):
            for invoice in account.invoice_ids:
                res[account.id] -= invoice.hour_removed
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
    
    def _get_total_hours(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        for dist in self.browse(cr, uid, ids, context=context):
            total_hours = dist.account_id.total_hours
            if total_hours:
                res[dist.id] = dist.percentual * total_hours / 100.0
            else:    
                res[dist.id] = 0
        return res         
        
    _columns = {
        'user_id': fields.many2one('res.users', 'Users', required=True),
        'account_id': fields.many2one(
            'account.analytic.account', 'Account'),
        'percentual': fields.float('% of hours', required=True,
            digits=(8, 2), help='Percentual on total hour'), 
        'hour': fields.function(
            _get_total_hours, method=True, 
            type='float', string='Tot. H.', store=False, readonly=True), 
        }

class account_analytic_account_invoice(orm.Model):
    ''' Invoice for account
    '''
    _name = 'account.analytic.account.invoice'
    _description = 'Invoice extra for contract'
    _rec_name = 'name'
    
    def extract_excel_status(self, cr, uid, ids, context=None):
        ''' Extract XLS status for intervent for this month and for
            this account analitic
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        
        # Read data from invoice:
        current_proxy = self.browse(cr, uid, ids, context=context)[0]    
        date = current_proxy.date
                
        account_pool = self.pool.get('account.analytic.account')
        return account_pool.extract_excel_status(cr, uid, 
            date[5:7], date[:4],  
            current_proxy.account_id, # browse
            context=context)
        
    _columns = {
        'date': fields.date('Date', required=True),
        'name': fields.char('Invoice ref.', size=40, required=True),
        'hour_removed': fields.float(
            'Hour covered', digits=(16, 2), required=True,            
            help='Number of hours coveder (removed from contract)'), 
        'hour': fields.float(
            'Hour invoiced', digits=(16, 2), required=True,
            help='Number of hours invoiced (sometimes is not all)'), 
        'hour_cost': fields.float('Hour cost', digits=(16, 2),
            help='Number of hours'), 
        'total_amount': fields.float('Total amount', digits=(16, 2)), 

        'account_id': fields.many2one('account.analytic.account', 'Account', 
            required=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        #'date_invoice': fields.related(
        #    'invoice_id', 'date_invoice', 'Invoice date', type='date'),
        #'note': fields.text('Note'),
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
