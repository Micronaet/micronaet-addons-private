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


class ProductProduct(orm.Model):
    """ Model name: Stock move
    """    
    _inherit = 'product.product'
    
    _columns = {
        'standard_price_date': fields.date('Update Date', 
            help='Update date for standard price'),
        }

class StockMove(orm.Model):
    """ Model name: Stock move
    """    
    _inherit = 'stock.move'
    _order = 'id'

class StockMove(orm.Model):
    """ Model name: StockMove
    """
    
    _inherit = 'stock.move'
    
    def _get_subtotal_total(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = move.price_unit * move.product_uom_qty
        return res
    
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
    
    _columns = {
        'subtotal': fields.function(
            _get_subtotal_total, method=True, 
            type='float', string='Subtotal', 
            ),

        'force_name': fields.text('Force name'),
        'auto_account_out_id': fields.many2one(
            'account.analytic.account', 'Account',
            help='This will create auto picking out document',
            ),
        }       

class StockQuants(orm.Model):
    """ Model name: Stock Quants
    """    
    _inherit = 'stock.quant'
        
    _columns = {
         'stock_move_id': fields.many2one('stock.move', 'Generator move'),
         }

class StockPickingManual(orm.Model):
    """ Model name: Stock Picking Manual
    """
    
    _inherit = 'res.company'
    
    _columns = {
         'manual_picking_type_id': fields.many2one(
             'stock.picking.type', 'Picking type customer'),         
         'manual_picking_type_in_id': fields.many2one(
             'stock.picking.type', 'Picking type supplier'),         
         }

class StockPicking(orm.Model):
    ''' Model name: StockPicking
    '''    
    _inherit = 'stock.picking'
    _order = 'name desc'

    # -------------------------------------------------------------------------
    # On change
    # -------------------------------------------------------------------------
    def onchange_picking_partner_filter(self, cr, uid, ids, 
            partner_id, account_no_parent, context=None):
        ''' On change partner and check box
        '''
        if account_no_parent:
            domain = [
                ('type', 'in', ['normal', 'contract']),
                ('state', '!=', 'close'),
                ('partner_id', '=', False),
                ]
        else:        
            domain = [
                ('type', 'in', ['normal', 'contract']),
                ('state', '!=', 'close'),
                ('partner_id', '=', partner_id)
                ]
        return {'domain': {'account_id': domain, }}
        
    # -------------------------------------------------------------------------
    # Button
    # -------------------------------------------------------------------------
    def update_standard_price_product(self, cr, uid, ids, context=None):
        ''' Update standard price on product if date passed
        '''
        product_pool = self.pool.get('product.product')
        
        picking = self.browse(cr, uid, ids, context=context)[0]
        
        # No cost update for out document:
        if picking.pick_move != 'in':
            return True 
            
        picking_date = (picking.min_date or picking.date or '')[:10]
        if not picking_date:
            raise osv.except_osv(
                _('Error'), 
                _('No date in picking document'),
                )
        
        for move in picking.move_lines:
            standard_price = move.price_unit
            if not standard_price:
                continue
            product = move.product_id
            
            # -----------------------------------------------------------------
            # Update price:
            # -----------------------------------------------------------------
            product_date = product.standard_price_date
            
            if not product_date or picking_date > product_date:
                # If better date:
                product_pool.write(cr, uid, product.id, {
                    'standard_price': standard_price,
                    'standard_price_date': picking_date,
                    }, context=context)
        return True

    def generate_pick_out_draft(self, cr, uid, ids, context=None):
        ''' Create pick out document depend on account analytic
        '''
        # Pool used:
        company_pool = self.pool.get('res.company')
        picking_pool = self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')
        
        type_pool = self.pool.get('stock.picking.type')

        # ---------------------------------------------------------------------
        # Parameters:
        # ---------------------------------------------------------------------
        company_id = company_pool.search(cr, uid, [], context=context)[0]
        now = ('%s' % datetime.now())[:19]

        # Type ID:
        type_ids = type_pool.search(cr, uid, [
            ('code', '=', 'outgoing'),
            ], context=context)
        if not type_ids:
            raise osv.except_osv(
                _('Error'), 
                _('Need setup of outgoing stock.picking.type!'),
                )    
        picking_type = type_pool.browse(cr, uid, type_ids, context=context)[0]
        location_id = picking_type.default_location_src_id.id
        location_dest_id = picking_type.default_location_dest_id.id
        
        pick_proxy = self.browse(cr, uid, ids, context=context)[0]        
        test = [
            True for item in pick_proxy.move_lines \
                if item.auto_account_out_id.id]

        if not test:
            raise osv.except_osv(
                _('Error'), 
                _('Picking without auto account!'),
                )
        pickings = {}
        for move in pick_proxy.move_lines:
            pick_orig = move.picking_id
            account = move.auto_account_out_id
            if not account:
                continue # No creation

            partner = account.partner_id
            origin = pick_orig.name
            product = move.product_id

            if account not in pickings:
                pickings[account] = picking_pool.create(cr, uid, {
                    'partner_id': partner.id,
                    'account_id': account.id,
                    'date': now,
                    'min_date': now,
                    'origin': origin, # Origin as an extra info                    
                    'picking_type_id': picking_type.id,
                    'pick_move': 'out',
                    'pick_state': 'todo',
                    'auto_generator_id': pick_orig.id,
                    #'state': 'delivered', # XXX not real!
                    }, context=context)
            picking_id = pickings[account]
            
            move_pool.create(cr, uid, {
                'name': move.name,
                'product_uom': move.product_uom.id,
                'picking_id': picking_id,
                'picking_type_id': picking_type.id,
                'origin': origin,
                'product_id': product.id,
                'product_uom_qty': move.product_uom_qty,
                'date': now,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                #'state': 'done',
                }, context=context)
                
        #model_pool = self.pool.get('ir.model.data')
        # model_pool.get_object_reference('module_name', 'view_name')[1]
        view_id = False

        # TODO put in close status !!!
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pick created'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'res_id': 1,
            'res_model': 'stock.picking',
            'view_id': view_id, # False
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', pickings.values())],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }
    
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
        if context is None:
            context = {}

        move_sign = -1 # default = out
        location_eval = 'move.location_id.id'
        if context.get('fast_picking') and context.get('fast_move') == 'in':
            move_sign = +1
            location_eval = 'move.location_dest_id.id'

        # Pool used:
        quant_pool = self.pool.get('stock.quant')

        for picking in self.browse(cr, uid, picking_ids, context=context):
            for move in picking.move_lines:                        
                # Create quants:
                quant_pool.create(cr, uid, {
                     'stock_move_id': move.id,
                     'qty': move_sign * move.product_qty,
                     # XXX Move price or current product price for cost:
                     'cost': move.price_unit or move.product_id.standard_price,
                     'location_id': eval(location_eval),#move.location_id.id,
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
        return quant_pool.unlink(cr, uid, quant_ids, context=context)    
        
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
        
        self.update_standard_price_product(cr, uid, ids, context=context)
        
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
    def get_default_picking_move(self, cr, uid, context=None):
        ''' Update default depend on context data        
        '''
        if context is None:
            return False

        if context.get('fast_picking') and context.get('fast_move') == 'in':
            return 'in'
        return 'out' # default

    def get_default_picking_type_id(self, cr, uid, context=None):
        ''' Update default depend on context data        
        '''
        if context is None:
            return False

        if context.get('fast_picking'): 
            company_pool = self.pool.get('res.company')
            company_ids = company_pool.search(cr, uid, [], context=context)
            if context.get('fast_move') == 'in':
                return company_pool.browse(
                    cr, uid, company_ids, 
                    context=context)[0].manual_picking_type_in_id.id
            else: # default 'out'
                return company_pool.browse(
                    cr, uid, company_ids, 
                    context=context)[0].manual_picking_type_id.id
        return False
    
    _columns = {
        'verified': fields.boolean('Verified'),
        'contact_id': fields.many2one(
            'res.partner', 'Contact', help='Partner contact for information'),
        'auto_generator_id': fields.many2one(
            'stock.picking', 'Auto generator pick in'),
        'account_id': fields.many2one(
            'account.analytic.account', 'Account'),
        'account_no_parent': fields.boolean('Account without partner'),
        'pick_state': fields.selection([
            ('todo', 'To do'),
            ('ready', 'Ready'),
            ('delivered', 'Delivered'),
            ], 'Picking state'),
        'pick_move': fields.selection([
            ('in', 'Move IN'),
            ('out', 'Move OUT'),
            ], 'Pick move'),
        }

    _defaults = {
        'pick_state': lambda *x: 'todo',
        'picking_type_id': lambda s, cr, uid, ctx: 
            s.get_default_picking_type_id(cr, uid, ctx),
        'pick_move': lambda s, cr, uid, ctx: 
            s.get_default_picking_move(cr, uid, ctx),
        }

class StockPicking(orm.Model):
    ''' Model name: StockPicking
    '''    
    _inherit = 'stock.picking'
    
    _columns = {
        'corresponding': fields.boolean('Corresponding'),
        'auto_child_ids': fields.one2many(
            'stock.picking', 'auto_generator_id', 'Auto Child out'),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
