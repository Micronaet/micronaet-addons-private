# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2004-2012 Micronaet srl. All Rights Reserved
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
from osv import fields, osv
from openerp.osv.fields import datetime as datetime_field    
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

class intervent_report_create_wizard(osv.osv_memory):
    ''' Wizard for create new intervent from invoice and linked to the document
    '''
    _name = "intervent.report.create.wizard"
    _description = "Wizard intervent creation"
        
    def get_account_id(self, cr, uid, context=None):
        ''' Funzione che recupera l'id conto analitico 
            cercando un conto analitico con code="EXPLAN"
        '''
        # 1. cerchi in account.analytic.account il codice "EXPLAN"
        # 2. testi la lista di ritorno
        #        return item_id[0]
        #    else: 
        #        return oggetto.create 
        
        item_id = self.pool.get("account.analytic.account").search(cr, uid, [
            ('code', '=', 'EXPLAN'),
            ], context=context)
        if item_id:
            return item_id[0]
        else:
            item_id = self.pool.get("account.analytic.account").create(
                cr, uid, {
                   'name':'Conto Explan', 
                   'type':'normal',
                   'use_timesheets':True,
                   'code':'EXPLAN',
                   }, context=context)
            return item_id
            
    def button_create(self, cr, uid, ids, context=None):
        ''' Create intervent
        '''
        if context is None:
            context = {}
        
        wiz_proxy = self.browse(cr, uid, ids)[0]    
        data = {
            'intervention_request':'Richiesta telefonica intervento',
            #'code':'Codice intervento',
            #'date_end',
            'google_from': 'company',
            'manual_total': False,
            'user_id': context.get('trip_user_id', False), 
            'google_to': 'company',
            'trip_require': wiz_proxy.mode == "customer",
            'intervent_partner_id': wiz_proxy.partner_id.id,
            'partner_id': wiz_proxy.partner_id.id,
            'break_require': False,
            'not_in_report': True,
            'name': 'Richiesta intervento generico',
            'mode': wiz_proxy.mode,
            'invoice_id': False,
            'intervent_duration': wiz_proxy.intervent_duration,
            'manual_total_internal': False,
            'extra_planned': True,
            'trip_id': context.get('active_id', False),
            #'message_ids': '',
            'trip_hour': wiz_proxy.partner_id.trip_duration,
            'date_start': wiz_proxy.datetime,
            'date': wiz_proxy.datetime[:10],
            'state': 'close',
            'intervention': 'Intervento generico',
            'ref': '', #TODO vedere se inserirlo
            'break_hour': 0.0,
            #'move_id': '',
            'internal_note': '',
            #'amount': '', #TODO
            #'unit_amount':, #TODO
            'intervent_total': 
                wiz_proxy.intervent_duration + \
                wiz_proxy.partner_id.trip_duration \
                    if wiz_proxy.mode == "customer" else 0.0,
            #'line_id': '',
            #'to_invoice': , #TODO
            'account_id': self.get_account_id(cr, uid, context=context) , #wiz_proxy.account_id.id,
            }
        
        res = self.pool.get ("hr.analytic.timesheet").on_change_user_id(
            cr, uid, [], data['user_id'],)
        data.update(res.get('value', {}))
        self.pool.get ("hr.analytic.timesheet").create(
            cr, uid, data, context=context)    
        self.pool.get("hr.analytic.timesheet.trip").calculate_step_list(
            cr, uid, [data['trip_id']], context=context)
        return False
        
    def onchange_datetime(self, cr, uid, ids, dt, context=None):
        ''' Read the appointment list of user for date selected 
        '''
        if context is None:
            context = {}
                      
        res = {"value": {}, 'warning': {}}
        user_id = context.get('trip_user_id', False) # context passed from button in hr.analytic.timesheet.trip and then from on_change function
        trip_date = context.get('trip_date', False)  # context passed from button in hr.analytic.timesheet.trip and then from on_change function
        
        if dt[:10] != trip_date:            
            res['warning']['title'] = 'Attenzione:'
            res['warning']['message'] = \
                'Utilizzare come data la data del viaggio: %s' % trip_date
            #dt="%s %s" %(trip_date, dt[11:])    
            return res 
            
        if user_id and dt:            
            intervent_pool = self.pool.get("hr.analytic.timesheet")
            domain = [
                ('user_id','=', user_id),
                ('date_start', '>=', "%s 00:00:00" % dt[:10]),
                ('date_start', '<=', "%s 23:59:59" % dt[:10]),
                ]
            intervent_ids = intervent_pool.search(cr, uid, domain)
            situation = ""       
            for rapportino in intervent_pool.browse(
                    cr, uid, intervent_ids, context=None):                
                date_start = datetime_field.context_timestamp(cr, uid,
                    timestamp=datetime.strptime(
                        rapportino.date_start, DEFAULT_SERVER_DATETIME_FORMAT),
                    context=context)
                date_start = date_start.strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)

                situation += "%s [%.2f] %s %s\n" % (
                    date_start[-8:], 
                    rapportino.intervent_duration,
                    rapportino.intervent_partner_id.name, 
                    "DAL CLIENTE" if \
                        rapportino.mode == "customer" else "IN AZIENDA")
            res["value"]["situation"]=situation
            #res["value"]["datetime"]=datetime

        return res
    
    def default_datetime(self, cr, uid, context=None):
        ''' Funzione che calcola dalla data il valore di default
        '''
        #import pdb; pdb.set_trace()
        return "%s 08:00:00" %(context.get('trip_date',False))
         
    _columns = {
        #'user_id': fields.many2one('res.users', 'User', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'datetime': fields.datetime('Data e ora', required=True),
        #'account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=False, required=True),
        'name': fields.char('Descrizione', size=64, required=True, select=True),
        'mode': fields.selection([
            ('phone','Phone'),
            ('customer','Customer address'),
            ('connection','Tele assistence'),
            ('company','Company address'),
            ],'Mode', select=True, required=True),        
        'situation': fields.text('User situation',),
        'intervent_duration': fields.float(
            'Intervent duration', digits=(8, 2), required=True),
        }

    _defaults = {
        'intervent_duration': lambda *a: 1.0,
        'name': lambda *a: 'Intervento generico',
        'mode': lambda *a: 'customer',
        'datetime': lambda s, cr, uid, c: s.default_datetime(cr, uid, context=c),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

