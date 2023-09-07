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
import pdb
import sys
import logging
import openerp
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class HrAnalyticTimesheetInherit(osv.osv):
    """ Intervention
    """

    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'ticket_id': fields.many2one('account.analytic.ticket', 'Ticket')
        }


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

    def create_new_intervention_for_ticket(self, cr, uid, ids, context=None):
        """ Create new intervent for this ticket
        """
        if context is None:
            context = {}

        ticket = self.browse(cr, uid, ids, context=context)[0]

        model_pool = self.pool.get('ir.model.data')
        # view_tree_id = model_pool.get_object_reference(cr, uid,
        #    'intervention_report', 'view_hr_analytic_timesheet_tree')[1]
        view_form_id = model_pool.get_object_reference(
            cr, uid,
            'intervention_report', 'view_hr_analytic_timesheet_form')[1]

        ctx = context.copy()
        ctx.update({
            'default_name': ticket.name,
            'default_intervention_request': ticket.name,
            'default_internal_note': ticket.solution,

            'default_request_by': ticket.contact_id.name or False,

            'default_ticket_id': ticket.id,
            'default_user_id': ticket.user_id.id,

            'default_intervent_partner_id': ticket.partner_id.id,
            'default_intervent_contact_id': ticket.contact_id.id,
            # 'default_account_no_parent': True,  # todo to see all account
            # 'default_account_id': ticket.account_id.id,

            'default_date_start': datetime.now().strftime(
                DEFAULT_SERVER_DATETIME_FORMAT),
            'default_intervent_duration': 1.0,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuovo intervento per il ticket',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,  # New record
            'res_model': 'hr.analytic.timesheet',
            'view_id': view_form_id,
            'views': [(view_form_id, 'form')],
            'domain': [],
            'context': ctx,
            'target': 'new',
            'nodestroy': False,
            }

    def assign_to_me(self, cr, uid, ids, context=None):
        """ Assign me to ticket operator
        """
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, uid, uid, context=context)

        message = 'Autoassegnazione ticket: %s' % user.name

        self.write_log_chatter_message(cr, uid, ids, message, context=context)
        return self.write(cr, uid, ids, {
            'user_id': uid,
        }, context=context)

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
            'invoice_date': False,
        }, context=context)

    def wkf_open(self, cr, uid, ids, context=None):
        """ Open ticket
        """
        ticket = self.browse(cr, uid, ids, context=context)[0]
        message = 'Cambio stato ticket: Aperto'
        self.write_log_chatter_message(cr, uid, ids, message, context=context)
        data = {
            'state': 'open',
        }
        if not ticket.ref:
            data['ref'] = self.pool.get('ir.sequence').get(
                cr, uid, 'account.analytic.ticket')

        return self.write(cr, uid, ids, data, context=context)

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
        'ref': fields.char('Rif.', size=15, readonly=True),
        'name': fields.char('Oggetto', size=90, required=True),
        'date': fields.datetime('Data'),
        'scheduled': fields.date('Schedulare per'),
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
            'res.partner', 'Cliente', required=True,
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
        'invoice_mode': fields.selection([
            ('month', 'Mensilmente'),
            ('end', 'Alla chiusura'),
            ('excluded', 'Non fatturare'),
            ], string='Modo fatturazione', required=True,
            help='Indica la modalità di fatturare gli interventi che '
                 'potrebbero essere fatti per questi ticket, es. se ' 
                 'il ticket dura più di un mese verrebbero fatturati '
                 'nel periodo di competenza, oppure è necessario aspettare '
                 'la fine del mese oppure non è da fatturare'),
        'state': fields.selection([
            ('draft', 'Bozza'),
            ('open', 'Aperta'),
            ('closed', 'Chiusa'),
            ('suspended', 'Sospesa'),
            ], string='Stato', required=True, readonly=True),
        'intervention_ids': fields.one2many(
            'hr.analytic.timesheet', 'ticket_id', 'Interventi collegati',
            ),
        }

    _defaults = {
        'date': lambda *x: datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        'priority': lambda *x: 'normal',
        'invoice_mode': lambda *x: 'end',
        'state': lambda *x: 'draft',
        }
