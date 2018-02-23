# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class hr_analytic_timesheet(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'
    
    def _get_profit(self, cr, uid, ids, fields, args, context=None):
        ''' Return real profit depend on type invoice and invoiced
        '''
        res = {}
        for intervent in self.browse(cr, uid, ids, context=context):
            hour = intervent.intervent_total * intervent.to_invoice.factor / 100.0
            cost = intervent.intervent_partner_id.hour_cost or 0.0
            res[intervent.id] = cost * hour
        return res
        
    _columns = {
        'profit': fields.function(_get_profit, method=True, type='float', 
            string='Profit', store=True), # TODO problems during change hour cost
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
