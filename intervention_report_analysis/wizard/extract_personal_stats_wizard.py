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

class HrAnalyticTimesheet(orm.Model):
    """ Model name: Timesheet
    """    
    _inherit = 'hr.analytic.timesheet'
    
    def write_account_list_excel_sheet(self, cr, uid, WS_name, ids, 
            float_time, context=None):
        ''' Write a page of intervents in Excel sheet passed
        '''    
        excel_pool = self.pool.get('excel.writer')

        # ---------------------------------------------------------------------
        #                               EXCEL:
        # ---------------------------------------------------------------------
        # Layout setup:        
        excel_pool.column_width(WS_name, [
            # Intervent header:
            10, 28, 10, 35, 10, 10, 10,
            # Total:
            10, 10, 10, 10, 10, 10,            
            # Description:
            20, 40, 40, 40, 40, 40, 40,
            ])
        
        # ---------------------------------------------------------------------
        # Generate format used:
        # ---------------------------------------------------------------------
        # Text:
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')
        f_text = excel_pool.get_format('text') 
        f_white_number = excel_pool.get_format('bg_white_number') 

        # Title:
        row = 0
        #excel_pool.write_xls_line(WS_name, row, [
        #    'Elenco rapportini contemplati nel periodo',
        #    ], f_title)
        
        # Header:
        #row += 2
        excel_pool.write_xls_line(WS_name, row, [
            # Intervent header information:
            'Numero',
            'Cliente',
            'Tipo conto',
            'Conto analitico',
            'Tipologia',
            'Data',
            'Stato',
            
            # Total:
            'Durata',
            'Manuale',
            'Viaggio', # >> trip_require
            'Pausa', # >> break_require            
            'Totale', # unit_amount
            'Riconosciuto extra', # extra_invoiced_total

            # Description:            
            'Stato fattura',            
            'Oggetto',
            'Richiesto da',
            'Rif. richiesta',
            'Richiesta',
            'Intervento',
            'Note',
            #'Non in report', # not in report
            ], f_header)
        
        # Write data sort by date:        
        for intervent in sorted(self.browse(cr, uid, ids, context=context),
                key=lambda x: (
                    x.intervent_partner_id.name,
                    x.account_id.account_mode,
                    x.account_id.name,
                    x.date_start,
                    )):
            row += 1
            
            if intervent.trip_require:
                trip_hour = intervent.trip_hour 
            else:    
                trip_hour = 0
            if intervent.break_require:
                break_hour = intervent.break_hour 
            else:    
                break_hour = 0
            excel_pool.write_xls_line(WS_name, row, [
                # Intervent header:
                intervent.ref or 'Da confermare',
                intervent.intervent_partner_id.name or ' ',
                intervent.account_id.account_mode or ' ',
                intervent.account_id.name or ' ',
                intervent.mode or ' ',
                intervent.state or ' ',
                excel_pool.format_date(intervent.date_start),
                
                # Total:
                (excel_pool.format_hour(
                    intervent.intervent_duration, float_time), f_white_number),
                (excel_pool.format_hour(
                    intervent.intervent_total, float_time), f_white_number),
                (excel_pool.format_hour(
                    trip_hour, float_time), f_white_number),
                (excel_pool.format_hour(
                    break_hour, float_time), f_white_number),
                (excel_pool.format_hour(
                    intervent.unit_amount, float_time), f_white_number),
                (excel_pool.format_hour(
                    intervent.extra_invoiced_total, float_time), 
                        f_white_number),

                # Description
                '%s [%s%%]' % (
                    intervent.to_invoice.name,
                    intervent.to_invoice.factor,
                    ),
                intervent.name or ' ',
                intervent.request_by or ' ',
                intervent.request_reference or ' ',
                intervent.intervention_request or ' ',
                intervent.intervention or ' ',
                intervent.internal_note or ' ',
                ], f_text)

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
        #                            UTILITY:
        # ---------------------------------------------------------------------
        def sort_order_account_mode(account_mode):
            ''' Order in stat report
            '''
            if account_mode == 'contract':
                return 0
            elif account_mode == 'open':
                return 1
            elif account_mode == 'fixed':
                return 2
            elif account_mode == 'unfixed':
                return 3
            else: # 'internal':
                return 4
            
        if context is None: 
            context = {} 
       
        yellow_rate = 0.9    
        
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
        user = wiz_browse.user_id
        
        account_id = wiz_browse.account_id.id or False    
        account_name = wiz_browse.account_id.name or _('Nessuno')
        
        partner_id = wiz_browse.partner_id.id or False    
        partner_name = wiz_browse.partner_id.name or _('Nessuno')
        
        contract = wiz_browse.contract
        float_time = wiz_browse.float_time
        
        res = {}
        domain = [
            ('account_id.is_extra_report', '=', False),
            ]
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
                ('account_mode', '=', 'contract'), # only contract
                ('distribution_ids', '!=', False), # with distribution
                ('state', 'in', ('draft', 'open')), # active
                ], context=context)         
            for account in account_pool.browse(
                    cr, uid, account_ids, context=context):
                if user_id: # filter (only contract with me in distribution
                    # for user filter check if user is in distribution:
                    todo = account_pool.get_account_distribution(
                        user_id, from_date, to_date, account)
                    if user_id not in [
                            item.user_id.id for item in \
                                account.distribution_ids]:
                        continue
                    # account and user browse obj    
                    res[(account, user)] = [
                        todo,
                        0.0, # done pay
                        0.0, # done gratis
                        0.0, # invoiced                    
                        ]
                else: # no filter, all contract with user in distribution:
                    for perc in account.distribution_ids:
                        select_user = perc.user_id
                        todo = account_pool.get_account_distribution(
                            select_user.id, from_date, to_date, account)
                        res[(account, select_user)] = [
                            todo,
                            0.0, # done pay
                            0.0, # done gratis
                            0.0, # invoiced                    
                            ]
        
        # ---------------------------------------------------------------------        
        # Collect statistics:
        # ---------------------------------------------------------------------        
        medium_type = {}
        invoiced_type = ('open', )
        my_total = 0.0
        ts_ids = ts_pool.search(cr, uid, domain, context=context)
        
        for intervent in ts_pool.browse(cr, uid, ts_ids, context=context):
            account = intervent.account_id
            select_user = intervent.user_id
            key = (account, select_user)
            if key not in res:
                todo = account_pool.get_account_distribution(
                    select_user.id, from_date, to_date, account)
                # Total hour, todo
                res[key] = [
                    todo,
                    0.0, 
                    0.0, 
                    0.0, 
                    ]

            # TODO extra hour in intervent pay!!        
            account_mode = intervent.account_id.account_mode
            if intervent.to_invoice.factor == 100:
                marked_qty = intervent.unit_amount # TODO Change using funct.
                free_qty = 0.0
                
                res[key][1] += marked_qty # Total hour invoiced
                if account_mode in invoiced_type:
                    my_total += marked_qty
                        
            else: # No invoice
                marked_qty = 0.0
                free_qty = intervent.unit_amount # Total hour gratis
                res[key][2] += free_qty

            if account_mode not in medium_type:
                # marked, free
                medium_type[account_mode] = [0.0, 0.0]            
            medium_type[account_mode][0] += marked_qty
            medium_type[account_mode][1] += free_qty

            res[key][3] += intervent.extra_invoiced_total # Extra invoiced
            my_total += intervent.extra_invoiced_total
            
        WS_name = _('Statistiche')
        excel_pool.create_worksheet(WS_name)

        # Write all intervent in second page:
        WS_intervent = _('Interventi')
        excel_pool.create_worksheet(WS_intervent)
        ts_pool.write_account_list_excel_sheet(cr, uid, WS_intervent, ts_ids, 
            float_time, context=context)

        # ---------------------------------------------------------------------
        #                               EXCEL:
        # ---------------------------------------------------------------------
        # Layout setup:        
        column_width = [25, 40, 10, 20, 10, 10]
        if not user_id: # Only for user
            column_width.append(15)  
        column_width.extend([10, 10, 10, 1, 10, 10])
        excel_pool.column_width(WS_name, column_width)
        
        # ---------------------------------------------------------------------
        # Generate format used:
        # ---------------------------------------------------------------------
        # Text:
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')
        f_text = excel_pool.get_format('text') 
        f_red_text = excel_pool.get_format('bg_red') 
        f_yellow_text = excel_pool.get_format('bg_yellow') 
        f_orange_text = excel_pool.get_format('bg_orange')         
        f_green_text = excel_pool.get_format('bg_green') 
        f_blue_text = excel_pool.get_format('bg_blue') 
        
        # Number:
        f_text_right = excel_pool.get_format('text_right') 
        f_white_number = excel_pool.get_format('bg_white_number') 
        f_blue_number = excel_pool.get_format('bg_blue_number') 
        f_red_number = excel_pool.get_format('bg_red_number') 
        f_yellow_number = excel_pool.get_format('bg_yellow_number') 
        f_orange_number = excel_pool.get_format('bg_orange_number') 
        f_green_number = excel_pool.get_format('bg_green_number') 

        # Title:
        row = 0
        excel_pool.write_xls_line(WS_name, row, [
            'Report: Data [%s - %s]' % (
                excel_pool.format_date(from_date), 
                excel_pool.format_date(to_date),
                ),  
            ], f_title)
        row += 1    
        excel_pool.write_xls_line(WS_name, row, [
            'Utente: %s Conto: %s  - Contratti: %s' % (
                user_name, 
                account_name,
                'SI' if contract else 'NO',
                ),
            ], f_title)
        row += 1    
        excel_pool.write_xls_line(WS_name, row, [
            'Totale a pagamento: %s' % excel_pool.format_hour(my_total),
            ], f_title)
        
        # Header:
        row += 2
        header_line = [
            'Cliente',
            'Conto analitico', 
            'Tipo',
            'Periodo',
            'H. parziali',
            'H. contratto',
            ]
        if not user_id: # only if not filter
            header_line.append('Utente')
            
        header_line.extend([    
            'Fabbi. pers.',
            'Ore marcate',             
            'Ore tolte',
            'S', # Status counter
            'Ore fatt.',
            'Riconosciute',
            ])
            
        excel_pool.write_xls_line(WS_name, row, header_line, f_header)
        
        # Write data:
        now = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        total_premium = 0.0
        for key in sorted(
                res, key=lambda x: (
                    sort_order_account_mode(x[0].account_mode),
                    x[0].partner_id.name,
                    x[0].name,
                    )):
            row += 1
            account, select_user = key
            data = res[key]
            
            # Intervent:
            h_todo, h_pay, h_no_pay, h_invoice = data
            h_done = h_pay + h_no_pay
            
            # Account:
            account_from = account.from_date
            account_to = account.to_date
            account_h_todo = account.total_hours
            account_h_done = account.hour_done
            account_mode = account.account_mode 
                        
            # TODO remove invoiced hours from total contract done
            if account_mode in invoiced_type:
                premium = h_pay + h_invoice
            else:    
                premium = h_invoice
            total_premium += premium    
                
            # -----------------------------------------------------------------
            # Color test:
            # -----------------------------------------------------------------
            # Mode:
            if account_mode == 'contract':
                # Not counted (only invoiced)
                mode_format = f_blue_text
                mode_format_value = 'N'
            elif account_mode == 'unfixed':
                # Not counted (depend on invoice monthly)
                mode_format = f_yellow_text
                mode_format_value = '?'
            elif account_mode == 'fixed':
                # Not counted (depend on invoice monthly)
                mode_format = f_orange_text
                mode_format_value = '!'
            elif account_mode == 'open':
                # Counted
                mode_format = f_green_text
                mode_format_value = 'S'
            else:#if account_mode == 'internal':
                # Not counted:
                mode_format = f_text # not red
                mode_format_value = 'N'
                
            # Date period:
            if account_to and account_to < now:
                date_format = f_red_text
            elif account_from and account_from >= now:
                date_format = f_yellow_text                
            else:
                date_format = f_text                
            
            # Account H.:
            if not account_h_todo:
                account_h_format = f_text_right                
            elif account_h_done > account_h_todo:
                account_h_format = f_red_number
            elif account_h_done / account_h_todo >= yellow_rate:
                account_h_format = f_yellow_number
            else:    
                account_h_format = f_green_number            

            # Intervent H.:
            if not h_todo:
                h_format = f_text_right                
            elif h_done > h_todo:
                h_format = f_red_number
            elif h_done / h_todo >= yellow_rate:
                h_format = f_yellow_number
            else:    
                h_format = f_green_number            
            
            data_line = [
                (account.partner_id.name or _('GENERICO'), f_text),
                (account.name, f_text), 
                (account_mode, mode_format),
                ('[%s - %s]' % (
                    excel_pool.format_date(account.from_date), 
                    excel_pool.format_date(account.to_date),
                    ), date_format), 
                (excel_pool.format_hour(account.hour_done, float_time), 
                    account_h_format),
                (excel_pool.format_hour(account.total_hours, float_time), 
                    account_h_format),
                ]
            if not user_id: # no user filter
                data_line.append(
                    (select_user.name or ' ', f_text),
                    )                
            data_line.extend([                
                (excel_pool.format_hour(h_todo, float_time), h_format),
                (excel_pool.format_hour(h_pay, float_time), h_format), 
                (excel_pool.format_hour(h_no_pay, float_time), h_format), 
                (mode_format_value, mode_format),
                excel_pool.format_hour(h_invoice, float_time), 
                excel_pool.format_hour(premium, float_time), 
                ])
            excel_pool.write_xls_line(WS_name, row, data_line, f_text_right)
        
        row += 2
        excel_pool.write_xls_line(WS_name, row, [
            '',
            '',
            '',
            ('Tipologie di contratti', f_header),
            ('H. marcate', f_header),
            ('H. tolte', f_header),
            ])
        
        total_free = total_marked = 0    
        for account_mode in sorted(
                medium_type, 
                key=lambda x: sort_order_account_mode(x)):
            row += 1
            
            marked_qty, free_qty = medium_type[account_mode]
            total_free += free_qty
            total_marked += marked_qty
            
            if account_mode == 'contract':
                text_format = f_blue_text
                number_format = f_blue_number
            elif account_mode == 'unfixed':
                text_format = f_yellow_text
                number_format = f_yellow_number
            elif account_mode == 'fixed':
                text_format = f_orange_text
                number_format = f_orange_number
            elif account_mode == 'open':
                text_format = f_green_text
                number_format = f_green_number
            else:#if account_mode == 'internal':
                text_format = f_text # not red
                number_format = f_white_number

            excel_pool.write_xls_line(WS_name, row, [
                '',
                '',
                '',
                (account_mode, text_format),
                (excel_pool.format_hour(
                    marked_qty, float_time), number_format),
                (excel_pool.format_hour(
                    free_qty, float_time), number_format),
                ])

        row += 2                 
        excel_pool.write_xls_line(WS_name, row, [
            '',
            '',
            '',
            '',
            ('Tot. marcate', f_header),
            ('Tot. tolte', f_header),
            ('Totale fatte', f_header),
            ('Riconosciute', f_header),
            ])
        row += 1    

        excel_pool.write_xls_line(WS_name, row, [
            '',
            '',
            '',
            '',
            (excel_pool.format_hour(
                total_marked), f_white_number),
            (excel_pool.format_hour(
                total_free), f_white_number),
            (excel_pool.format_hour(
                total_marked + total_free), f_white_number),
            (excel_pool.format_hour(
                total_premium), f_white_number),
            ])
            
        return excel_pool.return_attachment(
            cr, uid, 'Statistiche', version='7.0', 
            context=context)

    _columns = {
        'contract': fields.boolean('With contract', 
            help='Always add also contract with distribution'),
        'float_time': fields.boolean('Formatted hour', 
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
        'float_time': lambda *x: True,
        'user_id': lambda s, cr, uid, ctx: uid,
        'from_date': lambda *x: datetime.now().strftime('%Y-%m-01'),
        'to_date': lambda *x: (
            datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
