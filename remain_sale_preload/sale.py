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

class SaleOrderLine(orm.Model):
    """ Model name: SaleOrderLine
    """
    
    _inherit = 'sale.order.line'

    def delivery_done(self, cr, uid, ids, context=None):
        """ Update qty arrived in stock move and update remain
        """ 
        line_ids = self.search(cr, uid, [
            ('this_delivery_qty', '>', 0),
            ], context=context)
        for line in self.browse(
                cr, uid, line_ids, context=context):
            delivered_qty = line.delivered_qty
            product_uom_qty = line.product_uom_qty      
                  
            remain_qty = product_uom_qty - delivered_qty            
            this_delivery_qty = line.this_delivery_qty
            
            if this_delivery_qty > remain_qty:
                delivered_qty = product_uom_qty
            else:                
                delivered_qty = delivered_qty + this_delivery_qty
            # TODO Generate stock move
                
                
            self.write(cr, uid, [line.id], {
                'completed': 
                    delivered_qty + this_delivery_qty >= product_uom_qty,
                'this_delivery_qty': 0,
                'delivered_qty': delivered_qty,
            }, context=context)
        return True
            
        
    def delivery_remain(self, cr, uid, ids, context=None):
        """ Update remain for this delivery
        """ 
        line = self.browse(cr, uid, ids, context=context)[0]
        remain_qty = line.product_uom_qty - line.delivered_qty
        if remain_qty > 0:
            self.write(cr, uid, ids, {
                'this_delivery_qty': remain_qty,
            }, context=context)
        return True
        
    _columns = {
        'completed': fields.boolean('Completed'),
        'this_delivery_qty': fields.float('This Delivery', digits=(16, 2)),
        'delivered_qty': fields.float('Delivered', digits=(16, 2)),
        'partner_id': fields.related(
            'order_id', 'partner_id', 
            type='many2one', relation='res.partner', string='Partner', 
            store=True),
    }
    

