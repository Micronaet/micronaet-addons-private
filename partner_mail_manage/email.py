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
import requests
import json
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

    def button_load_all_domain_data(self, cr, uid, ids, context=None):
        """ Load all data in this server
        """
        # --------------------------------------------------------------------------------------------------------------
        #                                               Utility:
        # --------------------------------------------------------------------------------------------------------------
        def get_data_with_token(url, headers, mode='get', verbose=False):
            """ Call Endpoint passing headers data
            """
            if verbose:
                _logger.info('Connecting to {} ...'.format(url))

            try:
                if mode == 'get':
                    response = requests.get(url, headers=headers)
                elif mode == 'post':
                    response = requests.post(url, headers=headers)
                else:
                    _logger.info('No mode {}'.format(mode))
                    return False

                response.raise_for_status()
                if verbose:
                    _logger.info('Connected! Status code {}'.format(response.status_code))
                return response.json()

            except requests.exceptions.HTTPError as errh:
                _logger.info('Error HTTP: {}'.format(errh))
                # _logger.info('Reply response: {}'.format(response.text))
            except requests.exceptions.ConnectionError as errc:
                _logger.info('Connection error: {}'.format(errc))
            except requests.exceptions.Timeout as errt:
                _logger.info('Timeout in request: {}'.format(errt))
            except requests.exceptions.RequestException as err:
                _logger.info('Generic error: {}'.format(err))
            return None

        # --------------------------------------------------------------------------------------------------------------
        #                                                      Procedure:
        # --------------------------------------------------------------------------------------------------------------
        domain_pool = self.pool.get('res.partner.email.domain')
        email_pool = self.pool.get('res.partner.email.domain.mail')
        alias_pool = self.pool.get('res.partner.email.domain.alias')

        server_id = ids[0]
        imap_server = self.browse(cr, uid, server_id, context=context)

        ROOT_URL = imap_server.root_url
        API_TOKEN = imap_server.token

        HEADERS = {
            "X-API-Token": API_TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # --------------------------------------------------------------------------------------------------------------
        # Load Domain list:
        # --------------------------------------------------------------------------------------------------------------
        domain_url = '{}/domains'.format(ROOT_URL)
        domain_reply = get_data_with_token(domain_url, HEADERS, mode='post')

        domain_data = {}

        # Loop to read Domain extra data:
        loop = [
            ('email', 'email_accounts'),
            ('alias', 'alias_email_accounts'),
        ]

        if domain_reply:
            for domain in domain_reply['resources']:

                # ------------------------------------------------------------------------------------------------------
                # Load domain emails:
                # ------------------------------------------------------------------------------------------------------
                domain_code = domain['code']
                domain_name = domain['name']
                _logger.info('\n\nReading Domain: {}'.format(domain_name))

                domain_data[domain_name] = {
                    'detail': domain,
                    'email': [],
                    'alias': [],
                }

                for key, endpoint in loop:
                    email_url = '{}/domains/{}/{}'.format(ROOT_URL, domain_code, endpoint)
                    email_payload = HEADERS.copy()
                    page = 1

                    while True:
                        email_payload['page'] = page
                        reply = get_data_with_token(email_url, HEADERS, mode='get')
                        if reply:
                            for email in reply['resources']:
                                domain_data[domain_name][key].append(email)

                            total_pages = reply['pagination']['total_pages']
                            page += 1
                            if page > total_pages:
                                print('Max page raised {}'.format(total_pages))
                                break
                            else:
                                print('Read next page {} of {}'.format(page, total_pages))
                        else:
                            print('No mail for domain {}'.format(domain_code))
                            break

        else:
            _logger.error('Cannot connect to API server')
            return False

        # --------------------------------------------------------------------------------------------------------------
        # Update data
        # --------------------------------------------------------------------------------------------------------------
        previous_domain_ids = domain_pool.search(cr, uid, [
            ('server_id', '=', server_id)
        ], context=context)

        previous_email_ids = email_pool.search(cr, uid, [
            ('domain_id.server_id', '=', server_id),
        ], context=context)

        previous_alias_ids = alias_pool.search(cr, uid, [
            ('domain_id.server_id', '=', server_id),
        ], context=context)

        for domain_name in domain_data:

            # ----------------------------------------------------------------------------------------------------------
            # Domain update:
            # ----------------------------------------------------------------------------------------------------------
            domain_record = domain_data[domain_name]['detail']
            domain_code = domain_record['code']
            _logger.info('Update domain: {}'.format(domain_name))
            this_domain_ids = domain_pool.search(cr, uid, [
                ('server_id', '=', server_id),
                ('code', '=', domain_code),
            ], context=context)

            if this_domain_ids:
                # No update for now
                this_domain_id = this_domain_ids[0]
            else:
                this_domain_id = domain_pool.create(cr, uid, {
                    'code': domain_code,
                    'name': domain_record['code'],
                    'server_id': server_id,
                }, context=context)

            previous_domain_ids.remove(this_domain_id)

            # ----------------------------------------------------------------------------------------------------------
            # Mail update:
            # ----------------------------------------------------------------------------------------------------------
            for email in domain_data[domain_name]['email']:
                this_email_ids = email_pool.search(cr, uid, [
                    ('domain_id', '=', this_domain_id),
                    ('name', '=', email['email_address'])
                ], context=context)

                data = {
                    'name': email['email_address'],
                    # 'create_date': email['created_at'],
                    'dimension': email['max_email_quota'] / (1024 ** 3),
                    'active': email['status'] == 'enabled',
                }
                if this_email_ids:
                    email_pool.write(cr, uid, this_email_ids, data, context=context)
                    this_email_id = this_email_ids[0]
                else:
                    this_email_id = email_pool.create(cr, uid, data, context=context)
                previous_email_ids.remove(this_email_id)

            for alias in domain_data[domain_name]['alias']:
                alias_name = '{}@{}'.format(alias['name'], domain_name),
                this_alias_ids = alias_pool.search(cr, uid, [
                    ('domain_id', '=', this_domain_id),
                    ('name', '=', alias_name),
                ], context=context)

                data = {
                    'name': alias_name,
                    # 'create_date': alias['created_at'],
                    'redirect': ', '.join(alias['destinations']),
                    'active': alias['status'] == 'enabled',
                }
                if this_alias_ids:
                    alias_pool.write(cr, uid, this_alias_ids, data, context=context)
                    this_alias_id = this_alias_ids[0]
                else:
                    this_alias_id = alias_pool.create(cr, uid, data, context=context)
                previous_alias_ids.remove(this_alias_id)

            # ----------------------------------------------------------------------------------------------------------
            # Removed data operation:
            # ----------------------------------------------------------------------------------------------------------
            if previous_domain_ids:
                _logger.info('Removed domain {}'.format(previous_domain_ids))
                domain_pool.write(cr, uid, previous_domain_ids, {
                    'removed': True,
                }, context=context)
            if previous_email_ids:
                _logger.info('Removed email {}'.format(previous_email_ids))
                email_pool.write(cr, uid, previous_email_ids, {
                    'removed': True,
                }, context=context)
            if previous_alias_ids:
                _logger.info('Removed alias {}'.format(previous_alias_ids))
                alias_pool.write(cr, uid, previous_alias_ids, {
                    'removed': True,
                }, context=context)
        return True

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
        'removed': fields.boolean('Rimosso', help='Dominio cancellata, non più presente'),
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
