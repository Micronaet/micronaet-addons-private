# -*- coding: utf-8 -*-
################################################################################
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
################################################################################

from osv import osv, fields

class account_invoice(osv.osv):
    ''' Extra fields for account.invoice
    '''
    _name='account.invoice'
    _inherit='account.invoice'
    
    def _function_summary_intervent(self, cr, uid, ids, fields, param, context=None):
        ''' In all intervention_report_ids compute:
            total to_invoice
            Description for group of intervent
        '''
        res={}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id]={}
            res[invoice.id]['to_invoice_total'] = 0.0            
            res[invoice.id]['to_invoice_summary'] = ""
            summary={}
            for intervent in invoice.intervention_report_ids:                
                if intervent.state == 'cancel':
                    continue
                
                if intervent.manual_total: # Manual intervent:
                    total_hours=intervent.intervent_total or 0.0
                else:                      # Calculate with duration, trip, break
                    total_hours=((intervent.intervent_duration) + (intervent.trip_hour if intervent.trip_require else 0.0) - (intervent.break_hour if intervent.break_require else 0.0))

                if intervent.not_in_report: # not present in report                 
                    summary_name="Not in report"
                else: 
                    summary_name=intervent.to_invoice.name
                    res[invoice.id]['to_invoice_total'] += (intervent.to_invoice.factor or 0.0) / 100 * total_hours # only if in report (total)

                if summary_name not in summary: # Summary with also not in report values
                    summary[summary_name] = total_hours or 0.0
                else:    
                    summary[summary_name] += total_hours or 0.0
            res[invoice.id]['to_invoice_total_price'] = res[invoice.id]['to_invoice_total'] * (intervent.intervent_partner_id.hour_cost if intervent.intervent_partner_id and intervent.intervent_partner_id.hour_cost else 0.0)
            for key in summary.keys():
                res[invoice.id]['to_invoice_summary'] += "%s: %s\n"%(key, summary[key])                
        return res
        
    _columns = {
        'intervention_report_ids':fields.one2many('hr.analytic.timesheet', 
            'invoice_id', 'Intervents'),
        
        'to_invoice_total': fields.function(
            _function_summary_intervent, method=True, type='float', 
            digits=(16, 2), string='Total to invoice (h)', store=False, 
            multi=True),
        'to_invoice_total_price': fields.function(
            _function_summary_intervent, method=True, type='float', 
            digits=(16, 2), string='Total to invoice (€)', 
            store=False, multi=True),
        'to_invoice_summary': fields.function(_function_summary_intervent, 
            method=True, type='text', string='Summary', store=False, 
            multi=True),
        'comment': fields.text('Internal comment'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
