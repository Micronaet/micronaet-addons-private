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
        })

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
            domain.append(('date', '>=', data['from_date']))
        if data['to_date']:
            domain.append(('date', '<', data['to_date']))

        if data.get('user_id', False):
            domain.append(('user_id', '=', data['user_id']))
        if data.get('partner_id', False):
            domain.append(('partner_id', '=', data['partner_id']))
        int_ids = int_pool.search(self.cr, self.uid, domain)
        
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
