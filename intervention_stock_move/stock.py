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


class StockPickingManual(orm.Model):
    """ Model name: Stock Picking Manual
    """
    
    _name = 'stock.picking.manual'
    _description = 'Stock picking manual'
    _rec_name = 'name'
    _order = 'name'
    
    # -------------------------------------------------------------------------
    # WF Button:
    # -------------------------------------------------------------------------
    def wf_ready(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # TODO movement and picking!
        self.write(cr, uid, ids, {
            'state': 'ready',
            }, context=context)

    def wf_delivered(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # TODO movement and picking!
        self.write(cr, uid, ids, {
            'state': 'delivered',
            }, context=context)

    def wf_restart(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # TODO movement and picking!
        self.write(cr, uid, ids, {
            'state': 'todo',
            }, context=context)

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def dummy_button(self, cr, uid, ids, context=None):
        ''' Refresh
        '''
        return True
        
    def remove_to_intervention(self, cr, uid, ids, context=None):
        ''' Link to intervention
        '''
        if context is None:
            raise osv.except_osv(
                _('No context'), 
                _('Error passing data'),
                )
        intervention_id = context.get('intervention_id')
        self.write(cr, uid, ids, {
            'intervention_id': False,
            }, context=context)
        return {'tag': 'reload'}
        
    def add_to_intervention(self, cr, uid, ids, context=None):
        ''' Link to intervention
        '''
        if context is None:
            raise osv.except_osv(
                _('No context'), 
                _('Error passing data'),
                )
        intervention_id = context.get('intervention_id')
        self.write(cr, uid, ids, {
            'intervention_id': intervention_id,
            }, context=context)
        return {'tag': 'reload'}

    _columns = {
        'name': fields.char('Number', size=25),#TODO , required=True),
        'date': fields.date('Date', required=True),
        'planned_date': fields.date('Planned date'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', required=True),
        'address_id': fields.many2one('res.partner', 'Address'),
        'origin': fields.char('Origin', size=40),
        'note': fields.char('Note'),	        
        'intervention_id': fields.many2one(
            'hr.analytic.timesheet', 'Intervention'),
        'state': fields.selection([
            ('todo', 'To do'),
            ('ready', 'Ready'),
            ('delivered', 'Delivered'),
            ], 'Picking state')
        }

    _defaults = {
        'state': lambda *x: 'todo',
        }

class StockMoveManual(orm.Model):
    """ Model name: StockMoveManual
    """
    
    _name = 'stock.move.manual'
    _description = 'Stock move manual'
    _rec_name = 'product_id'
    _order = 'product_id'
    
    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product', required=True),            
        'intervention_id': fields.many2one(
            'hr.analytic.timesheet', 'Intervention'),
        'product_uom_qty': fields.float('Q.ty', digits=(16, 3), required=True),
        'uom_id': fields.related(
            'product_id', 'uom_id', 
            type='many2one', relation='product.uom', 
            string='UOM'),
        'picking_id': fields.many2one(
            'stock.picking.manual', 'Picking'),

        #'state': fields.selection([
        #    ('todo', 'To do'),
        #    ('ready', 'Ready'),
        #    ('delivered', 'Delivered'),
        #    ], 'Picking state')
        'state': fields.related(
            'picking_id', 'state', 
            type='selection', selection=[
                ('todo', 'To do'),
                ('ready', 'Ready'),
                ('delivered', 'Delivered'),
                ] , string='State', readonly=True),
        }

    _defaults = {
        #'state': lambda *x: 'todo',
        }

class StockPickingManual(orm.Model):
    """ Model name: Stock Picking Manual
    """
    
    _inherit = 'stock.picking.manual'
    
    _columns = {
        'line_ids': fields.one2many(
            'stock.move.manual', 'picking_id', 
            'Line'),
        }

class HrAnalyticTimesheet(orm.Model):
    ''' Add extra data for delivery
    '''
    _inherit = 'hr.analytic.timesheet'

    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def make_and_confirm_picking(self, cr, uid, ids, context=None):
        ''' Confirm picking when confirmed or create one
        '''
        pick_pool = self.pool.get('stock.picking.manual')
        
        # Create picking if material is present:
        self.create_picking(cr, uid, ids, context=context)

        # Confirm Picking delivery:
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        pick_ids = [pick.id for pick in current_proxy.picking_ids]
        pick_pool.write(cr, uid, pick_ids, {
            'state': 'delivered',
            }, context=context)
        return True    
        
    # -------------------------------------------------------------------------
    # Override WF:
    # -------------------------------------------------------------------------
    def intervention_confirmed(self, cr, uid, ids, context=None):
        ''' Confirm picking when confirmed or create one
        '''
        self.make_and_confirm_picking(cr, uid, ids, context=context)
        
        return super(HrAnalyticTimesheet, self).intervention_confirmed(
            cr, uid, ids, context=context)

    def intervention_close(self, cr, uid, ids, context=None):
        ''' Confirm picking when close or create one
        '''
        self.make_and_confirm_picking(cr, uid, ids, context=context)
        
        return super(HrAnalyticTimesheet, self).intervention_close(
            cr, uid, ids, context=context)

        
    def _get_partner_delivery_picking(
            self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        current_proxy = self.browse(cr, uid, ids, context=context)[0]        
        partner_id = current_proxy.intervent_partner_id.id
        pick_pool = self.pool.get('stock.picking.manual')
        res[ids[0]] = pick_pool.search(cr, uid, [
            ('partner_id', '=', partner_id),
            ('state', 'in', ('todo', 'ready')),
            ('intervention_id', '=', False),            
            ], context=context)
        return res

    def create_picking(self, cr, uid, ids, context=None): 
        ''' Create picking and link to intervent
        '''
        current_proxy = self.browse(cr, uid, ids, context=context)[0]

        # Pool used:        
        move_pool = self.pool.get('stock.move.manual')        
        pick_pool = self.pool.get('stock.picking.manual')        

        move_ids = [move.id for move in current_proxy.delivered_ids]    
        if not move_ids: # Nothing to do
            return True
            
        pick_id = pick_pool.create(cr, uid, {
            'partner_id': current_proxy.intervent_partner_id.id,
            'date': current_proxy.date_start,
            'planned_date': current_proxy.date_start,
            'name': '',
            'address_id': False,
            'origin': 'Intervent',
            'note': False,
            'intervention_id': current_proxy.id,
            'state': 'ready',            
            }, context=context)
            
        # Unlock movement from intervent:    
        move_pool.write(cr, uid, move_ids, {
            'intervention_id': False,
            'picking_id': pick_id,
            }, context=context)
        return True
        
    _columns = {
        'delivered_ids': fields.one2many(
            'stock.move.manual', 'intervention_id', 
            'Delivered'),
        'picking_ids': fields.one2many(
            'stock.picking.manual', 'intervention_id', 
            'Picking'),

        'todo_ids': fields.function(
            _get_partner_delivery_picking, method=True, 
            type='many2many', relation='stock.picking.manual', 
            string='Delivery available', store=False),                   
        }

"""
class StockPicking(orm.Model):
    ''' Model name: StockPicking
    '''    
    _inherit = 'stock.picking'
    
    
    def remove_to_intervention(self, cr, uid, ids, context=None):
        ''' Link to intervention
        '''
        if context is None:
            raise osv.except_osv(
                _('No context'), 
                _('Error passing data'),
                )
        intervention_id = context.get('intervention_id')
        self.write(cr, uid, ids, {
            'intervention_id': False,
            }, context=context)
        return {'tag': 'reload'}
        
    def add_to_intervention(self, cr, uid, ids, context=None):
        ''' Link to intervention
        '''
        if context is None:
            raise osv.except_osv(
                _('No context'), 
                _('Error passing data'),
                )
        intervention_id = context.get('intervention_id')
        self.write(cr, uid, ids, {
            'intervention_id': intervention_id,
            }, context=context)
        return {'tag': 'reload'}

    # Second WF Button:
    def pickwk_ready(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # TODO movement and picking!
        self.write(cr, uid, ids, {
            'pick_state': 'ready',
            }, context=context)

    def pickwk_delivered(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # TODO movement and picking!
        self.write(cr, uid, ids, {
            'pick_state': 'delivered',
            }, context=context)

    def pickwk_restart(self, cr, uid, ids, context=None):
        ''' Restart procedure
        '''
        # TODO movement and picking!
        self.write(cr, uid, ids, {
            'pick_state': 'todo',
            }, context=context)
        
    _columns = {
        'intervention_id': fields.many2one(
            'hr.analytic.timesheet', 'Intervention'),
        'pick_state': fields.selection([
            ('todo', 'To do'),
            ('ready', 'Ready'),
            ('delivered', 'Delivered'),
            ], 'Picking state')
        }

    _defaults = {
        'pick_state': lambda *x: 'todo',
        }

class HrAnalyticTimesheet(orm.Model):
    ''' Add extra data for delivery
    '''
    _inherit = 'hr.analytic.timesheet'

    def _get_partner_delivery_picking(
            self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        current_proxy = self.browse(cr, uid, ids, context=context)[0]        
        partner_id = current_proxy.intervent_partner_id.id
        pick_pool = self.pool.get('stock.picking')
        res[ids[0]] = pick_pool.search(cr, uid, [
            ('partner_id', '=', partner_id),
            ('pick_state', 'in', ('todo', 'ready')),
            ('intervention_id', '=', False),            
            ], context=context)
        return res

    _columns = {
        'delivered_ids': fields.one2many(
            'stock.picking', 'intervention_id', 
            'Delivered picking'),
        'picking_ids': fields.function(
            _get_partner_delivery_picking, method=True, 
            type='many2many', relation='stock.picking', 
            string='Delivery available', store=False),                         
            
        }"""
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
