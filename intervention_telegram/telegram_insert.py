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
import telepot
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class TelegramMessage(orm.Model):
    """ Model name: TelegramMessage
    """    
    _name = 'telegram.message'
    _description = 'Telegram Message'
    _rec_name = 'datetime'
    _order = 'datetime'

    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def get_user(self, cr, uid, user, context=None):
        ''' Return user ID
            Not used for now
        '''
        user_ids = user_pool.search(cr, uid, [
            '|',
            ('name', 'ilike', user),
            ('login', 'ilike', user),
            ], context=context)
        if user_ids:
            return user_ids[0]
        return False

    def get_partner(self, cr, uid, partner_name, context=None):
        ''' Return user ID
        '''
        partner_pool = self.pool.get('res.partner')
        partner_ids = partner_pool.search(cr, uid, [
            '|',
            ('name', 'ilike', partner_name),
            ('telegram_nickname', 'ilike', partner_name),
            ], context=context)
        if partner_ids:
            return partner_ids[0]
        return False

    def get_datetime(self, date, time, months):
        ''' Return datetime from date-time
        '''
        import pdb; pdb.set_trace()
        if '/' in date or '-' in date:
            date_formatted = date
        else:    
            # Format Date:
            date_part = date.lower().split(' ')
            try:
                day = int(date_part[0].strip())
                
                month = date_part[1].strip()
                if not month.isdigit():
                    month = months.get(month)
                month = int(month)
                
                if len(date_part) > 2:
                    year = int(year.strip())
                else:
                    year = datetime.now().year    
                date_formatted = '%s/%02d/%02d' % (
                    year,
                    month, 
                    day,
                    )
            except:    
                date_formatted = ''
            
        # Format hour:
        time = time.replace('.', ':').replace(' ', '')
        time_part = time.split(':')
        try:
            time_formatted = '%s:%s:00' % (
                time_part[0],
                time_part[1] if len(time_part) >= 2 else '00',
                #time_part[2] if len(time_part) == 3 else '00',
                )
        except:
            time_formatted = ''    
        
        if not date_formatted or not time_formatted:
            return False
            
        return '%s %s' % (
            date_formatted,
            time_formatted,
            )

    def get_duration(self, duration):
        ''' Return duration float
        '''
        duration = duration.replace(',', '.').replace(' ', '')
        try:
            return float(duration)
        except:
            return False

    def get_location(self, location, location_db):
        ''' Return location code
        '''
        location = location.lower().strip()
        for mode in location_db:
            for text in location_db[mode]:
                if location == text:
                    return mode
        return False

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def show_intervent_from_message(self, cr, uid, ids, context=None):
        ''' Show intervent
        '''
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        intervent_id = current_proxy.intervent_id.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Message imported'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_id': intervent_id,
            'res_model': 'hr.analytic.timesheet',
            'view_id': False, #view_id, # False
            'views': [(False, 'form'), (False, 'tree')],
            'domain': [],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }
        
    def create_intervent_from_message(self, cr, uid, ids, context=None):
        ''' Create intervent parsing message        
            Also used during import process with more ids
        '''
        # Pool used:
        partner_pool = self.pool.get('res.partner')
        intervent_pool = self.pool.get('hr.analytic.timesheet')
        token_pool = self.pool.get('telegram.token')
        location_pool = self.pool.get('telegram.token.location')
        month_pool = self.pool.get('telegram.token.month')

        # ---------------------------------------------------------------------
        # Load token list:
        # ---------------------------------------------------------------------
        token_ids = token_pool.search(cr, uid, [], context=context)
        token_list = {}
        for token in token_pool.browse(
                cr, uid, token_ids, context=context):
            token_list[token.name] = token.keyword.split('|')

        # ---------------------------------------------------------------------
        # Load token location list:
        # ---------------------------------------------------------------------
        location_ids = location_pool.search(cr, uid, [], context=context)
        location_db = {}
        for location in location_pool.browse(
                cr, uid, location_ids, context=context):
            location_db[location.name] = location.keyword.split('|')

        # ---------------------------------------------------------------------
        # Load months translation:
        # ---------------------------------------------------------------------
        month_ids = month_pool.search(cr, uid, [], context=context)
        month_db = {}
        for month in month_pool.browse(
                cr, uid, month_ids, context=context):
            month_db[month.name] = month.value

        for message in self.browse(cr, uid, ids, context=context):
            message_text = message.text      
            message_date = message.datetime  
            user_id = message.user_id.id

            telegram_part = message_text.split(' ')
            token_block = []
            i = 0
            for part in telegram_part:
                part = part.lower()
                if not part:
                    i += 1
                    continue
                for token in token_list:
                    for word in token_list[token]:
                        if part == word:
                            if token_block:
                                token_block[-1][2] = (i)
                            token_block.append([token, i + 1, 0])
                            break
                    if token in token_block:
                        break
                # if len(token_list) == len(token_block)        
                i += 1
                
            token_value = {}
            for token, from_pos, to_pos in token_block:
                if not to_pos:
                    to_pos = len(telegram_part)
                token_text_part = telegram_part[from_pos: to_pos]
                if token_text_part:    
                    token_value[token] = ' '.join(token_text_part)

            # -----------------------------------------------------------------
            # Create Intervent record: TODO put in button
            subject = token_value.get('subject', '')
            if not subject:
                continue # not an intervent

            intervent_data = {
                'telegram_id': message.id,
                'name': subject,
                'intervention_request': subject,
                'intervention': token_value.get('description', ''),
                'user_id': user_id,
                }
                
            # -----------------------------------------------------------------
            # Update extra information for user:
            # -----------------------------------------------------------------
            res = intervent_pool.on_change_user_id(
                cr, uid, False, user_id)
            intervent_data.update(res.get('value', {}))
                
            incomplete = []
            
            # -----------------------------------------------------------------
            # Partner: 
            # -----------------------------------------------------------------
            if 'partner' in token_value:
                partner_id = self.get_partner(
                    cr, uid, token_value['partner'], context=context)
                if partner_id:
                    intervent_data['intervent_partner_id'] = partner_id
                    
                    # ---------------------------------------------------------
                    # Put default account:
                    # ---------------------------------------------------------
                    res = intervent_pool.on_change_partner(
                        cr, uid, False, partner_id, False, context=context)
                    intervent_data.update(res.get('value', {}))

                else:
                    incomplete.append('partner')
            else:
                incomplete.append('partner')

            # -----------------------------------------------------------------
            # From datetime: 
            # -----------------------------------------------------------------
            date = token_value.get('date', message_date[:10])
            time = token_value.get('time', message_date[-8:])
            from_date = self.get_datetime(date, time, month_db)
            if from_date:
                intervent_data['date_start'] = from_date
            else:
                incomplete.append('from_date')

            # -----------------------------------------------------------------
            # Duration: 
            # -----------------------------------------------------------------
            if 'duration' in token_value:
                duration = self.get_duration(token_value['duration'])
                if duration:
                    intervent_data['intervent_duration'] = duration
                else:
                    incomplete.append('duration')
            else:
                incomplete.append('duration')

            # -----------------------------------------------------------------
            # Location: 
            # -----------------------------------------------------------------
            if 'location' in token_value:
                location = self.get_location(
                    token_value['location'], location_db)
                if location:
                    intervent_data['mode'] = location
                    
                    # Update trip info:
                    res = intervent_pool.on_change_mode(
                        cr, uid, False, location, context=context)
                    intervent_data.update(res.get('value', {}))    
                else:
                    incomplete.append('location')
            
            # -----------------------------------------------------------------
            # Create intervent: 
            # -----------------------------------------------------------------            
            try:                
                intervent_id = intervent_pool.create(
                    cr, uid, intervent_data, context=context)
                # Update back referente on message
                self.write(cr, uid, message.id, {
                    'intervent_id': intervent_id,
                    'missing_field': ', '.join(incomplete),
                    }, context=context)        
            except:
                _logger.error('Error creating intervent: %s' % intervent_data)
                continue

        return {
            'type': 'ir.actions.act_window',
            'name': _('Message imported'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'res_id': 1,
            'res_model': 'telegram.message',
            'view_id': False, #view_id, # False
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', ids)],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }
        
    _columns = {
        'datetime': fields.datetime('Date'),
        'username': fields.char('Username', size=64, required=True),
        'user_id': fields.many2one('res.users', 'User'),
        
        'text': fields.text('Text'),
        'intervent_id': fields.many2one('hr.analytic.timesheet', 'Intervent'),
        
        'missing_field': fields.char('Missing', size=120),
        'telegram_id': fields.integer('Message ID'),
        'update_id': fields.integer('Update ID'),
        'telegram_group': fields.char('Telegram group', size=64),
        }

class TelegramToken(orm.Model):
    """ Model name: TelegramToken
    """    
    _name = 'telegram.token'
    _description = 'Telegram Token'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'required': fields.boolean('Required'),
        'keyword': fields.text('Keyword list',
            help='List of lowercase keyword lise separater with |'),
        'note': fields.text('Note'),            
        }

class TelegramTokenLocation(orm.Model):
    """ Model name: Telegram token months
    """    
    _name = 'telegram.token.location'
    _description = 'Telegram token location'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Month', size=20, required=True),
        'keyword': fields.text('Keyword list',
            help='List of lowercase keyword lise separater with |'),
        }

