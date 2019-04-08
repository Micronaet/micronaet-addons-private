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

    def create_intervent_from_message(self, cr, uid, ids, context=None):
        ''' Create intervent parsing message        
        '''
        return True
        
    _columns = {
        'datetime': fields.date('Date'),
        'username': fields.char('Username', size=64, required=True),
        'user_id': fields.many2one('res.users', 'User'),
        
        'text': fields.text('Text'),
        'intervent_id': fields.many2one('hr.analytic.timesheet', 'Intervent'),
        
        'missing_field': fields.char('Telegram text', size=100),
        'telegram_id': fields.integer('Message ID'),
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

class ResUsers(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _inherit = 'res.users'

    # TODO schedule procedure for import every hours:

    def load_telegram_intervent(self, cr, uid, ids, context=None):
        ''' Load current user telegram intervent
        '''
        return True

    _columns = {
        'telegram_login': fields.text('Telegram login'),
        }

class ResCompany(osv.osv):
    ''' Add extra fields to company
    '''
    _inherit = 'res.company'
    
    _columns = {
        'telegram_token': fields.char('Telegram token', size=40),
        'telegram_group': fields.char('Telegram group', size=20),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
