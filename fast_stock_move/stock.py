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
import pdb
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

    def dummy_save(self, cr, uid, ids, context=None):
        """ Dummy save
        """
        return True

    _columns = {
        'standard_price_date': fields.date(
            'Update Date',
            help='Update date for standard price'),
        }


class StockMove(orm.Model):
    """ Model name: Stock move
    """
    _inherit = 'stock.move'
    _order = 'id'

    def dummy_save(self, cr, uid, ids, context=None):
        """ Dummy save
        """
        return True

    def open_product_print_detail(self, cr, uid, ids, context=None):
        """ Open product form (extra data form movement)
        """
        model_pool = self.pool.get('ir.model.data')
        view_id = model_pool.get_object_reference(
            cr, uid,
            'fast_stock_move', 'view_stock_picking_report_note_form'
            )[1]

        move_proxy = self.browse(cr, uid, ids, context=context)[0]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dettaaglio per stampa'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ids[0],
            'res_model': 'stock.move',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'domain': [('id', '=', ids[0])],
            'context': context,
            'target': 'new',
            'nodestroy': False,
            }

    def open_product_movement(self, cr, uid, ids, context=None):
        """ Open product form
        """
        # model_pool = self.pool.get('ir.model.data')
        # view_id = model_pool.get_object_reference('module_name', 'view_name')[1]
        move_proxy = self.browse(cr, uid, ids, context=context)[0]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Movimenti prodotto'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_id': False,
            'res_model': 'stock.move',
            'view_id': False,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('product_id', '=', move_proxy.product_id.id)],
            'context': context,
            'target': 'current',  # 'new'
            'nodestroy': False,
            }

    def open_product_form(self, cr, uid, ids, context=None):
        """ Open product form
        """
        if context is None:
            context = {}
        context['popup_mode'] = True
        # model_pool = self.pool.get('ir.model.data')
        # view_id = model_pool.get_object_reference(
        # 'module_name', 'view_name')[1]
        move_proxy = self.browse(cr, uid, ids, context=context)[0]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotto'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_id': move_proxy.product_id.id,
            'res_model': 'product.product',
            'view_id': False,
            'views': [(False, 'form'), (False, 'tree')],
            'domain': [],
            'context': context,
            'target': 'new',  # 'new'
            'nodestroy': False,
            }

    def onchange_split_qty(
            self, cr, uid, ids, product_uom_qty, split_qty, context=None):
        """ Check not pass the original q.
        """
        res = {}
        if split_qty > product_uom_qty:
            res['value'] = {
                'split_qty': 0.0,
            }
            res['warning'] = {
                'title': 'Attenzione:',
                'message':
                    'Indicare una quantità <= di quella presente nel '
                    'documento originale, se consegnate più di quello '
                    'indicato va corretto il documento di partenza',
            }
        return res

    def split_qty_all(self, cr, uid, ids, context=None):
        """ Delivery all
        """
        move = self.browse(cr, uid, ids, context=context)[0]
        product_uom_qty = move.product_uom_qty

        return self.write(cr, uid, ids, {
            'split_qty': product_uom_qty,
        }, context=context)

    def split_qty_none(self, cr, uid, ids, context=None):
        """ Delivery none
        """
        return self.write(cr, uid, ids, {
            'split_qty': 0.0,
        }, context=context)

    _columns = {
        'split_qty': fields.float(
            'Consegna solo', digits=(16, 2),
            help='Indicare la quantità da consegnare, verrà utilizzata'
                 'per creare un nuovo documento togliendo poi la q.'
                 'dal picking che l''ha originata e lasciando il residuo'
                 'per la consegna futura. Se il questa q. è la stessa'
                 'del picking verrà invece eliminata la riga completamente'
                 'dal documento di partenza.',
        ),
    }


