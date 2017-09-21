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

from osv import fields, osv
from datetime import datetime

class account_invoice_intervent_wizard(osv.osv_memory):
    ''' Wizard: 
        Create invoice and link intervent list for print report
        Create XLSX report for sent intervent list
    '''
    _name = 'account.invoice.intervent.wizard'

    # Button function:
    def create_invoice(self, cr, uid, ids, context=None):
        ''' Create trip for choosen month for all partner in the list
        '''
        domain = [
            ('intervent_partner_id', '!=', False),
            ('extra_planned', '=', False),
            ]

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        domain.append(
            ('date_start', '>=', '%s-%s-01 00:00:00' % (
                wiz_proxy.year,wiz_proxy.month)))
            
        intervent_pool = self.pool.get('hr.analytic.timesheet')    
        invoice_pool = self.pool.get('account.invoice')
        
        intervent_ids = intervent_pool.search(
            cr, uid, domain, order='partner_id,date_start', context=context)
        intervent_proxy = intervent_pool.browse(
            cr, uid, intervent_ids, context=context)
        partner_invoice = {} # partner_id : invoice_id
        for intervent in intervent_proxy: #loop all intervent 
            # test if <= end of month
            if intervent.date_start[5:7] != wiz_proxy.month:    
                continue
            partner = intervent.intervent_partner_id    
            if partner.id not in partner_invoice:
                invoice_ids = invoice_pool.search(cr, uid, [
                    ('partner_id','=', partner.id),
                    ('date_invoice', '=', '%s-01' % (
                        intervent.date_start[:7])),
                    ], context=context)
                if invoice_ids:
                    partner_invoice[partner.id] = \
                        invoice_ids[0]
                else:
                    partner_invoice[partner.id] = \
                        invoice_pool.create(cr, uid, {
                            'name': partner.name,
                            #wiz_proxy.month,wiz_proxy.year) ,
                            'date_invoice': '%s-01' % (
                                intervent.date_start[:7]),
                            'partner_id': partner.id,
                            'account_id': \
                                partner.property_account_receivable.id,
                            }, context=context)

            mod = intervent_pool.write(cr, uid, intervent.id, {
                'invoice_id': partner_invoice[partner.id],
                }, context=context)
        return True

    _columns = {
        'year': fields.integer('Year', required=True),
        'month': fields.selection([
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),            
            ],'Month', select=True, required=True),
        }
        
    _defaults = {
        'year': lambda *a:int(datetime.now().strftime('%Y')),
        'month': lambda *a: '%02d' % (
            int(datetime.now().strftime('%m'))-1) if \
                datetime.now().strftime('%m') != '01' else '12',
        
        #'year': lambda *a: True,
        }
account_invoice_intervent_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
