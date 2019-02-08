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

class FastStockPicking(orm.TransientModel):
    """ Model name: Fast Stock Picking
    """
    _name = 'fast.stock.picking.wizard'
    _description = 'Fast picking wizard'
    _rec_name = 'partner_id'

    # -------------------------------------------------------------------------
    # Button
    # -------------------------------------------------------------------------
    def report_original_picking(self, cr, uid, ids, context=None):
        ''' Report mode button
        '''
        if context in None:
            context = {}
        context['report_mode'] = True
        return self.update_original_picking(cr, uid, ids, context=context)
        
    def update_original_picking(self, cr, uid, ids, context=None):
        ''' Force update picking active
        '''
        if context in None:
            context = {}
        report_mode = context.get('report_move', False)    
        
        picking_pool = self.pool.get('stock.picking')
        excel_pool = self.pool.get('excel.writer')
        move_pool = self.pool.get('stock.move')
        
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        # ---------------------------------------------------------------------
        # Wizard parameters:
        # ---------------------------------------------------------------------
        partner_id = current_proxy.partner_id.id
        account_id = current_proxy.account_id.id
        with_ddt = current_proxy.with_ddt
        
        # ---------------------------------------------------------------------
        # Line product to clean:
        # ---------------------------------------------------------------------
        remove_db = {}
        for line in current_proxy.move_lines:
            product_id = line.product_id.id
            if product_id not in remove_db:
                remove_db[product_id] = line.product_qty

        # ---------------------------------------------------------------------
        # Picking to clean DB:
        # ---------------------------------------------------------------------        
        picking_ids = picking_pool.search(cr, uid, [
            ('ddt_id.is_invoiced', '=', False), # Not invoiced DDT
            ('partner_id', '=', partner_id),
            ('account_id', '=', account_id),
            ], context=context)

        clean_db = [] # Database used to clean data:        
        # picking_id: (move_id, new_qty, previous_qty)
        
        for picking in picking_pool.browse(cr, uid, picking_ids, 
                context=context):                
            # Test if needed DDT:                    
            if not with_ddt and picking.ddt_id:
                continue # Jump
            
            for line in picking.move_lines:
                product_id = line.product_id.id
                product_qty = line.product_uom_qty
                if product_id not in remove_db:
                    continue # Product not used
                remove_qty = remove_db[product_id]
                if not remove_qty:
                    continue  # yet removed
                    
                if remove_qty <= product_qty: # remove all
                    new_qty = product_qty - remove_qty
                    remove_db[product_id] = 0 # No more removing
                else:
                    new_qty = 0 # used all
                    remove_db[product_id] -= product_qty # pick q. used
                
                # Mark new picking (for unlock procedure)    
                if picking not in clead_db:
                    clead_db[picking] = []
                    
                clean_db[picking].append((
                    move, 
                    new_qty, 
                    ))

        # ---------------------------------------------------------------------
        # Update procedure:
        # ---------------------------------------------------------------------        
        if report_move:
            # Create WS:
            ws_name = 'Reso cantiere'            
            excel_pool.create_worksheet(name=ws_name)
            
            # Format:
            excel_pool.set_format()
            f_title = excel_pool.get_format('title')
            f_title = excel_pool.get_format('header')
            f_text_black = excel_pool.get_format('text')
            f_text_red = excel_pool.get_format('text_red')
            f_number_black = excel_pool.get_format('number')
            f_number_red = excel_pool.get_format('number_red')
            
            excel_pool.column_width([
                20, 20, 20, 30, 5, 5, 2])
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                'Correzioni effettuate sui picking di carico',
                ], default_format=f_title)

            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                'Picking',
                'DDT', 
                'Codice',
                'Prodotto',
                'Q. prec.', 
                'Q. nuova',
                'Eliminata',
                ], default_format=f_title)
            
        for picking in clean_db:
            picking_id = picking.id
            
            # Unlock picking and remove stock movement:
            if not report_mode:
                picking_pool.pickwk_restart(cr, uid, [picking_id],             
                    context=context)
                
            # Update movement:    
            for record in clean_db[picking_id]:            
                move, new_qty = record
                if new_qty <= 0: # remove movement
                    if report_mode:
                        # Report format red (delete row)
                        f_text = f_text_red
                        f_number = f_number_red
                    else:    
                        move_pool.unlink(cr, uid, [move_id], context=context)
                else:
                    if report_mode:
                        # Report format black (not delete row)
                        f_text = f_text_black
                        f_number = f_number_black
                    else:    
                        move_pool.write(cr, uid, [move_id], {
                            'product_uom_qty': new_qty,
                            }, context=context)

                # Print line:
                if report_mode:
                    row += 1
                    excel_pool.write_xls_line(ws_name, row, [
                        picking.name,
                        picking.ddt_id.name or '/', 
                        move.product_id.default_code,
                        move.product_id.name,
                        move.product_uom_qty, 
                        new_qty,
                        'X' if new_qty else '',
                        ], default_format=f_text)

            # Lock pickin (and generate stock movements)
            if not report_mode:
                picking_pool.pickwk_delivered(cr, uid, [picking_ids],             
                    context=context)                
        return True        

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
        
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'account_id': fields.many2one('account.analytic.account', 'Account',
            return=True),
        #'account_no_parent': fields.boolean('Account without partner'),        
        'with_ddt': fields.boolean('With DDT', 
            help='Update also picking with DDT number (not invoiced)'),        
        }

class FastStockMove(orm.TransientModel):
    """ Model name: Fast Stock Move
    """
    
    _name = 'fast.stock.move.wizard'
    _description = 'Fast move wizard'
    _rec_name = 'product_id'

    _columns = {
        'picking_id': fields.many2one('fast.stock.picking', 'Picking'),
        'product_id': fields.many2one('product.product', 'Product'),
        'product_qty': fields.boolean('Q.'),
        }
        
class FastStockPicking(orm.TransientModel):
    """ Model name: Fast Stock Picking
    """
    _inherit = 'fast.stock.picking.wizard'
    
    _columns = {
        'move_lines': fields.one2many(
            'fast.stock.move.wizard', 'picking_id', 'Detail'),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
