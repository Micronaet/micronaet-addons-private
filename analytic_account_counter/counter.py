#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class AccountAnalyticAccount(orm.Model):
    """ Model name: AccountAnalyticAccount
    """
    
    _inherit = 'account.analytic.account'
    
    def create(self, cr, uid, vals, context=None):
        """ Create a new record for a model ClassName
            @param cr: cursor to database
            @param uid: id of current user
            @param vals: provides a data for new record
            @param context: context arguments, like lang, time zone
            
            @return: returns a id of new record
        """
        sequence_pool = self.pool.get('ir.sequence')
        counter_mode = vals.get('counter_mode', False)
        code = vals.get('code', False)

        if not code:
            sequence_name = 'account.analytic.account.%s' % counter_mode
            sequence_ids = sequence_pool.search(cr, uid, [
                ('name', '=', sequence_name),
                ], context=context)
            if sequence_ids:                    
                vals['code'] = sequence_pool.next_by_id(
                    cr, uid, sequence_ids[0], context=context)
            else:
                raise osv.except_osv(
                    _('Error'), 
                    _('Counter %s not found' % sequence_name)
                    )

        return super(AccountAnalyticAccount, self).create(
            cr, uid, vals, context=context)
    
    _columns = {
        # Override to change default:
        'code': fields.char(
            'Reference', select=True, track_visibility='onchange', copy=False),
        
        # Extra data:    
        'to_date': fields.date('Deadline'),        
        'counter_mode': fields.selection([
            ('generic', 'Generic'),
            ('manutention', 'Manutention'),
            ('analytic', 'Analytic'),
            ], 'Mode', required=True),
        }

    _defaults = {
        'counter_mode': lambda *x: 'generic',
        'code' : False,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
