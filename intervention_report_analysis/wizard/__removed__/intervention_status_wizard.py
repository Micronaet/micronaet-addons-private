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
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class intervention_status_wizard(osv.osv_memory):
    ''' Parameter to setup before reporting
    '''    
    _name = 'hr.intervent.wizard'
    _description = 'Intervention analysis wizard'

    def action_print(self, cr, uid, ids, context=None):
        ''' Redirect to bom report passing parameters
        ''' 
        wiz_proxy = self.browse(cr, uid, ids)[0]

        datas = {}
        datas['detailed'] = wiz_proxy.detailed
        datas['from_date'] = wiz_proxy.from_date
        datas['to_date'] = wiz_proxy.to_date
        datas['user_id'] = wiz_proxy.user_id.id or False
        datas['partner_id'] = wiz_proxy.partner_id.id or False

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'intervent_status_report',#'webkitinterventstatus',
            'datas': datas,
            }
        
    _columns = {
        'from_date': fields.date('From date >=', required=True),
        'to_date': fields.date('To date <', required=True),
        'user_id': fields.many2one('res.users', 'User'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'detailed': fields.boolean('Detailed'),
        }
        
    _defaults = {
        'from_date': lambda *x: (datetime.now() - timedelta(days=30)).strftime(
            '%Y-%m-01'),
        'to_date': lambda *x: datetime.now().strftime('%Y-%m-01'),
        'detailed': lambda *x: True,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
