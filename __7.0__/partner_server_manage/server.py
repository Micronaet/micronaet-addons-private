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
import netsvc
import logging
from osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class res_partner_server_os(orm.Model):
    ''' Operanting system
    '''
    _name = 'res.partner.server.os'
    _description = 'Operating system'
    
    _columns = {
        'name': fields.char('Nome', size=30, required=True),
        'note': fields.text('Note'),
         }

class res_partner_server_password_type(orm.Model):
    ''' Type of password
    '''
    _name = 'res.partner.server.password.type'
    _description = 'Password type'
    
    _columns={
        'name': fields.char('Nome', size=60, required=True),
        'note': fields.text('Note'),
         }

class res_partner_server_service(orm.Model):
    ''' Server services
    '''
    _name = 'res.partner.server.service'
    _description = 'Server service'
    
    _columns = {
        'name': fields.char('Name', size=60, required=True),
        'version': fields.char('Version', size=30,),
        'note': fields.text('Note'),
        'server_id': fields.many2one('res.partner.server', 'Server'),            
        }

class res_partner_server_password(orm.Model):
    ''' Server password for service
    '''
    _name = 'res.partner.server.password'
    _description = 'Service password'
    
    _columns={
            'name': fields.char('Username', size=30, required=True),
            'password': fields.char('Password', size=15, required=True),
            'note': fields.text('Note'),
            'interval': fields.integer('Interval', 
                help="For deadline password, this field is the interval in days"),
            'deadline': fields.date('Deadline'),
            'address': fields.char('Address', size=40),
            'port': fields.integer('Port'),
            'type_id': fields.many2one(
                'res.partner.server.password.type', 'Type'),
            'server_id': fields.many2one('res.partner.server', 'Server'),
            'service_id': fields.many2one(
                'res.partner.server.service', 'Service'), #REQUIRED??
             }

class res_partner_server_service(orm.Model):
    '''Aggiunta di campi *2many
    '''
    _name = 'res.partner.server.service'
    _inherit = 'res.partner.server.service'
    
    _columns = {            
        'password_ids': fields.one2many('res.partner.server.password', 
            'service_id', 'Password'),
        }

class res_partner_server(orm.Model):
    ''' Server per partner
    '''
    _name = 'res.partner.server'
    _description = 'Server'
    
    _columns={
        'name': fields.char('Nome', size=30, required=True),
        'domain': fields.char('Dominio', size=60),
        'ip': fields.char('IP', size=15, required=True),
        'note': fields.text('Note'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'os_id': fields.many2one('res.partner.server.os', 'Operating System'),
        'password_ids': fields.one2many('res.partner.server.password', 
            'server_id', 'Password'),
        'service_ids': fields.one2many('res.partner.server.service', 
            'server_id', 'Services'),
        'bit': fields.selection([
            ('32', '32 bit'), 
            ('64', '64 bit')
            ], 'Bit', select=True),
        }
             
class res_partner(orm.Model):
    ''' *2many in Partner 
    '''
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'server_ids': fields.one2many(
            'res.partner.server', 'partner_id', 'Server'),   
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
