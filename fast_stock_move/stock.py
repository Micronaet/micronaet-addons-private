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


class StockMove(orm.Model):
    """ Model name: Stock move
    """    
    _inherit = 'stock.move'

    def onchange_product_id(self, cr, uid, ids, product_id=False, loc_id=False, 
            loc_dest_id=False, partner_id=False):
        ''' Update price during creation of movement
        '''        
        res = super(StockMove, self).onchange_product_id(
            cr, uid, ids, prod_id=product_id, loc_id=loc_id,
            loc_dest_id=loc_dest_id, partner_id=partner_id)

        if product_id and 'value' in res:
            product_proxy = self.pool.get('product.product').browse(
                cr, uid, product_id)
            res['value']['price_unit'] = product_proxy.standard_price
        return res    

class StockQuants(orm.Model):
    """ Model name: Stock Quants
    """    
    _inherit = 'stock.quant'
    
        
    _columns = {
         'stock_move_id': fields.many2one('stock.move', 'Generator move', 
             ondelete='cascade',
             ),
         }

class StockPickingManual(orm.Model):
    """ Model name: Stock Picking Manual
    """
    
    _inherit = 'res.company'
    
    _columns = {
         'manual_picking_type_id': fields.many2one(
             'stock.picking.type', 'Picking type customer'),         
         }

class StockPicking(orm.Model):
    ''' Model name: StockPicking
    '''    
    _inherit = 'stock.picking'
    
    # -------------------------------------------------------------------------
    # Second WF: Buttons
    # -------------------------------------------------------------------------
    # Utility for update movement:
    def _set_stock_move_picked(self, cr, uid, ids, state, context=None):
        ''' Return list of moved in picking
        '''
        move_pool = self.pool.get('stock.move')
        move_ids = move_pool.search(cr, uid, [
            ('picking_id', 'in', ids),
            ], context=context)
        return move_pool.write(cr, uid, move_ids, {
            'state': state,
            }, context=context)
    
    # Utility for update quants:
    def _create_quants(self, cr, uid, picking_ids, context=None):
        ''' Create quants when done a movement
        '''
        # Pool used:
        quant_pool = self.pool.get('stock.quant')

        for picking in self.browse(cr, uid, picking_ids, context=context):
            for move in picking.move_lines:                        
                # Create quants:
                quant_pool.create(cr, uid, {
                     'stock_move_id': move.id,
                     'qty': -move.product_qty,
                     # XXX Move price or current product price for cost:
                     'cost': move.price_unit or move.product_id.standard_price,
                     'location_id': move.location_id.id,
                     'company_id': move.company_id.id,
                     'product_id': move.product_id.id,
                     'in_date': move.date,
                     #'propagated_from_id'
                     #'package_id'
                     #'lot_id'
                     #'reservation_id'
                     #'owner_id'
                     #'packaging_type_id'
                     #'negative_move_id'
                    }, context=context)
        return True
                    
    def _delete_quants(self, cr, uid, picking_ids, context=None):
        ''' Create quants when done a movement
        '''
        if context is None:  
            context={}
        
        context['force_unlink'] = True # TODO delete quants

        # Pool used:
        quant_pool = self.pool.get('stock.quant')
        quant_ids = quant_pool.search(cr, uid, [
            ('stock_move_id.picking_id', 'in', picking_ids),
            ], context=context)
        return quant_pool.unlink(cr, uid, quant_ids)    
        
        
    def pickwf_ready(self, cr, uid, ids, context=None):
        ''' Restart procedure
            draft, cancel, waiting, confirmed, partially_available, 
            assigned, done
        '''
        # Update stock movement:
        self._set_stock_move_picked(
            cr, uid, ids, state='assigned', context=context)
                    
        # Update picking:
        return self.write(cr, uid, ids, {
            'pick_state': 'ready',
            }, context=context)

    def pickwf_delivered(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # Create quants for stock evaluation:
        self._create_quants(cr, uid, ids, context=context)
        
        # Update stock movement:
        self._set_stock_move_picked(#assigned
            cr, uid, ids, state='done', context=context)
        
        # Update picking:
        return self.write(cr, uid, ids, {
            'pick_state': 'delivered',
            }, context=context)

    def pickwf_restart(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # Create quants for stock evaluation:
        self._delete_quants(cr, uid, ids, context=context)
        
        # Update stock movement:
        self._set_stock_move_picked(
            cr, uid, ids, state='draft', context=context)
        
        # Update picking:
        return self.write(cr, uid, ids, {
            'pick_state': 'todo',
            }, context=context)
        
    # -------------------------------------------------------------------------
    # Default function:
    # -------------------------------------------------------------------------
    def get_default_picking_type_id(self, cr, uid, context=None):
        ''' Update default depend on context data        
        '''
        if context is None:
            return False

        if context.get('fast_picking'): 
            company_pool = self.pool.get('res.company')
            company_ids = company_pool.search(cr, uid, [], context=context)
            return company_pool.browse(
                cr, uid, company_ids, 
                context=context)[0].manual_picking_type_id.id
        return False
    
    _columns = {
        'account_id': fields.many2one(
            'account.analytic.account', 'Account'),
        'pick_state': fields.selection([
            ('todo', 'To do'),
            ('ready', 'Ready'),
            ('delivered', 'Delivered'),
            ], 'Picking state')
        }

    _defaults = {
        'pick_state': lambda *x: 'todo',
        'picking_type_id': lambda s, cr, uid, ctx: 
            s.get_default_picking_type_id(cr, uid, ctx),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
