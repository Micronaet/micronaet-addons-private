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

import xlsxwriter
from osv import fields, osv
from datetime import datetime


class account_invoice_intervent_wizard(osv.osv_memory):
    ''' Wizard: 
        Create invoice and link intervent list for print report
        Create XLSX report for sent intervent list
    '''
    _name = 'account.invoice.intervent.wizard'   
    _xls_format_db = {}

    # -------------------------------------------------------------------------
    # Utility:    
    # -------------------------------------------------------------------------
    def get_xls_format(self, mode, WB=None, num_format='#,##0'):  
        ''' Database for format cells
            first call is with mode not present and WB pased
            next call with only mode
        '''
        # if not present generate database for format:
        if not mode or not self._xls_format_db:
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
        ''' Write cell, the row
        '''
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
    
    # -------------------------------------------------------------------------
    # Onchange:
    # -------------------------------------------------------------------------
    def onchange_date_search_invoice(self, cr, uid, ids, month, year,
            context=None):
        ''' Set domain depend on filter
        '''    
        res = {}
        res['domain'] = {}
        
        # Generate month filter:
        next_month = int(month) + 1
        if next_month == 13:
            next_month = 1
        from_date = '%s-%s-01' % (year, month)
        to_date = '%s-%s-01' % (year, next_month)
                
        # Set domain for invoice:        
        res['domain']['invoice_id'] = [
            ('date_invoice', '>=', from_date),
            ('date_invoice', '<', to_date),
            ]
        return res
        
    # -------------------------------------------------------------------------
    # Button function:
    # -------------------------------------------------------------------------
    def create_intervent_list(self, cr, uid, ids, context=None):
        ''' Create list of intervent depend on selection
        ''' 
        # Read paremeters:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        # TODO read parameters:
        
        filename = '/home/thebrush/Scrivania/intervent.xlsx' # TODO change (one per invoice)
        
        WB = xlsxwriter.Workbook(filename)
        WS = WB.add_worksheet('Interventi')
        # ---------------------------------------------------------------------
        # 0. Set column dimension:
        # ---------------------------------------------------------------------
        #WS.set_column('A:A', 19)
        #WS.merge_range(row, 0, row, 12, '') # merge cell

        # ---------------------------------------------------------------------
        # 1. Partner header:
        # ---------------------------------------------------------------------
        #WS.write_rich_string(row, col, *record)
        format_title = self.get_xls_format('title', WB)
        self.write_xlsx_line(
            WS, 0, [
                'Partner:',
                # TODO nome partner
                ], format_title)
        
        # ---------------------------------------------------------------------
        # 2. Header title:
        # ---------------------------------------------------------------------
        format_header = self.get_xls_format('header', WB)
        self.write_xlsx_line(
            WS, 1, [
                u'Commessa',
                u'Num.',
                u'Data', 
                u'Richiesta',
                u'Tecnico',
                u'Oggetto', 
                u'Modalità',
                u'Traferta',
                u'Pausa',
                u'Effettivo',
                u'Fatturato',            
                ], format_header)

        
        # TODO print intervento:
        row = 2
        
        # End operations:
        WB.close()
        return True
        
    def create_invoice(self, cr, uid, ids, context=None):
        ''' Create trip for choosen month for all partner in the list
        '''
        domain = [
            ('intervent_partner_id', '!=', False),
            ('extra_planned', '=', False),
            ]

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        domain.append(
            ('date_start', '>=', '%s-%s-01 00:00:00' % (
                wiz_proxy.year,wiz_proxy.month)))
            
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
        'year': fields.integer('Year', required=True),
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
        }
account_invoice_intervent_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
