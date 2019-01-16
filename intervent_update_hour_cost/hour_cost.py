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

class ProductProduct(orm.Model):
    """ Model name: Product product
    """
    
    _inherit = 'product.product'
    
    def update_hr_intervent(self, cr, uid, ids, context=None):
        ''' Update hour cost for this user
        '''
        line_pool = self.pool.get('account.analytic.line')        
        product = self.browse(cr, uid, ids, context=context)[0]
        
        line_ids = line_pool.search(cr, uid, [
            ('product_id', '=', product.id), # This product
            ('date', '>=', product.hr_date), # From update date
            ], context=context)
        
        standard_price = product.standard_price
        _logger.warning('Update %s product with cost: %s [%s]' % (
            len(line_ids),
            standard_price,
            line_ids,
            ))
        for line in line_pool.browse(cr, uid, line_ids, context=context):                
            line_pool.write(cr, uid, line.id, {
                'amount': -(standard_price * line.unit_amount),
                }, context=context)
        return True
        
    _columns = {
        'hr_date': fields.date(
            'HR Date', 
            help='If intervent present will be updated from this date'),            
        }    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
