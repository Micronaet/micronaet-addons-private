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
import time
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class report_webkit_html(report_sxw.rml_parse):    
    # Global parameter for manage report data:
    partner = {}
    
    def __init__(self, cr, uid, name, context):
        super(report_webkit_html, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'load_data': self._load_data,
            'write_header': self.write_header,
            'write_total': self.write_total,
            'table_start': self.table_start,
            'table_end': self.table_end,
            'dict_operation': self.dict_operation,
        })

    def dict_operation(self, data, value, operation='add'
            #, modify_list=None
            ):
        ''' Dict add value to all keys:
        '''
        #if modify_list is None:
        #    modify_list = ()
            
        for k in data:
            #if modify_list and (k in modify_list):
            if operation == 'add':
                data[k] += value
            elif operation == 'set':   
                data[k] = value
        return 
        
    def table_start(self, header=None):
        ''' Start table element passing header list values
        '''
        if header is None:
            return '<p>#Partner ERR</p><table class="list_table">'
        else:   
            return '''
                <p>%(partner)s</p>
                    <table class="list_table">
                ''' % header
    
    def table_end(self, ):
        ''' End table element
        '''
        return '</table>'
        
    def write_header(self, ):
        ''' Return HTML code for header
        '''        
        return '''
            <tr>
                <th>Tipo</th>
                <th>Conto</th>
                <th>Utente</th>
                <th>Data</th>
                <th>Ore</th>
                <th>Ore totali</th>
                <th>Ore interne</th>
                <th>Viaggio</th>
            </tr>''' # Last 5 cols for value    # <th>Cliente</th>

            
    def write_total(self, total, break_level, header=None, new_table=False):    
        ''' Format and return total HTML table row 
            self: instance object
            break_level: values used are partner, type, account, user 
            total: dict of all totals for every element
        '''
        return '%s%s%s%s%s' % (
            '''
            <tr>
                <td colspan='2'>Totali:</td>
                %s
                <td></td>
                %s
                %s
                %s
                %s
            </tr>''' % ( 
                '<td>%(partner)s - %(type)s - %(account)s</td>' % total[
                    'number'], # - %(user)s
                '<td>%(partner)2.2f - %(type)2.2f - %(account)2.2f' % total[
                    'hour'],
                '<td>%(partner)2.2f - %(type)2.2f - %(account)2.2f' % total[
                    'hour_total'],
                '<td>%(partner)2.2f - %(type)2.2f - %(account)2.2f' % total[
                    'internal'],
                '<td>%(partner)2.2f - %(type)2.2f - %(account)2.2f' % total[
                    'trip'],
                ),
            self.table_end() if new_table else '',
            '<br />'  if new_table else '',
            self.table_start(header) if new_table else '',
            self.write_header() if new_table else '',
            )

    def _load_data(self, data=None):
        ''' Load all data for analytic report
            Search all intervent in period
        '''
        
        # Reset global variables:
        self.partner = {}
        
        # Pool used:
        int_pool = self.pool.get('hr.analytic.timesheet')

        # -------------------------------
        # Search depend on filter domain:
        # -------------------------------
        domain = []
        if data['from_date']:
            domain.append(
                ('date_start', '>=', '%s 00:00:00' % data['from_date']))
        if data['to_date']:
            domain.append(
                ('date_start', '<', '%s 00:00:00' % data['to_date']))

        if data.get('user_id', False):
            domain.append(('user_id', '=', data['user_id']))
        if data.get('partner_id', False):
            domain.append(('partner_id', '=', data['partner_id']))
        int_ids = int_pool.search(
            self.cr, self.uid, domain)
        
        # Start analyse data intervent:
        items = []
        for item in int_pool.browse(self.cr, self.uid, int_ids):
            #if intervention.intervent_partner_id not in self.partner:
            #    self.partner[intervention.intervent_partner_id] = []#{} # user
            #self.partner[intervention.intervent_partner_id].append(
            #    intervention)
            order = ( # key for order elements:
                item.intervent_partner_id.name, # Partner
                'Contratti' if item.account_id.partner_id else 'Generico', # With partner
                item.account_id.name, # Analytic account
                item.user_id.name, # Users
                item.date_start, # Date
                )
            items.append((order, item))
        return sorted(items)            

report_sxw.report_sxw(
    'report.webkitinterventstatus',
    'hr.analytic.timesheet', 
    'addons/intervention_report_analysis/report/status_webkit.mako',
    parser=report_webkit_html
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
