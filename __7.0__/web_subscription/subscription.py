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

from osv import osv, fields

class product_product(osv.osv):
    '''
    '''  
    _name = 'product.product'
    _inherit = 'product.product'
    
    _columns={
        'is_periodic':fields.boolean('Is periodic'),
             }
    
    _defaults={
        'is_periodic':lambda *a:False,          
              }

class res_partner_web_subscription(osv.osv):
    '''
    '''
    
    _name = 'res.partner.web.subscription'
    _description = ''
    
    _columns={
        'name':fields.char('Name', size=50, required=True),
        'period':fields.integer('Periodo in mesi'),
        'deadline':fields.date('Scadenza'),
        'pay_date':fields.date('Data di pagamento'),
        'amount':fields.float('Importo'),
        'product_id':fields.many2one('product.product','Subscription type'),
        'web_id':fields.many2one('res.partner.web', 'Website'),
             }

    _defaults={
        'period':lambda *a:12,    
              }
            
class res_partner_web(osv.osv):
    '''
    '''
    _name = 'res.partner.web'
    _inherit = 'res.partner.web'
    
    _columns={
        'subscription_ids':fields.one2many('res.partner.web.subscription', 'web_id', 'Subscription'),     
             }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
