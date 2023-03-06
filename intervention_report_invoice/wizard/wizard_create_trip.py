# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2004-2012 Micronaet srl. All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import pdb
import sys
import logging
import openerp
import xlsxwriter
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from osv import fields, osv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


class account_invoice_intervent_wizard(osv.osv_memory):
    """ Wizard:
        Create invoice and link intervent list for print report
        Create XLSX report for sent intervent list
    """
    _name = 'account.invoice.intervent.wizard'
    _xls_format_db = {}

    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def get_xls_format(self, mode, WB=None, num_format='#,##0.00'):
        """ Database for format cells
            first call is with mode not present and WB pased
            next call with only mode
        """
        # if not present generate database for format:
        #if not mode or not self._xls_format_db:
        self._xls_format_db = {
            'title' : WB.add_format({
                'bold': True,
                'font_name': 'Courier 10 pitch', # 'Arial'
                'font_size': 11,
                'align': 'left',
                }),
            'header': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'font_name': 'Courier 10 pitch', # 'Arial'
                'font_size': 9,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#cfcfcf', # gray
                'border': 1,
                #'text_wrap': True,
                }),
            'text': WB.add_format({
                'font_color': 'black',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                }),
            'text_total': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'right',
                'border': 0,
                }),
            'text_center': WB.add_format({
                'font_color': 'black',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'center',
                'border': 1,
                }),

            # -------------------------------------------------------------
            # With text color:
            # -------------------------------------------------------------
            'bg_red': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'bg_color': '#ff420e',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                }),
            'bg_green': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'bg_color': '#99cc66',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                }),
            'bg_order': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'bg_color': '#cc9900',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'right',
                'border': 1,
                'num_format': num_format,
                }),

            # -------------------------------------------------------------
            # With text color:
            # -------------------------------------------------------------
            'text_black': WB.add_format({
                'font_color': 'black',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                'text_wrap': True
                }),
            'text_blue': WB.add_format({
                'font_color': 'blue',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                'text_wrap': True
                }),
            'text_red': WB.add_format({
                'font_color': '#ff420e',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                'text_wrap': True
                }),
            'text_green': WB.add_format({
                'font_color': '#328238', ##99cc66
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                'text_wrap': True
                }),

            'text_grey': WB.add_format({
                'font_color': '#eeeeee',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                }),
            'text_wrap': WB.add_format({
                'font_color': 'black',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                'text_wrap': True,
                }),

            'text_bg_yellow': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'bg_color': '#ffff99',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'border': 1,
                }),

            'number': WB.add_format({
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'right',
                'border': 1,
                'num_format': num_format,
                }),
            'number_blue': WB.add_format({
                'font_color': 'blue',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'right',
                'border': 1,
                'num_format': num_format,
                }),
            'text_total': WB.add_format({
                'bold': True,
                'font_color': 'black',
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'left',
                'bg_color': '#DDDDDD',
                'border': 1,
                #'text_wrap': True,
                }),
            'number_total': WB.add_format({
                'bold': True,
                'font_name': 'Courier 10 pitch',
                'font_size': 9,
                'align': 'right',
                'bg_color': '#DDDDDD',
                'border': 1,
                'num_format': num_format,
                }),
            }
        return self._xls_format_db.get(mode, False)

    def write_xlsx_line(self, WS, row, line, format_default=False):
        """ Write cell, the row
        """
        col = -1
        for item in line:
            col += 1
            format_type = format_default # use default
            if type(item) in (tuple, list):
                if len(item) == 2: # case: (value, format)
                    value, format_type = item
                else: # case: (value) >> use default format
                    value = item[0]
            else: # case: value >> use default format
                value = item
            if format_type:
                WS.write(row, col, value, format_type)
            else:
                WS.write(row, col, value)
        return True

    def extra_from_to(self, year, month):
        """ Extrat from to date from year month
        """
        # Generate month filter:
        next_month = int(month) + 1
        next_year = int(year)
        if next_month == 13:
            next_month = 1
            next_year += 1

        return (
            '%s-%s-01' % (year, month),
            '%s-%02d-01' % (next_year, next_month),
            )

    # -------------------------------------------------------------------------
    # Onchange:
    # -------------------------------------------------------------------------
    def onchange_date_search_invoice(self, cr, uid, ids, month, year,
            context=None):
        """ Set domain depend on filter
        """
        res = {}
        res['domain'] = {}

        from_date, to_date = self.extra_from_to(year, month)

        # Set domain for invoice:
        res['domain']['invoice_id'] = [
            ('date_invoice', '>=', from_date),
            ('date_invoice', '<', to_date),
            ]
        return res

    # -------------------------------------------------------------------------
    #                           BUTTON FUNCTION:
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    #                           STATISTIC MONTH:
    # -------------------------------------------------------------------------
    def create_month_statistic(self, cr, uid, ids, context=None):
        """ Statistic for month and invoice status
        """
        # Pool used:
        account_pool = self.pool.get('account.analytic.account')
        intervent_pool = self.pool.get('hr.analytic.timesheet')

        # Read paremeters:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]

        month = wiz_proxy.month
        year = wiz_proxy.year
        user_id = wiz_proxy.user_id.id
        mode = wiz_proxy.mode

        filename = '~/Scrivania/statistic_%s_%s.xlsx' % (
            wiz_proxy.year,
            wiz_proxy.month,
            )
        filename = os.path.expanduser(filename)
        _logger.info('Export filename: %s' % filename)

        WB = xlsxwriter.Workbook(filename)
        WS = WB.add_worksheet('Statistica %s-%s' % (
            wiz_proxy.year,
            wiz_proxy.month,
            ))
        WS_all = WB.add_worksheet('Dettaglio')

        # ---------------------------------------------------------------------
        # 0. Set column dimension:
        # ---------------------------------------------------------------------
        WS.set_column('A:A', 20)

        WS_all.set_column('A:A', 20)

        # ---------------------------------------------------------------------
        #                         1. Header title:
        # ---------------------------------------------------------------------
        format_header = self.get_xls_format('header', WB)
        self.write_xlsx_line(
            WS, 0, [
                u'Cliente',
                u'Commessa',
                u'Dati commessa', # XXX explode in columns
                u'Utente',
                u'H.',
                u'Fabb. H.',
                u'Scost.',
                u'Subtotale',
                ], format_header)

        self.write_xlsx_line(
            WS_all, 0, [
                u'Cliente',
                u'Conto Analitico',
                u'Utente',
                u'Numero commessa',
                u'Richiesta',
                u'Data inizio',
                u'Viaggio',
                u'Pausa',
                u'Durata',
                u'Totale manuale',
                u'Subtotale',
                ], format_header)

        # ---------------------------------------------------------------------
        #                      2. Table: list of intervent
        # ---------------------------------------------------------------------
        intervent_db = {}
        from_date, to_date = self.extra_from_to(year, month)

        # ---------------------------------
        # Search all analytic account open:
        # ---------------------------------
        account_ids = account_pool.search(cr, uid, [
            # TODO Filter only active
            ], context=context)
        for account in account_pool.browse(cr, uid, account_ids,
                context=context):
            intervent_db[account] = {}

        # -----------------------------------------------------
        # Search all intervent to be invoiced and collect data:
        # -----------------------------------------------------
        format_text = self.get_xls_format('text', WB)

        # Generate domain for period:
        domain = [
            ('date_start', '>=', '%s 00:00:00' % from_date),
            ('date_start', '<', '%s 00:00:00' % to_date),
            ]
        if user_id:
            domain.append(('user_id', '=', user_id))

        intervent_ids = intervent_pool.search(cr, uid, domain, context=context)

        row_all = 0
        for intervent in sorted(intervent_pool.browse(cr, uid, intervent_ids,
                context=context), key=lambda x: (
                    x.intervent_partner_id.name if \
                        x.intervent_partner_id else False,
                    x.account_id.name,
                    x.user_id.name,
                    #x.ref,
                    x.date_start,
                    )):
            row_all += 1
            account = intervent.account_id
            user = intervent.user_id

            # 1. Write detail
            total = intervent_pool.get_total_h_2_invoice(intervent)

            self.write_xlsx_line(
                WS_all, row_all, [
                    intervent.intervent_partner_id.name,
                    account.name,
                    intervent.user_id.name,
                    intervent.ref,
                    intervent.intervention_request,
                    intervent.date_start,
                    #intervent.mode,
                    intervent.trip_hour if intervent.trip_require \
                        else '/',
                    intervent.break_hour if intervent.break_require \
                        else '/',

                    intervent.intervent_duration, # total intervent
                    intervent.intervent_total, # manual
                    total,
                    ], format_text)

            # Collect data:
            if account not in intervent_db:
                _logger.warning('Account was closed: %s' % account.name)
                intervent_db[account] = {}
            if mode == 'summary':
                if '/' in intervent_db[account]:
                    intervent_db[account]['/'] += total
                else:
                    intervent_db[account]['/'] = total
            else: # 'detaued'
                if user in intervent_db[account]:
                    intervent_db[account][user] += total
                else:
                    intervent_db[account][user] = total

            # Populate database:


            #intervent_db[intervent.account_id]

        # ----------------
        # Generate report:
        # ----------------
        row = 0
        for account in sorted(intervent_db,
                key=lambda x: (
                    x.partner_id.name if x.partner_id else False,
                    x.name,
                    )):
            for user in intervent_db[account]:
                row += 1
                self.write_xlsx_line(
                    WS, row, [
                        account.partner_id.name,
                        account.name,
                        u'Dati commessa',
                        user if mode == 'summary' else user.name,
                        intervent_db[account][user],
                        u'Fabb. H.',
                        u'Scost.',
                        u'Subtotale',
                        ], format_text)

        # End operations:
        WB.close()
        return True

    # -------------------------------------------------------------------------
    #                           INTERVENT LIST:
    # -------------------------------------------------------------------------
    # Utility:
    def get_wizard_invoices(self, cr, uid, ids, context=None):
        """ Generate domain list
        """
        invoice_pool = self.pool.get('account.invoice')

        # Read parameters:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]

        year = wiz_proxy.year
        month = wiz_proxy.month
        invoice_id = wiz_proxy.invoice_id.id

        if invoice_id:
            invoice_ids = [invoice_id]
        else:
            from_date, to_date = self.extra_from_to(year, month)
            invoice_ids = invoice_pool.search(cr, uid, [
                ('date_invoice', '>=', from_date),
                ('date_invoice', '<', to_date),
                ], context=context)

        invoices = invoice_pool.browse(
            cr, uid, invoice_ids, context=context)
        return invoices

    # ODT:
    def create_intervent_list_odt(self, cr, uid, ids, context=None):
        """ Create list as ODT
        """
        import xmlrpclib
        import time
        import base64

        if context is None:
            context = {}

        user_pool = self.pool.get('res.users')
        user_proxy = user_pool.browse(cr, uid, uid, context=context)

        # Parameters from wizard:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        year = wiz_proxy.year
        month = wiz_proxy.month

        path = os.path.expanduser(
            '~/filestore/samba/detail/%s_%s' % (year, month))
        try:
            os.system('mkdir -p %s' % path)
        except:
            _logger.error('Cannot create detail folder: %s' % path)

        # Invoice loop:
        invoices = self.get_wizard_invoices(cr, uid, ids, context=context)

        # XMLRPC Parameters:
        db = cr.dbname
        uid = uid
        pwd = user_proxy.password
        model = 'account.invoice'
        report_name = 'invoice_intervent_report_list'
        pdb.set_trace()
        for invoice in invoices:
            invoice_id = invoice.id
            invoice_ids = [invoice_id]

            printsock = xmlrpclib.ServerProxy(
                'http://localhost:8069/xmlrpc/report')

            datas = {
                'ids': invoice_ids,
                'record_ids': invoice_ids,
                'model': model,
                'active_model': model,
                'active_id': invoice_id,
                'active_ids': invoice_ids,
            }

            action = {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,  # TODO one for all??

                # 'report_type': 'pdf',
                'model': model,

                'datas': datas,
                }

            id_report = printsock.report(
                db, uid, pwd, report_name, ids, action)
            _logger.warning('Printing report ID %s' % id_report)
            time.sleep(2)

            _logger.warning('Printing report id: %s' % id_report)
            report = printsock.report_get(db, uid, pwd, id_report)
            result = base64.decodestring(report['result'])

            # Generate file:
            filename = 'Dettaglio_%s-%s_%s.odt' % (
                month,
                year,
                invoice.partner_id.name.replace('"', ''),
            )
            fullname = os.path.join(
                path,
                filename,
            )

            file_odt = open(fullname, 'wb')
            file_odt.write(result)
            file_odt.close()
            os.system('chmod 777 %s' % fullname)
        return True

    # XLSX:
    def create_intervent_list(self, cr, uid, ids, context=None):
        """ Create list of intervent depend on selection
        """
        # Generate ODF file
        self.create_intervent_list_odt(cr, uid, ids, context=context)

        # Generate XLSX file:
        # Pool used:
        intervent_pool = self.pool.get('hr.analytic.timesheet')
        invoices = self.get_wizard_invoices(cr, uid, ids, context=context)

        # Parameters:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        year = wiz_proxy.year
        month = wiz_proxy.month

        smb_root = '~/filestore/samba/intervent/%s_%s' % (year, month)
        smb_root = os.path.expanduser(smb_root)
        try:
            os.system('mkdir -p %s' % smb_root)
        except:
            _logger.error('Cannot create folder: %s' % smb_root)

        for invoice in invoices:

            # -----------------------------------------------------------------
            # Open file XLSX:
            # -----------------------------------------------------------------
            name = invoice.partner_id.name if invoice.partner_id else 'Manca'
            filename = os.path.join(smb_root, 'Interventi_%s.xlsx' % name)
            WB = xlsxwriter.Workbook(filename)

            # Format used:
            format_title = self.get_xls_format('title', WB)
            format_header = self.get_xls_format('header', WB)
            format_text = self.get_xls_format('text', WB)
            format_text_total = self.get_xls_format('text_total', WB)
            format_center = self.get_xls_format('text_center', WB)
            format_number = self.get_xls_format('number', WB)

            # -----------------------------------------------------------------
            # 0. Set column dimension:
            # -----------------------------------------------------------------
            # Sheet Intervent:
            WS = WB.add_worksheet('Interventi %s-%s' % (year, month))
            WS.set_column('A:A', 30)
            WS.set_column('C:C', 20)
            WS.set_column('D:D', 30)
            WS.set_column('E:E', 15)
            WS.set_column('F:F', 30)  # Subject
            WS.set_column('G:G', 30)  # Description
            WS.set_column('H:H', 15)
            WS.set_column('I:I', 15)
            # 4 col standard

            # Sheet Contract:
            WS_c = WB.add_worksheet('Contratti %s-%s' % (year, month))
            WS_c.set_column('A:A', 30)
            WS_c.set_column('B:B', 10)
            WS_c.set_column('C:C', 20)
            WS_c.set_column('D:D', 10)
            WS_c.set_column('E:E', 10)
            WS_c.set_column('F:F', 10)

            # XXX WS.merge_range(row, 0, row, 12, '') # merge cell

            # -----------------------------------------------------------------
            # 1. Partner header:
            # -----------------------------------------------------------------
            # WS.write_rich_string(row, col, *record)
            # Sheet Intervent:
            self.write_xlsx_line(WS, 0, [
                u'Interventi (dettaglio): %s' % name,
                ], format_title)

            # Sheet Contract:
            self.write_xlsx_line(WS_c, 0, [
                u'Contratti (sommario): %s' % name,
                ], format_title)

            # -----------------------------------------------------------------
            # 2. Header title:
            # -----------------------------------------------------------------
            # Sheet Intervent:
            self.write_xlsx_line(
                WS, 2, [
                    u'Commessa',
                    u'Num.',
                    u'Data',
                    u'Richiesta',
                    u'Tecnico',
                    u'Oggetto',
                    u'Dettaglio',
                    u'Modalita\'',
                    u'Fatturabile',
                    u'Traferta',
                    u'Pausa',
                    u'Effettivo',
                    u'Fatturato',
                    ], format_header)

            # Sheet Contract:
            self.write_xlsx_line(
                WS_c, 2, [
                    u'Commessa',
                    u'Num.',
                    u'Responsabile',
                    u'Dalla data',
                    u'Alla data',
                    u'Fatturato',
                    ], format_header)

            # -----------------------------------------------------------------
            # 3. Table: list of intervent
            # -----------------------------------------------------------------
            row = 2
            res = {}
            final_total = 0.0
            for intervent in invoice.intervention_report_ids:
                row += 1
                request = intervent.intervention_request or ''
                total = intervent_pool.get_total_h_2_invoice(
                    intervent)
                final_total += total
                if request == 'Nuovo evento':
                    request = intervent.name
                self.write_xlsx_line(
                    WS, row, [
                        intervent.account_id.name,
                        (intervent.ref, format_center),
                        (intervent.date_start, format_center),  # todo better!
                        intervent.intervention_request,
                        intervent.user_id.name,
                        request,
                        intervent.intervention,
                        (intervent.mode, format_center),
                        (intervent.to_invoice.name, format_center),
                        (intervent.trip_hour if intervent.trip_require \
                            else '/', format_number),
                        (intervent.break_hour if intervent.break_require \
                            else '/', format_number),
                        (intervent.intervent_total, format_number),
                        (total, format_number),
                        ], format_text)
                if intervent.account_id not in res:
                    res[intervent.account_id] = total
                else:
                    res[intervent.account_id] += total

            # Write total
            self.write_xlsx_line(
                WS, row + 1, [
                    u'', u'', u'', u'', u'', u'', u'', u'', u'', u'',
                    ('Totale', format_text_total),
                    (final_total, format_text_total),
                    ], format_text_total)
            # WS.write_formula(row + 1, 10, 'SUM(), format_text_total)

            # Summary mode need write after total:
            row = 2
            for account in sorted(res, key=lambda x: x.name):
                row += 1
                self.write_xlsx_line(
                    WS_c, row, [
                        account.name,
                        account.code,
                        account.manager_id.name or '',
                        account.from_date or '',
                        account.to_date or '',
                        (res[account], format_number),
                        ], format_text)
            # End operations:
            WB.close()

        # File zip with folder: # todo
        # Return ZIP file # todo
        return True

    def create_invoice(self, cr, uid, ids, context=None):
        """ Create trip for chosen month for all partner in the list
        """
        domain = [
            ('intervent_partner_id', '!=', False),
            ('extra_planned', '=', False),
            ]

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]

        domain.append(
            ('date_start', '>=', '%s-%s-01 00:00:00' % (
                wiz_proxy.year, wiz_proxy.month)))

        intervent_pool = self.pool.get('hr.analytic.timesheet')
        invoice_pool = self.pool.get('account.invoice')

        intervent_ids = intervent_pool.search(
            cr, uid, domain, order='partner_id,date_start', context=context)
        intervent_proxy = intervent_pool.browse(
            cr, uid, intervent_ids, context=context)
        partner_invoice = {} # partner_id : invoice_id
        for intervent in intervent_proxy: #loop all intervent
            # test if <= end of month
            if intervent.date_start[5:7] != wiz_proxy.month:
                continue
            partner = intervent.intervent_partner_id
            if partner.id not in partner_invoice:
                invoice_ids = invoice_pool.search(cr, uid, [
                    ('partner_id','=', partner.id),
                    ('date_invoice', '=', '%s-01' % (
                        intervent.date_start[:7])),
                    ], context=context)
                if invoice_ids:
                    partner_invoice[partner.id] = \
                        invoice_ids[0]
                else:
                    partner_invoice[partner.id] = \
                        invoice_pool.create(cr, uid, {
                            'name': partner.name,
                            #wiz_proxy.month,wiz_proxy.year) ,
                            'date_invoice': '%s-01' % (
                                intervent.date_start[:7]),
                            'partner_id': partner.id,
                            'account_id': \
                                partner.property_account_receivable.id,
                            }, context=context)

            mod = intervent_pool.write(cr, uid, intervent.id, {
                'invoice_id': partner_invoice[partner.id],
                }, context=context)
        return True

    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'user_id': fields.many2one('res.users', 'User'),
        'year': fields.integer('Year', required=True),
        'mode': fields.selection([
            ('summary', 'Summary'),
            ('detailed', 'Detailed'),
            ], 'Mode', required=True),

        'month': fields.selection([
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
            ],'Month', select=True, required=True),
        }

    _defaults = {
        'year': lambda *a:int(datetime.now().strftime('%Y')),
        'month': lambda *a: '%02d' % (
            int(datetime.now().strftime('%m')) - 1) if \
                datetime.now().strftime('%m') != '01' else '12',
        'mode': lambda *x: 'summary',
        }
account_invoice_intervent_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
