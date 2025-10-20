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
import pdb
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

                try:
                    json_data = response.json()
                except:
                    json_data = json.loads(response.content)
                return json_data

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
        API_TOKEN = imap_server.token.encode('ascii', 'ignore')

        HEADERS = {
            "X-API-Token": API_TOKEN,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # --------------------------------------------------------------------------------------------------------------
        # Load Domain list:
        # --------------------------------------------------------------------------------------------------------------
        domain_url = '{}/domains'.format(ROOT_URL)
        domain_reply = get_data_with_token(domain_url, HEADERS, mode='get')

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
                domain_pool.write(cr, uid, this_domain_ids, {
                    # 'code': domain_code,
                    # 'server_id': server_id,
                    'name': domain_record['name'],
                }, context=context)
                this_domain_id = this_domain_ids[0]
            else:
                this_domain_id = domain_pool.create(cr, uid, {
                    'code': domain_code,
                    'name': domain_record['name'],
                    'server_id': server_id,
                }, context=context)

            try:
                # If present remove:
                previous_domain_ids.remove(this_domain_id)
            except:
                pass

            # ----------------------------------------------------------------------------------------------------------
            # Mail update:
            # ----------------------------------------------------------------------------------------------------------
            for email in domain_data[domain_name]['email']:
                this_email_ids = email_pool.search(cr, uid, [
                    ('domain_id', '=', this_domain_id),
                    ('name', '=', email['email_address'])
                ], context=context)

                data = {
                    'domain_id': this_domain_id,
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
                try:
                    # Remove if present
                    previous_email_ids.remove(this_email_id)
                except:
                    pass

            for alias in domain_data[domain_name]['alias']:
                alias_name = '{}@{}'.format(alias['name'], domain_name)
                this_alias_ids = alias_pool.search(cr, uid, [
                    ('domain_id', '=', this_domain_id),
                    ('name', '=', alias_name),
                ], context=context)

                data = {
                    'domain_id': this_domain_id,
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
                try:
                    # Remove if present
                    previous_alias_ids.remove(this_alias_id)
                except:
                    pass

        # --------------------------------------------------------------------------------------------------------------
        # Removed data operation:
        # --------------------------------------------------------------------------------------------------------------
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
        'token': fields.char('API Token', size=100, required=True),
        'root_url': fields.char('Root URL', size=120, required=True),
        'name': fields.char('Dominio', size=60, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'note': fields.text('Note'),
    }


class ResPartnerEmailDomain(orm.Model):
    """ Domain
    """
    _name = 'res.partner.email.domain'
    _description = 'Mail Domain'
    
    def open_email_list(self, cr, uid, ids, context=None):
        """ Open mail from domain
        """
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'

        domain_id = ids[0]
        if context is None:
            context = {}

        force_operation = context.get('force_operation', 'mail')
        res_model = 'res.partner.email.domain.{}'.format(force_operation)


        form_view_id = tree_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': res_model,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('domain_id', '=', domain_id)],
            # 'target': '',
            'context': context,
        }
    def open_alias_list(self, cr, uid, ids, context=None):
        """ Open alias for domain
        """
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['force_operation'] = 'alias'
        return self.open_email_list(cr, uid, ids, context=ctx)

    _columns = {
        'server_id': fields.many2one('res.partner.email.server', 'Server', ondelete='cascade'),
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
        'domain_id': fields.many2one('res.partner.email.domain', 'Domini', ondelete='cascade'),
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
        'domain_id': fields.many2one('res.partner.email.domain', 'Domini', ondelete='cascade'),
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

    def open_domain_list(self, cr, uid, ids, context=None):
        """ Partner button open domain list
        """
        return True

    def open_email_list(self, cr, uid, ids, context=None):
        """ Partner button open domain list
        """
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'

        # ir_model_data = self.pool.get('ir.model.data')
        # template_id = ir_model_data.get_object_reference(
        # cr, uid, 'intervention_report', 'email_template_timesheet_intervent')[1]

        partner_id = ids[0]
        if context is None:
            context = {}

        force_operation = context.get('force_operation', 'mail')
        res_model = 'res.partner.email.domain.{}'.format(force_operation)


        form_view_id = tree_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': res_model,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('domain_id.partner_id', '=', partner_id)],
            # 'target': '',
            'context': context,
        }
    def open_alias_list(self, cr, uid, ids, context=None):
        """ Partner button open domain list
        """
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['force_operation'] = 'alias'
        return self.open_email_list(cr, uid, ids, context=ctx)

    _columns = {
        'domain_ids': fields.one2many('res.partner.email.domain', 'partner_id', 'Domini di posta'),
        }
