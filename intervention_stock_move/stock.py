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


"""    def remove_to_intervention(self, cr, uid, ids, context=None):
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


        if current_proxy.state == 'delivered':
            state = 'assigned' #done
        else: # 'todo', 'ready'
            state = 'waiting' # 'assigned'

        move_pool = self.pool.get('stock.move')
        date = current_proxy.date or datetime.now().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        data = {
            'name': current_proxy.product_id.name,
            'product_id': current_proxy.product_id.id,
            'product_uom_qty': current_proxy.product_uom_qty,
            'product_uom': current_proxy.product_id.uom_id.id,
            'partner_id': current_proxy.partner_id.id,            
            'date': date,
            'date_expected': date,
            'origin': _('Manual picking'),
            'picking_id': False, # TODO
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,            
            'state': state,
            #'product_qty': current_proxy.product_uom_qty,
            #'product_uos_qty': current_proxy.product_uom_qty,
            #'product_uos': current_proxy.product_id.uom_id.id,
            #'product_packaging',
            #'producton_id'
            #'price_unit',
            #'priority':,
            #'invoice_state':
            #'procure_method':
            }
        if current_proxy.move_id:
            move_id = current_proxy.move_id.id
            move_pool.write(cr, uid, move_id, {
                'state': 'draft',
                }, context=context)
            
            move_pool.write(cr, uid, move_id, data, context=context)
        else:
            move_id = move_pool.create(cr, uid, data, context=context)        
        # TODO create quants if done movement!!    
        return move_id
"""

