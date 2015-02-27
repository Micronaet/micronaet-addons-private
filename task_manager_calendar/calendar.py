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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from datetime import datetime 
from tools.translate import _


class crm_meeting(osv.osv):
    ''' Add field for link to task
    '''
    _name = 'crm.meeting'
    _inherit = 'crm.meeting'
    
    _columns = {
        'task_id':fields.many2one('task.activity', 'Task linked', required=False),
    }

class task_activity(osv.osv):
    ''' Add extra field in task.manager for manage quotations
    '''
    _inherit = 'task.activity'
    _name = 'task.activity'
       
    _columns = {
        'meeting_ids': fields.one2many('crm.meeting', 'task_id', 'Meeting', required=False),
    }
    
"""class task_activity(osv.osv):
    ''' Add extra field in task.manager for manage quotations
    '''
    _inherit = 'task.activity'
    _name = 'task.activity'
    
    # Button event:
    def create_quotation(self, cr, uid, ids, context=None):
        ''' Create a new quotation wit task parameters
        '''
        task_proxy = self.browse(cr, uid, ids, context=context)[0]
        if not task_proxy.partner_id:
            raise osv.except_osv(_('Required value:'), _('Set up a partner reference for tast, mandatory for generate a quotation'))
            return True
        
        sale_pool = self.pool.get('sale.order')
        quotation_id = sale_pool.create(cr, uid, {
            'partner_id': task_proxy.partner_id.id,
            'partner_invoice_id': task_proxy.partner_id.id,
            'partner_shipping_id': task_proxy.partner_id.id,
            'task_id': task_proxy.id,            
            'client_order_ref': task_proxy.contact_id.name if task_proxy.contact_id else task_proxy.partner_ref,
            'date_deadline': task_proxy.deadline_date,
            'pricelist_id': task_proxy.partner_id.property_product_pricelist.id,
        }, context=context)
        
        return {
            'res_model': 'sale.order',
            'res_id': quotation_id,
            'view_type': 'form,tree,calendar',
            'view_mode': 'form'
        }
        
    _columns = {
        'quotation_ids':fields.one2many('sale.order', 'task_id', 'Quotations', required=False, help='Quotation generated from task'),
    }
"""    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
