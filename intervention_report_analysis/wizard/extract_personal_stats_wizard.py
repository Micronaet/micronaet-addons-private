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
        period = to_dt - from_dt
        days = period.days() + 1 # start day

        # Account period:
        account_from_dt = datetime.strptime(
            account.from_date, DEFAULT_SERVER_DATE_FORMAT)
        account_to_dt = datetime.strptime(
            account.to_date, DEFAULT_SERVER_DATE_FORMAT)
        account_period = to_dt - from_dt
        account_days = period.days() + 1 # start day
        
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
                todo = self.get_account_distribution(
                    user_id, from_date, to_date, account)
                if user_id and user_id not in [
                        item.id for item in account.distribution_ids]:
                    continue
                res[account] = [0.0, todo]
        
        # ---------------------------------------------------------------------        
        # Collect statistics:
        # ---------------------------------------------------------------------        
        ts_ids = ts_pool.search(cr, uid, domain, context=context)
        for intervent in ts_pool.browse(cr, uid, ts_ids, context=context):
            account = intervent.account_id
            if account not in res:
                # Total hour, todo
                res[account] = [0.0, 0.0]
            res[account][0] += intervent.unit_amount # Total hour
            # TODO check to_invoice parameter
        
        WS_name = _('Statistiche')
        excel_pool.create_worksheet(WS_name)

        # ---------------------------------------------------------------------
        #                               EXCEL:
        # ---------------------------------------------------------------------
        # Layout setup:        
        excel_pool.column_width(WS_name, [25, 25, 10, 10])

        # Title:
        excel_pool.write_xls_line(WS_name, 0, [
            'Report dalla data %s alla data %s' % (from_date, to_date),  
            ])
        excel_pool.write_xls_line(WS_name, 1, [
            'Utente: %s Conto: %s Contratti: %s' % (
                user_name, 
                account_name,
                'SI' if contract else 'NO',
                ),
            ])
        
        # Header:
        excel_pool.write_xls_line(WS_name, 2, [
            'Conto analitico', 
            'Cliente',
            'Fabbisogno',
            'Ore fatte', 
            ])
        
        # Write data:
        row = 2
        for account in sorted(
                res, key=lambda x: (0 if res[x][1] else 1, x.name)):
            row += 1    
            data = res[account]
            excel_pool.write_xls_line(WS_name, 0, [
                account.name, 
                account.partner_id.name,
                data[1] or '', 
                data[0], 
                ])
        
        return excel_pool.return_attachment(
            cr, uid, 'Statistiche', version='7.0', 
            context=context)

    _columns = {
        'contract': fields.boolean('With contract', 
            help='Always add also contract with distribution'),
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
        'user_id': lambda s, cr, uid, ctx: uid,
        'from_date': lambda *x: datetime.now().strftime('%Y-%m-01'),
        'to_date': lambda *x: (
            datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


