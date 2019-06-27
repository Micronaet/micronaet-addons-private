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
    
    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def update_partner_changed(self, cr, uid, ids, context=None):
        ''' Update partner
        '''
        account = self.browse(cr, uid, ids, context=context)[0]
        account_id = account.id
        partner_id = account.partner_id.id

        # Not used:
        # sale_order (no account_id)
        # stock_move (no account_id)        
        # account_move (no account_id)
        # stock_quant (no account_id)
                
        # ---------------------------------------------------------------------
        # Picking:
        # ---------------------------------------------------------------------
        _logger.info('Update partner for picking')
        query = '''
            UPDATE stock_picking
            SET partner_id = %s            
            WHERE account_id = %s and partner_id != %s;
            '''
        cr.execute(query, (partner_id, account_id, partner_id))

        # ---------------------------------------------------------------------
        # Stock DDT:
        # ---------------------------------------------------------------------
        _logger.info('Update partner for DDT')
        query = '''
            UPDATE stock_ddt
            SET partner_id = %s            
            WHERE account_id = %s and partner_id != %s;
            '''
        cr.execute(query, (partner_id, account_id, partner_id))

        # ---------------------------------------------------------------------
        # Stock Manual invoice:
        # ---------------------------------------------------------------------
        _logger.info('Update partner for manual invoice')
        query = '''
            UPDATE manual_account_invoice
            SET partner_id = %s            
            WHERE account_id = %s and partner_id != %s;
            '''
        cr.execute(query, (partner_id, account_id, partner_id))

        # ---------------------------------------------------------------------
        # Stock Manual account move line:
        # ---------------------------------------------------------------------
        _logger.info('Update partner for account move line')
        query = '''
            UPDATE account_move_line
            SET partner_id = %s            
            WHERE account_id = %s and partner_id != %s;
            '''
        cr.execute(query, (partner_id, account_id, partner_id))

        # ---------------------------------------------------------------------
        # Stock Manual Intervent:
        # ---------------------------------------------------------------------
        _logger.info('Update partner for intervent')
        query = '''
            UPDATE hr_analytic_timesheet
            SET partner_id = %s, intervent_partner_id = %s
            WHERE (partner_id != %s OR intervent_partner_id != %s)
                AND line_id in (
                   SELECT id 
                   FROM account_analytic_line 
                   WHERE account_id = %s
                   );
            '''
        cr.execute(query, (
            partner_id, partner_id,
            partner_id, partner_id, 
            account_id, 
            ))
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
