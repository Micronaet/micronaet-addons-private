# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class AccountAnalyticTicketInherit(osv.osv):
    """ Ticket Management
    """

    _inherit = 'account.analytic.ticket'
    _order = 'date desc'

    def write_log_chatter_message(self, cr, uid, ids, message, context=None):
        """ Write message for log operation in order chatter
        """
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, uid, uid, context=context)
        body = '%s\n[User: %s]' % (message, user.name)
        return self.message_post(cr, uid, ids, body=body, context=context)

    # -------------------------------------------------------------------------
    #                            Fast Workflow:
    # -------------------------------------------------------------------------
    def wkf_restart(self, cr, uid, ids, context=None):
        """ Open ticket
        """
        message = 'Cambio stato ticket: Riavviato'
        self.write_log_chatter_message(cr, uid, ids, message, context=context)
        return self.write(cr, uid, ids, {
            'state': 'draft',
        }, context=context)

    def wkf_open(self, cr, uid, ids, context=None):
        """ Open ticket
        """
        message = 'Cambio stato ticket: Aperto'
        self.write_log_chatter_message(cr, uid, ids, message, context=context)
        return self.write(cr, uid, ids, {
            'state': 'open',
            'invoice_date': False,
        }, context=context)

    def wkf_suspended(self, cr, uid, ids, context=None):
        """ Open ticket
        """
        message = 'Cambio stato ticket: Sospeso'
        self.write_log_chatter_message(cr, uid, ids, message, context=context)
        return self.write(cr, uid, ids, {
            'state': 'suspended',
        }, context=context)

    def wkf_closed(self, cr, uid, ids, context=None):
        """ Open ticket
        """
        message = 'Cambio stato ticket: Chiuso'
        self.write_log_chatter_message(cr, uid, ids, message, context=context)
        return self.write(cr, uid, ids, {
            'state': 'closed',
            'invoice_date':
                datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        }, context=context)

    _columns = {
        'name': fields.char('Oggetto', size=90),
        'date': fields.datetime('Data'),
        'deadline': fields.date('Scadenza'),
        'invoice_date': fields.date(
            'Data chiusura',
            help='Data di chiusura ticket utilizzata per '
                 'fatturare gli interventi'),
        'description': fields.text(
            'Descrizione problema',
            help='Descrizione del problema da richiedere al cliente'),
        'solution': fields.text(
            'Intervento da effettuare',
            help='Descrizione intervento per il tecnico che interverrà '
                 'dal cliente (alcune indicazioni di massima per spiegare'
                 ' come deve intervenire, di solito rilasciate dal '
                 'responsabile)'),
        'partner_id': fields.many2one(
            'res.partner', 'Cliente',
            help='Cliente che ha aperto il ticket'),
        'account_id': fields.many2one(
            'account.analytic.account', 'Contratto',
            help='Contratto sul quale è stato aperto il ticket, se presente'),
        'contact_id': fields.many2one(
            'res.partner', 'Contatto',
            help='Il richiedende intervento se non è una ditta ma un privato'
                 'o una persona che appartiene alla ditta.'),
        'max_hours': fields.float(
            'Durata massima', digits=(16, 2),
            help='Durata massima intervento da',
        ),
        'assigned_user_ids': fields.many2many(
            'res.users', 'ticket_users_rel', 'ticket_id', 'user_id',
            'Tecnici',
            help='Tecnici che possono portare a termina il ticket, la '
                 'assegnazione della lista permette i vedere nei loro ticket '
                 'quelli che comprendono il loro nome (o quelli non assegnati)'
                 ' Il tecnico poi prenderà in carico i ticket che ritiene '
                 'di potere portare a termina (se non assegnato direttamente)'
            ),
        'user_id': fields.many2one(
            'res.users', 'Assegnato a',
            help='Il tecnico può assegnarsi il ticket oppure gli può '
                 'già venire assegnato dalla amministrazione o da chi '
                 'ha preso il ticket.'),

        # todo invoice_mode (at the end of ticket, at intervention)
        'priority': fields.selection([
            ('low', 'Bassa'),
            ('normal', 'Normale'),
            ('high', 'Alta'),
            ], string='Priorità', required=True),
        'state': fields.selection([
            ('draft', 'Bozza'),
            ('open', 'Aperta'),
            ('closed', 'Chiusa'),
            ('suspended', 'Sospesa'),
            ], string='Stato', required=True, readonly=True),
        }

    _defaults = {
        'priority': lambda *x: 'normal',
        'state': lambda *x: 'draft',
        }
