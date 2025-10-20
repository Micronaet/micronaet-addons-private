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
from osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP)
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class ResPartnerEmailServer(orm.Model):
    """ IMAP Server
    """
    _name = 'res.partner.email.server'
    _description = 'Mail Server'

    _columns = {
        'token': fields.char('API Token', size=60, required=True),
        'root_url': fields.char('Root URL', size=120, required=True),
        'name': fields.char('Dominio', size=30, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'note': fields.text('Note'),
    }


class ResPartnerEmailDomain(orm.Model):
    """ Domain
    """
    _name = 'res.partner.email.domain'
    _description = 'Mail Domain'
    
    _columns = {
        'server_id': fields.many2one('res.partner.email.server', 'Server'),
        'code': fields.char('Codice', size=30, required=True),
        'name': fields.char('Dominio', size=30, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'note': fields.text('Note'),
         }

class ResPartnerDomainMail(orm.Model):
    """ Email for domain
    """
    _name = 'res.partner.email.domain.mail'
    _description = 'Email'
    
    _columns={
        'name': fields.char('Nome', size=120, required=True),
        'domain_id': fields.many2one('res.partner.email.domain', 'Domini'),
        'create_date': fields.datetime('Data Creazione'),
        'dimension': fields.integer('Dimensione'),

        'removed': fields.boolean('Rimossa', help='Email cancellata, non più presente'),
        'active': fields.boolean('Attiva'),
         }


class ResPartnerDomainAlias(orm.Model):
    """ Alias for domain
    """
    _name = 'res.partner.email.domain.alias'
    _description = 'Alias'

    _columns = {
        'name': fields.char('Nome', size=120, required=True),
        'domain_id': fields.many2one('res.partner.email.domain', 'Domini'),
        'create_date': fields.datetime('Data Creazione'),
        'redirect': fields.text('Indiriziz di redirect'),

        'removed': fields.boolean('Rimosso', help='Alias cancellata, non più presente'),
        'active': fields.boolean('Attiva'),
    }

class ResPartnerEmailDomainInherit(orm.Model):
    """ Relation fields
    """
    _inherit = 'res.partner.email.domain'

    _columns = {            
        'email_ids': fields.one2many('res.partner.email.domain.mail', 'domain_id', 'Caselle di posta'),
        'alias_ids': fields.one2many('res.partner.email.domain.alias', 'domain_id', 'Alias di email'),
        }

class ResPartnerInherit(orm.Model):
    """ *2many in Partner
    """
    _inherit = 'res.partner'
    
    _columns = {
        'domain_ids': fields.one2many('res.partner.email.domain', 'partner_id', 'Domini di posta'),
        }