class HrAnalyticTimesheetForcePicking(orm.Model):
    ''' Add extra data for delivery
    '''
    _inherit = 'hr.analytic.timesheet'

    # -------------------------------------------------------------------------
    # On Change:
    # -------------------------------------------------------------------------
    """
    TODO loop procedure
    def on_change_partner(self, cr, uid, ids, partner_id, account_id,
            context=None):
        ''' Update alert
        '''
        # Call super procedure:
        ctx = context.copy()
        res = super(HrAnalyticTimesheet, self).on_change_partner(
            cr, uid, ids, partner_id, account_id, context=ctx)
            
        # Update extra data:    
        partner_pool = self.pool.get('res.partner')
        if 'value' not in res:
            res['value'] = {}
        pending_material_present = partner_pool._get_pending_stock_material(
            cr, uid, [partner_id], None, 
            None, context=context)[partner_id]['pending_material_present']
        res['value']['pending_material_present'] = pending_material_present
        return res
    """
    
    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def confirm_also_picking(self, cr, uid, ids, context=None):
        ''' Confirm picking when confirmed or create one
        '''
        pick_pool = self.pool.get('stock.picking')
        
        # Confirm Picking delivery:
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        pick_ids = [pick.id for pick in current_proxy.delivered_ids if \
            pick.pick_state in ('todo', 'ready')]
        
        # Update with WF action:
        if pick_ids:
            _logger.warning('Closed also %s picking' % len(pick_ids))
            return pick_pool.pickwf_delivered(cr, uid, pick_ids, context=context)
        else:
            return True        
    # -------------------------------------------------------------------------
    # Override WF:
    # -------------------------------------------------------------------------
    def intervention_confirmed(self, cr, uid, ids, context=None):
        ''' Confirm picking when confirmed or create one
        '''
        # Confirm also picking:    
        self.confirm_also_picking(cr, uid, ids, context=context)

        return super(HrAnalyticTimesheetForcePicking, self).intervention_confirmed(
            cr, uid, ids, context=context)

    def intervention_close(self, cr, uid, ids, context=None):
        ''' Confirm picking when close or create one
        '''
        # Confirm also picking:    
        self.confirm_also_picking(cr, uid, ids, context=context)

        return super(HrAnalyticTimesheetForcePicking, self).intervention_close(
            cr, uid, ids, context=context)
        
    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def link_all_delivery_pending(self, cr, uid, ids, context=None):
        ''' Link all pending delivery:
        '''
        # Pool used:
        picking_pool = self.pool.get('stock.picking')

        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        partner_id = current_proxy.intervent_partner_id.id
        
        picking_ids = picking_pool.search(cr, uid, [
            ('pick_state', 'in', ('todo', 'ready')), # in status to delivery
            ('partner_id', '=', partner_id), # with selected partner
            ('intervention_id', '=', False), # not linked
            ], context=context)
        if not picking_ids:
            return True

        return picking_pool.write(cr, uid, picking_ids, {
            'intervention_id': ids[0],
            }, context=context)    
       
    def dummy_button(self, cr, uid, ids, context=None):
        ''' Refresh
        '''
        return True

    #def _get_partner_delivery_picking(
    #        self, cr, uid, ids, fields, args, context=None):
    #    ''' Fields function for calculate 
    #    '''
    #    res = {}
    #    current_proxy = self.browse(cr, uid, ids, context=context)[0]        
    #    partner_id = current_proxy.intervent_partner_id.id
    #    pick_pool = self.pool.get('stock.picking.manual')
    #    res[ids[0]] = pick_pool.search(cr, uid, [
    #        ('partner_id', '=', partner_id),
    #        ('state', 'in', ('todo', 'ready')),
    #        ('intervention_id', '=', False),            
    #        ], context=context)
    #    return res

    def create_picking(self, cr, uid, ids, context=None): 
        ''' Create picking and link to intervent
        '''
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        model_pool = self.pool.get('ir.model.data')
        form_id = model_pool.get_object_reference(
            cr, uid,
            'stock', 'view_picking_form')[1]
        ctx = context.copy()
        ctx.update({
            'default_partner_id': current_proxy.intervent_partner_id.id,
            'default_intervention_id': current_proxy.id,
            'fast_picking': True,
            'default_account_id': current_proxy.account_id.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': _('New picking'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            #'res_id': 1,
            'res_model': 'stock.picking',
            'view_id': form_id, # False
            'views': [(form_id, 'form'), (False, 'tree')],
            'domain': [],
            'context': ctx,
            'target': 'new',
            'nodestroy': False,
            }

        # Pool used:        
        """
        current_proxy = self.browse(cr, uid, ids, context=context)[0]

        move_pool = self.pool.get('stock.move')     
        pick_pool = self.pool.get('stock.picking')

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
        """
        
    _columns = {
        'delivered_ids': fields.one2many(
            'stock.move.manual', 'intervention_id', 
            'Delivered'),
        'picking_ids': fields.one2many(
            'stock.picking.manual', 'intervention_id', 
            'Picking'),

        #'todo_ids': fields.function(
        #    _get_partner_delivery_picking, method=True, 
        #    type='many2many', relation='stock.picking.manual', 
        #    string='Delivery available', store=False),                   
        'delivery_present': fields.char('Delivery present', size=64),
        'pending_material_present': fields.related(
            'intervent_partner_id', 'pending_material_present', 
            type='boolean', string='Pending material present'),
        'pending_material_detail': fields.related(
            'intervent_partner_id', 'pending_material_detail', 
            type='char', size=80, string='Pending material detail'),
        }

    _defaults = {
        'delivery_present': lambda *x: _('PENDING DELIVERY')
        }

class ResPartner(orm.Model):
    """ Model name: Res Partner
    """
    
    _inherit = 'res.partner'

    def _get_pending_stock_material(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Fields function for calculate 
        '''
        # Pool used:
        picking_pool = self.pool.get('stock.picking')

        # Prepare empty database for partner
        partner_db = {}
        for item in ids:
            partner_db[item] = [0, 0] # todo, ready status counter
        
        picking_ids = picking_pool.search(cr, uid, [
            ('pick_state', 'in', ('todo', 'ready')), # in status to delivery
            ('partner_id', 'in', ids), # with selected partner
            ('intervention_id', '=', False), # not linked
            ], context=context)

        for picking in picking_pool.browse(cr, uid, picking_ids, 
                context=context):    
            if picking.pick_state == 'todo':
                partner_db[picking.partner_id.id][0] += 1
            elif picking.pick_state == 'ready':   
                partner_db[picking.partner_id.id][1] += 1
            else:
                pass # nothing

        res = {}
        for partner_id in partner_db:
            res[partner_id] = {
                'pending_material_present': any(partner_db[partner_id]),
                'pending_material_detail': _(
                    'TODO: %s - Ready: %s') % tuple(partner_db[partner_id]),
                }
        return res
        
    _columns = {
        'pending_material_present': fields.function(
            _get_pending_stock_material, method=True, 
            type='boolean', string='Pending material', store=False, 
            multi=True),                         
        'pending_material_detail': fields.function(
            _get_pending_stock_material, method=True, 
            type='char', size=80, string='Pending material detail', 
            store=False, multi=True),
        }


class StockPicking(orm.Model):
    ''' Model name: StockPicking
    '''    
    _inherit = 'stock.picking'
    
    def unlink_picking(self, cr, uid, ids, context=None):
        """ Remove reference for picking
        """        
        self.write(cr, uid, ids, {
            'intervention_id': False,
            }, context=context)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }
        
    # -------------------------------------------------------------------------
    # UTILITY:
    # -------------------------------------------------------------------------
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
        'intervention_id': fields.many2one(
            'hr.analytic.timesheet', 'Intervention'),
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
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