class StockMovePrefilter(orm.Model):
    """ Model name: StockMove
    """

    _inherit = 'stock.move'

    def create(self, cr, uid, vals, context=None):
        """ Create a new record for a model ClassName
            @param cr: cursor to database
            @param uid: id of current user
            @param vals: provides a data for new record
            @param context: context arguments, like lang, time zone

            @return: returns a id of new record
        """
        # Clean prefilter:
        vals['pre_filter'] = False
        return super(StockMovePrefilter, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """ Update redord(s) comes in {ids}, with new value comes as {vals}
            return True on success, False otherwise
            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of record ids to be update
            @param vals: dict of new values to be set
            @param context: context arguments, like lang, time zone

            @return: True on success, False otherwise
        """
        vals['pre_filter'] = False
        return super(StockMovePrefilter, self).write(
            cr, uid, ids, vals, context=context)

    def _get_subtotal_total(self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate
        """
        res = {}
        for move in self.browse(cr, uid, ids, context=context):
            res[move.id] = move.price_unit * move.product_uom_qty
        return res

    def onchange_product_id(self, cr, uid, ids, product_id=False, loc_id=False,
            loc_dest_id=False, partner_id=False):
        """ Update price during creation of movement
        """
        res = super(StockMove, self).onchange_product_id(
            cr, uid, ids, prod_id=product_id, loc_id=loc_id,
            loc_dest_id=loc_dest_id, partner_id=partner_id)

        if product_id and 'value' in res:
            product_proxy = self.pool.get('product.product').browse(
                cr, uid, product_id)
            res['value']['price_unit'] = product_proxy.standard_price
        return res

    def onchange_move_prefilter_id(self, cr, uid, ids, pre_filter, context=None):
        """ Force domain of product
        """
        res = {
            'domain': {'product_id': []},
            'value': {},
            }

        if pre_filter:
            res['domain']['product_id'].append(
                ('default_code', 'ilike', pre_filter))
            # res['value']['pre_filter'] = False
        return res

    _columns = {
        'pre_filter': fields.char('Pre filtro', size=50),

        'subtotal': fields.function(
            _get_subtotal_total, method=True,
            type='float', string='Subtotal',
            ),
        'report_comment': fields.text('Commento in stampa'),
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


class StockPickingInherit(orm.Model):
    """ Model name: StockPicking
    """
    _inherit = 'stock.picking'
    _order = 'name desc'

    def write_log_chatter_message(self, cr, uid, ids, message, context=None):
        """ Write message for log operation in order chatter
        """
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, uid, uid, context=context)
        body = '%s\n[User: %s]' % (message, user.name)
        return self.message_post(cr, uid, ids, body=body, context=context)

    def split_picking_partial_delivery_setup(self, cr, uid, ids, context=None):
        """ Select lines to split
        """
        model_pool = self.pool.get('ir.model.data')

        # Return new picking:
        view_tree_id = model_pool.get_object_reference(
            cr, uid,
            'fast_stock_move', 'view_stock_move_select_split_line_form')[1]

        picking_id = ids[0]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Righe del picking da dividere',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,
            'res_model': 'stock.move',
            'view_id': view_tree_id,
            'views': [(view_tree_id, 'tree')],
            'domain': [
                ('picking_id', '=', picking_id),
                ],
            'context': context,
            'nodestroy': False,
            }

    def split_picking_partial_delivery(self, cr, uid, ids, context=None):
        """ Split picking for a partial delivery
        """
        model_pool = self.pool.get('ir.model.data')
        move_pool = self.pool.get('stock.move')

        # Checklist before run procedure:
        picking_id = ids[0]
        old_picking = self.browse(cr, uid, picking_id, context=context)
        if old_picking.pick_state == 'delivered':
            raise osv.except_osv(
                _('Errore'),
                _('Documenti già consenati non possono essere divisi!'),
            )

        if not old_picking.has_partial:
            raise osv.except_osv(
                _('Errore'),
                _('Selezionare prima le quantità da spezzare nella consegna'
                  'con il bottone "Setup consegna parziale" poi ripremere il '
                  'bottone "Dividi picking"'),
            )

        # Generate new picking:
        new_picking_id = self.copy(cr, uid, picking_id, {
            'move_lines': [],  # Without lines
            'state': 'draft',
            'origin': old_picking.name,
        }, context=context)
        new_picking = self.browse(cr, uid, new_picking_id, context=context)

        # Generate new lines:
        split_comment = 'Diviso nel pick: %s\n' % new_picking.name
        for move in old_picking.move_lines:
            move_id = move.id
            new_qty = move.split_qty
            if new_qty <= 0:
                _logger.warning('Jump line no partial quantity selected')
                continue

            # create new stock move line for new picking
            move_pool.copy(cr, uid, move_id, {
                'product_uom_qty': new_qty,
                # 'product_uos_qty': uom_obj._compute_qty(cr, uid,
                # move.product_uom.id, new_qty, move.product_uos.id),
                'picking_id': new_picking_id,
                'state': 'draft',
                'split_qty': 0.0,  # reset
            })

            split_comment += '%s x %s (orig. doc. %s)\n' % (
                move.product_id.default_code or '?',
                new_qty,
                move.product_uom_qty,
            )

            # update previous pricking
            remain_qty = move.product_uom_qty - new_qty
            if remain_qty > 0:
                move_pool.write(cr, uid, move_id, {
                    'product_uom_qty': remain_qty,
                    'split_qty': 0.0,  # reset
                }, context=context)
            else:
                # Draft before delete:
                move_pool.write(cr, uid, move_id, {
                    'state': 'draft',
                }, context=context)
                move_pool.unlink(cr, uid, [move_id], context=context)

        # Write message detail
        self.write_log_chatter_message(
            cr, uid, ids, split_comment.replace('\n', '<br/>'),
            context=context)

        # Return new picking:
        view_form_id = model_pool.get_object_reference(
            cr, uid,
            'stock', 'view_picking_form')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuovo picking',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': new_picking_id,
            'res_model': 'stock.picking',
            'view_id': view_form_id,
            'views': [(view_form_id, 'form')],
            'domain': [],
            'context': context,
            # 'target': 'new',
            'nodestroy': False,
            }

    # -------------------------------------------------------------------------
    # On change
    # -------------------------------------------------------------------------
    def onchange_picking_partner_filter(
            self, cr, uid, ids,
            partner_id, account_no_parent, context=None):
        """ On change partner and check box
        """
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
        """ Update standard price on product if date passed
        """
        product_pool = self.pool.get('product.product')
        move_pool = self.pool.get('stock.move')

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
            default_code = product.default_code

            # -----------------------------------------------------------------
            # Update product price:
            # -----------------------------------------------------------------
            product_date = product.standard_price_date

            if not product_date or picking_date >= product_date:
                # If better date:
                product_pool.write(cr, uid, product.id, {
                    'standard_price': standard_price,
                    'standard_price_date': picking_date,
                    }, context=context)

            # -----------------------------------------------------------------
            # Update product price:
            # -----------------------------------------------------------------
            move_ids = move_pool.search(cr, uid, [
                ('picking_id.corresponding', '=', False),
                ('picking_id.pick_move', '=', 'out'),
                ('product_id', '=', product.id),
                ('date', '>=', '%s 00:00:00' % picking_date),
                ], context=context)
            if move_ids:
                move_pool.write(cr, uid, move_ids, {
                    'price_unit': standard_price,
                    }, context=context)
                _logger.warning('Updating # %s move for product %s' % (
                    len(move_ids),
                    default_code,
                    ))
        return True

    def generate_pick_out_draft(self, cr, uid, ids, context=None):
        """ Create pick out document depend on account analytic
        """
        if context is None:
            context = {}

        # Pool used:
        company_pool = self.pool.get('res.company')
        picking_pool = self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')
        account_pool = self.pool.get('account.analytic.account')
        type_pool = self.pool.get('stock.picking.type')

        # Get default account proxy:
        default_account_id = context.get('default_account_id', False)
        if default_account_id:
            default_account = account_pool.browse(
                cr, uid, default_account_id, context=context)
        else:
            default_account = False

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
        if not default_account_id:
            test = [
                True for item in pick_proxy.move_lines
                if item.auto_account_out_id.id]

            if not test:
                raise osv.except_osv(
                    _('Error'),
                    _('Picking without auto account!'),
                    )

        pickings = {}
        for move in pick_proxy.move_lines:
            pick_orig = move.picking_id
            account = move.auto_account_out_id or default_account
            if not account:
                continue  # No creation

            partner = account.partner_id
            origin = pick_orig.name
            product = move.product_id

            if account not in pickings:
                pickings[account] = picking_pool.create(cr, uid, {
                    'partner_id': partner.id,
                    'account_id': account.id,
                    'date': now,
                    'min_date': now,
                    'origin': origin,  # Origin as an extra info
                    'picking_type_id': picking_type.id,
                    'pick_move': 'out',
                    'pick_state': 'todo',
                    'auto_generator_id': pick_orig.id,
                    # 'state': 'delivered', # XXX not real!
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
                'price_unit': move.price_unit,  # same price
                # 'state': 'done',
                }, context=context)

        # model_pool = self.pool.get('ir.model.data')
        # model_pool.get_object_reference('module_name', 'view_name')[1]
        view_id = False

        # todo put in close status !!!
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pick created'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'res_id': 1,
            'res_model': 'stock.picking',
            'view_id': view_id,  # False
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', pickings.values())],
            'context': context,
            'target': 'current',  # 'new'
            'nodestroy': False,
            }

    # -------------------------------------------------------------------------
    # Second WF: Buttons
    # -------------------------------------------------------------------------
    # Utility for update movement:
    def _set_stock_move_picked(self, cr, uid, ids, state, context=None):
        """ Return list of moved in picking
        """
        move_pool = self.pool.get('stock.move')
        move_ids = move_pool.search(cr, uid, [
            ('picking_id', 'in', ids),
            ], context=context)
        return move_pool.write(cr, uid, move_ids, {
            'state': state,
            }, context=context)

    # Utility for update quants:
    def _create_quants(self, cr, uid, picking_ids, context=None):
        """ Create quants when done a movement
        """
        if context is None:
            context = {}

        move_sign = -1  # default = out
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
                     'location_id': eval(location_eval),  # move.location_id.id
                     'company_id': move.company_id.id,
                     'product_id': move.product_id.id,
                     'in_date': move.date,
                     # 'propagated_from_id'
                     # 'package_id'
                     # 'lot_id'
                     # 'reservation_id'
                     # 'owner_id'
                     # 'packaging_type_id'
                     # 'negative_move_id'
                    }, context=context)
        return True

    def _delete_quants(self, cr, uid, picking_ids, context=None):
        """ Create quants when done a movement
        """
        if context is None:
            context = {}

        context['force_unlink'] = True  # TODO delete quants

        # Pool used:
        quant_pool = self.pool.get('stock.quant')
        quant_ids = quant_pool.search(cr, uid, [
            ('stock_move_id.picking_id', 'in', picking_ids),
            ], context=context)
        return quant_pool.unlink(cr, uid, quant_ids, context=context)

    def pickwf_ready(self, cr, uid, ids, context=None):
        """ Restart procedure
            draft, cancel, waiting, confirmed, partially_available,
            assigned, done
        """
        # Update stock movement:
        self._set_stock_move_picked(
            cr, uid, ids, state='assigned', context=context)

        # Update picking:
        return self.write(cr, uid, ids, {
            'pick_state': 'ready',
            }, context=context)

    def pickwf_delivered(self, cr, uid, ids, context=None):
        """ Restart procedure
        """
        # Create quants for stock evaluation:
        self._create_quants(cr, uid, ids, context=context)

        # Update stock movement:
        self._set_stock_move_picked(  # assigned
            cr, uid, ids, state='done', context=context)

        self.update_standard_price_product(cr, uid, ids, context=context)

        # Update picking:
        return self.write(cr, uid, ids, {
            'pick_state': 'delivered',
            }, context=context)

    def pickwf_restart(self, cr, uid, ids, context=None):
        """ Restart procedure
        """
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
        """ Update default depend on context data
        """
        if context is None:
            return False

        if context.get('fast_picking') and context.get('fast_move') == 'in':
            return 'in'
        return 'out'  # default

    def get_default_picking_type_id(self, cr, uid, context=None):
        """ Update default depend on context data
        """
        if context is None:
            return False

        if context.get('fast_picking'):
            company_pool = self.pool.get('res.company')
            company_ids = company_pool.search(cr, uid, [], context=context)
            if context.get('fast_move') == 'in':
                return company_pool.browse(
                    cr, uid, company_ids,
                    context=context)[0].manual_picking_type_in_id.id
            else:  # default 'out'
                return company_pool.browse(
                    cr, uid, company_ids,
                    context=context)[0].manual_picking_type_id.id
        return False

    def _function_has_partial(self, cr, uid, ids, fields, args, context=None):
        """ Return real profit depend on type invoice and invoiced
        """
        assert len(ids) == 1, 'Dato disponibile solo su selezione singola'

        res = {}
        has_partial = False
        picking_id = ids[0]
        for move in self.browse(
                cr, uid, picking_id, context=context).move_lines:
            if move.split_qty > 0.0:
                has_partial = True
                break
        res[picking_id] = has_partial
        return res

    _columns = {
        'has_partial': fields.function(
            _function_has_partial, method=True, type='boolean',
            string='Ha parziali', store=False,
            help='Contiene delle selezioni di parziali per sdoppiare '
                 'il documento di consegna'),
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
    """ Model name: StockPicking
    """
    _inherit = 'stock.picking'

    _columns = {
        'corresponding': fields.boolean('Corresponding'),
        'auto_child_ids': fields.one2many(
            'stock.picking', 'auto_generator_id', 'Auto Child out'),
        }
