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
import base64
import xlrd
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


class AccountAnalyticAccountInvoiceXLSXImport(orm.TransientModel):
    ''' Wizard for import XLSX file for restore data
    '''
    _name = 'account.analytic.account.invoice.xlsx.import'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_import(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        if context is None: 
            context = {}        
        
        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        
        # Pool used:
        ts_pool = self.pool.get('hr.analytic.timesheet')
        # ---------------------------------------------------------------------
        # Save file passed:
        # ---------------------------------------------------------------------
        if not wiz_browse.xls_file:
            raise osv.except_osv(
                _('No file:'), 
                _('Please pass a XLSX file for import data'),
                )
        b64_file = base64.decodestring(wiz_browse.xls_file)
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        filename = '/tmp/TS_%s.xlsx' % now.replace(':', '_').replace('-', '_')
        f = open(filename, 'wb')
        f.write(b64_file)
        f.close()

        # ---------------------------------------------------------------------
        # Load force name (for web publish)
        # ---------------------------------------------------------------------
        # Parameters:    
        row_start = 1
        try:
            WB = xlrd.open_workbook(filename)
        except:
            raise osv.except_osv(
                _('Error XLSX'), 
                _('Cannot read XLS file: %s' % filename),
                )
        WS = WB.sheet_by_index(0)

        res = []
        for row in range(row_start, WS.nrows):
            try:
                item_id = int(WS.cell(row, 0).value)
            except:
                continue # jump not float lines    
            extra_invoiced_total = WS.cell(row, 9).value
            if extra_invoiced_total and item_id:
                ts_pool.write(cr, uid, item_id, {
                    'extra_invoiced_total': extra_invoiced_total,
                    }, context=context)
                res.append(item_id)
        
        model_pool = self.pool.get('ir.model.data')
        view_tree_id = model_pool.get_object_reference(cr, uid, 
            'intervention_report', 'view_hr_analytic_timesheet_tree')[1]
        view_form_id = model_pool.get_object_reference(cr, uid, 
            'intervention_report', 'view_hr_analytic_timesheet_form')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Updated intervent'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'res_id': 1,
            'res_model': 'hr.analytic.timesheet',
            'view_id': view_tree_id,
            'views': [(view_tree_id, 'tree'), (view_form_id, 'form')],
            'domain': [('id', 'in', res)],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }

    _columns = {
        'xls_file': fields.binary('XLSX file', filters=None),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