class TelegramTokenMonth(orm.Model):
    """ Model name: Telegram token months
    """    
    _name = 'telegram.token.month'
    _description = 'Telegram Token month'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Month', size=20, required=True),
        'value': fields.char('Value', size=2, required=True),
        }

class HrAnalyticTimesheet(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'telegram_id': fields.many2one('telegram.message', 'Telegram'),
        }

class ResPartner(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _inherit = 'res.partner'
    
    _columns = {
        'telegram_nickname': fields.char('Telegram nickname', size=100,
           help='Nick name used for identify partner in Telegram input'),
        # TODO manage syntax!
        }

class ResUsers(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _inherit = 'res.users'

    # Utility:
    def get_telegram_gmt(self, seconds):
        ''' Date from 1970-01-01 00:00:00
        '''
        datetime_format = '%Y-%m-%d %H:%M:%S'
        origin = datetime.strptime('1970-01-01 00:00:00', datetime_format)
        return datetime.strftime(
            origin + timedelta(seconds=seconds), datetime_format)

    # TODO schedule procedure for import every hours:

    def load_telegram_intervent(self, cr, uid, ids, context=None):
        ''' Load current user telegram intervent
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        # Pool used:
        message_pool = self.pool.get('telegram.message')

        user = self.browse(cr, uid, ids, context=context)[0]
        company = user.company_id
        telegram_group = company.telegram_group
        telegram_username = user.telegram_login
        telegram_user_id = ids[0] # This user 

        # ---------------------------------------------------------------------
        # Load all message ID for this user / group:
        # ---------------------------------------------------------------------
        message_pool = self.pool.get('telegram.message')
        message_ids = message_pool.search(cr, uid, [
            ('username', '=', telegram_username),
            ('telegram_group', '=', telegram_group),
            ], context=context)
        telegram_ids = [msg.telegram_id for msg in message_pool.browse(
                cr, uid, message_ids, context=context)]
        
        # ---------------------------------------------------------------------
        # Comunicate Telegram message:
        # ---------------------------------------------------------------------
        bot = telepot.Bot(company.telegram_token)
        bot.getMe()

        new_message_ids = []
        for record in bot.getUpdates():
            # -----------------------------------------------------------------
            # 1. Only message record:
            if 'message' not in record:
                continue 
            message = record['message']

            # -----------------------------------------------------------------
            # 2. Only message in chat group selected:
            try:
                if message['chat']['id'] != int(telegram_group):
                    continue # not in chat group
            except:
                continue
                
            # -----------------------------------------------------------------
            # 2. Only real user (no bot): 
            try:
                is_bot = message['from']['is_bot']
                if is_bot:
                    continue
                    
                username = message['from']['username']
                if telegram_username != username:
                    continue
                    
                from_id = message['from']['id'] # XXX not used for now
            except:
                continue
            
            # -----------------------------------------------------------------
            #3. Message not yet imported:
            message_id = message['message_id']
            if message_id in telegram_ids:
                continue # yet present

            # -----------------------------------------------------------------
            # Read Message:
            # -----------------------------------------------------------------
            message_text = message['text'].strip()

            message_data = {
                'text': message_text,
                'update_id': record['update_id'],
                'datetime': self.get_telegram_gmt(message['date']), 
                'username': username,
                'user_id': telegram_user_id,
                'telegram_group': telegram_group,
                'telegram_id': message_id,
                }
            new_message_ids.append(message_pool.create(
                cr, uid, message_data, context=context))

        # ---------------------------------------------------------------------
        # Create intervent:
        # ---------------------------------------------------------------------
        if new_message_ids:
            return message_pool.create_intervent_from_message(
                cr, uid, new_message_ids, context=context)        
        _logger.warning('No new telegram message')
        return True

    _columns = {
        'telegram_login': fields.char('Telegram username', size=40),
        }

class ResCompany(osv.osv):
    ''' Add extra fields to company
    '''
    _inherit = 'res.company'
    
    _columns = {
        'telegram_token': fields.char('Telegram token', size=80),
        'telegram_group': fields.char('Telegram group', size=20),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
