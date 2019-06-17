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

class StockPicking(orm.Model):
    """ Model name: StockMove
    """
    
    _inherit = 'stock.picking'
    
    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def split_stock_move(self, cr, uid, ids, context=None):
        ''' Split selected line into another picking
        '''
        picking_id = ids[0]
        move_pool = self.pool.get('stock.move')
        
        move_ids = move_pool.search(cr, uid, [
            ('picking_id', '=', picking_id),
            ('move_selection', '=', True),
            ], context=context)
        if not move_ids:
            raise osv.except_osv(
                _('Error'), 
                _('No line selected'),
                )
                
        picking = self.browse(cr, uid, picking_id, context=context)
        move_to_picking_id = picking.move_to_picking_id.id
        update = True
        if not move_to_picking_id:
            update = False
            now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            move_to_picking_id = self.create(cr, uid, {
                'partner_id': picking.partner_id.id,
                'account_id': picking.account_id.id,
                'date': now,
                'min_date': now,
                'origin': '',
                'picking_type_id': picking.picking_type_id.id,
                'pick_move': 'out',
                'pick_state': 'todo',
                #'auto_generator_id': pick_orig.id,
                #'state': 'delivered', # XXX not real!
                }, context=context)
        
        # Move lines
        move_pool.write(cr, uid, move_ids, {
            'picking_id': move_to_picking_id,
            'move_selection': False, # reset selection
            }, context=context)
            
        if update:
            self.write(cr, uid, ids, {
                'move_to_picking_id': False,
                # TODO update other related fields?
                }, context=context)     
                
        #model_pool = self.pool.get('ir.model.data')
        #view_id = model_pool.get_object_reference('module_name', 'view_name')[1]        
        view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Result for view_name'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_id': move_to_picking_id,
            'res_model': 'stock.picking',
            'view_id': view_id, # False
            'views': [(False, 'form'), (False, 'tree')],
            'domain': [],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }

    _columns = {
        'move_to_picking_id': fields.many2one('stock.picking', 'Move to',
            help='If not selected will be create another picking from this'),
        }

class StockMove(orm.Model):
    """ Model name: StockMove
    """
    
    _inherit = 'stock.move'
    
    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def move_selection_on(self, cr, uid, ids, context=None):
        ''' Move marked ON
        '''
        return self.write(cr, uid, ids, {
            'move_selection': True,
            }, context=context)

    def move_selection_off(self, cr, uid, ids, context=None):
        ''' Move marked OFF
        '''
        return self.write(cr, uid, ids, {
            'move_selection': False,
            }, context=context)
        
    _columns = {
        'move_selection': fields.boolean('Selected for move'),
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
