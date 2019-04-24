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

class FastStockPickingReturnet(orm.Model):
    """ Model name: Fast Stock Picking
    """
    _name = 'fast.stock.picking.returned'
    _description = 'Fast picking wizard'
    _rec_name = 'partner_id'

    # -------------------------------------------------------------------------
    # Button
    # -------------------------------------------------------------------------
    def report_original_picking(self, cr, uid, ids, context=None):
        ''' Report mode button
        '''
        if context is None:
            context = {}
        context['report_mode'] = True
        return self.update_original_picking(cr, uid, ids, context=context)
        
    def update_original_picking(self, cr, uid, ids, context=None):
        ''' Force update picking active
        '''
        if context is None:
            context = {}
        report_mode = context.get('report_mode', False)    
        
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
            product = line.product_id
            if product not in remove_db:
                remove_db[product] = line.product_qty

        # ---------------------------------------------------------------------
        # Picking to clean DB:
        # ---------------------------------------------------------------------        
        picking_ids = picking_pool.search(cr, uid, [
            #('ddt_id.is_invoiced', '=', False), # Not invoiced DDT
            ('partner_id', '=', partner_id),
            ('account_id', '=', account_id),
            ('pick_move', '=', 'out'), # only out document
            ('pick_state', '=', 'delivered'), # only delivered
            ], context=context)

        clean_db = {} # Database used to clean data:        
        # picking_id: (move_id, new_qty, previous_qty)
        for picking in sorted(
                picking_pool.browse(cr, uid, picking_ids, context=context),
                key=lambda x: x.create_date):              
                  
            # Test if needed DDT:                    
            if not with_ddt and picking.ddt_id:
                continue # Jump

            # Invoiced:    
            if picking.ddt_id and picking.ddt_id.is_invoiced:
                continue # Jump
            
            for move in picking.move_lines:
                product = move.product_id
                product_qty = move.product_uom_qty
                
                if product not in remove_db:
                    continue # Product not used

                remove_qty = remove_db[product]
                if not remove_qty:
                    continue  # yet removed
                    
                if remove_qty <= product_qty: # remove all
                    new_qty = product_qty - remove_qty
                    remove_db[product] = 0 # No more removing
                else:
                    new_qty = 0 # used all
                    remove_db[product] -= product_qty # pick q. used
                
                # Mark new picking (for unlock procedure)    
                if picking not in clean_db:
                    clean_db[picking] = []
                    
                clean_db[picking].append((
                    move, 
                    new_qty, 
                    ))

        # ---------------------------------------------------------------------
        # Update procedure:
        # ---------------------------------------------------------------------        
        if report_mode:
            # Create WS:
            ws_name = 'Reso cantiere'            
            excel_pool.create_worksheet(name=ws_name)
            
            # Format:
            excel_pool.set_format()
            f_title = excel_pool.get_format('title')
            f_header = excel_pool.get_format('header')
            f_text_black = excel_pool.get_format('text')
            f_text_red = excel_pool.get_format('text_red')
            f_number_black = excel_pool.get_format('number')
            f_number_red = excel_pool.get_format('number_red')

            excel_pool.column_width(ws_name, [
                20, 20, 20, 30, 10, 10, 5])
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
                'Canc.',
                ], default_format=f_header)
            
        for picking in clean_db:
            picking_id = picking.id
            
            # Unlock picking and remove stock movement:
            if not report_mode:
                picking_pool.pickwf_restart(cr, uid, [picking_id],             
                    context=context)
                
            # Update movement:    
            for record in clean_db[picking]:            
                move, new_qty = record
                move_id = move.id

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
                        (move.product_uom_qty, f_number), 
                        (new_qty, f_number),
                        '' if new_qty else 'X',
                        ], default_format=f_text)

            # Lock pickin (and generate stock movements)
            if not report_mode:
                picking_pool.pickwf_delivered(cr, uid, [picking_id], 
                    context=context)                
        
        # ---------------------------------------------------------------------
        # Check remain:
        # ---------------------------------------------------------------------
        remain = False
        for product in remove_db:
            if remove_db[product]:
                remain = True 
                break
                    
        if report_mode:
            # -----------------------------------------------------------------
            # Add remain page if present:
            # -----------------------------------------------------------------
            if remain:
                # Create WS:
                ws_name = 'Errate'
                excel_pool.create_worksheet(name=ws_name)
                
                # Format:
                excel_pool.set_format()

                excel_pool.column_width(ws_name, [
                    20, 40, 10])
                row = 0
                excel_pool.write_xls_line(ws_name, row, [
                    'Prodotti non trovati nei DDT confermati (non fatturati)',
                    ], default_format=f_title)

                row += 1
                excel_pool.write_xls_line(ws_name, row, [
                    'Codice',
                    'Nome',
                    'Residuo', 
                    ], default_format=f_header)
                for product in remove_db:
                    row += 1
                    excel_pool.write_xls_line(ws_name, row, [
                        product.default_code,
                        product.name,
                        remove_db[product], 
                        ], default_format=f_text_black)
        
            # -----------------------------------------------------------------
            # Add page with all material delivered:
            # -----------------------------------------------------------------
            move_ids = move_pool.search(cr, uid, [
                ('picking_id.partner_id', '=', partner_id),
                ('picking_id.account_id', '=', account_id),
                ('picking_id.pick_move', '=', 'out'), # only out document
                ('product_id', 'in', [item.id for item in remove_db])
                ], context=context)
            
            # Create WS:
            ws_name = 'Tutte le consegne'
            excel_pool.create_worksheet(name=ws_name)
            
            excel_pool.column_width(ws_name, [
                20, 20, 20, 30, 10, 20, 30, 10, 10])
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                'Elenco ti tutti i movimenti con i prodotti selezionati',
                ], default_format=f_title)

            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                'Data',            
                'Picking',
                'Stato', 
                'DDT', 
                'Fatturato',
                'Codice',
                'Prodotto',
                'Q.',
                'Modo',
                ], default_format=f_header)
            
            move_proxy = sorted(
                move_pool.browse(cr, uid, move_ids, context=context),
                key=lambda x: (
                    x.product_id.default_code, 
                    x.picking_id.date,
                    ))

            for move in move_proxy:
                # -------------------------------------------------------------        
                # Readability:
                # -------------------------------------------------------------        
                picking = move.picking_id
                ddt = picking.ddt_id
                product = move.product_id
                pick_move = picking.pick_move

                if pick_move == 'out':
                    f_text = f_text_black
                    f_number = f_number_black
                else:    
                    f_text = f_text_red
                    f_number = f_number_red

                row += 1
                excel_pool.write_xls_line(ws_name, row, [
                    picking.date,
                    picking.name,
                    picking.pick_state, 
                    ddt.name if ddt else '/', 
                    'X' if ddt.is_invoiced else '',
                    product.default_code or '',
                    product.name,
                    (move.product_uom_qty, f_number),
                    picking.pick_move,
                    ], default_format=f_text)
            
            if report_mode:
                # Report format red (delete row)
                f_text = f_text_red
                f_number = f_number_red
            
            return excel_pool.return_attachment(cr, uid, 'Reso_Cantiere')   
        else:
            if remain:
                raise osv.except_osv(
                    _('Unload error'), 
                    _('There are remain q. to unload!'),
                    ) 

        # ---------------------------------------------------------------------
        # Delete current refund document and subline:
        # ---------------------------------------------------------------------
        picking_ids = [item.id for item in clean_db]    
        # model_pool = self.pool.get('ir.model.data')
        # model_pool.get_object_reference('module_name', 'view_name')[1]
        view_id = False
        
        # Marked as done:
        self.write(cr, uid, ids, {
            'done': True,
            }, context=context)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Picking modificati'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'res_id': 1,
            'res_model': 'stock.picking',
            'view_id': False,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', picking_ids)],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }           

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
            required=True),
        #'account_no_parent': fields.boolean('Account without partner'),        
        'with_ddt': fields.boolean('With DDT', 
            help='Update also picking with DDT number (not invoiced)'),        
        'done': fields.boolean('Done'),
        }

class FastStockMoveReturned(orm.Model):
    """ Model name: Fast Stock Move Returned
    """
    
    _name = 'fast.stock.move.returned'
    _description = 'Fast move wizard'
    _rec_name = 'product_id'

    _columns = {
        'picking_id': fields.many2one(
            'fast.stock.picking.returned', 'Picking', ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Product'),
        'product_qty': fields.float('Q.', digits=(16, 2)),
        }
        
class FastStockPicking(orm.Model):
    """ Model name: Fast Stock Picking
    """
    _inherit = 'fast.stock.picking.returned'
    
    _columns = {
        'move_lines': fields.one2many(
            'fast.stock.move.returned', 'picking_id', 'Detail'),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
