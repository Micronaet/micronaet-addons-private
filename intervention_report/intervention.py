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


class account_analytic_account(osv.osv):
    """ Add extra fields to account.analytic.account
    """
    _inherit = 'account.analytic.account'
    
    _columns = {
        'default_to_invoice': fields.many2one('hr_timesheet_invoice.factor', 'Default invoice', help = "Defaulf invoice type if there's one active for customer. All intervent are, for default, setted to this value"),        
        'total_hours': fields.float('Total hour', digits = (16, 2), help = "Total hour for this contract for all period"),        
        'is_extra_report': fields.boolean('Extra report', 
            help='Hided in reports'),
        #'request_by':fields.char('Request by', size=100, 
        #    help='List of people that request intervent'
        #    ),
        #'request_reference':fields.char('Request reference', size=200, 
        #    help='Reference for request (asana link, mail ecc.)',
        #    ),            
        }

class res_partner_extra_fields(osv.osv):
    """ Add extra field to partner for intervent manage
    """
    _inherit = 'res.partner'
    
    _columns = {
        'trip_duration': fields.float('Trip duration', digits=(16, 2), 
            help="Trip hour duration dealed with the partner"),
        'has_contract': fields.boolean('Has contract', 
            help="Contract for assistence, if yes compile also the analytic account"),
        'default_contract_id': fields.many2one('account.analytic.account', 
            'Default Contract', 
            help="Defaulf contract if there's one active for customer. All intervent are, for default, setted to this value"),
        }

class hr_analytic_timesheet_extra(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _inherit = 'hr.analytic.timesheet'
    _order = 'date_start'
    
    def unlink(self, cr, uid, ids, context=None):
        """ Override to correct remove intervent from calendar
        """   
        # delete thread before:
        if type(ids) not in (list, tuple):
            ids = [ids]
            
        msg_ids = self.pool.get('mail.message').search(cr, uid, [
            ('model','=','hr.analytic.timesheet'),
            ('res_id','in',ids)], context=context)
        self.pool.get('mail.message').unlink(cr, uid, msg_ids, context=context)
        return super(hr_analytic_timesheet_extra, self).unlink(
            cr, uid, ids, context)
        
    # Workflow function:
    def force_confirmation(self, cr, uid, ids, context = None):
        ''' Test if is not present ref, calculate and change status
        '''
        data={'state': 'reported',}
        ref=self.get_sequence_if_not_present(cr, uid, ids, context=context)
        if ref:
            data['ref']=ref
        self.write(cr, uid, ids, data) 
        return True


    def intervention_draft(self, cr, uid, ids, context = None):
        self.write(cr, uid, ids, {'state': 'draft',}) 
        return True

    def intervention_waiting(self, cr, uid, ids, context = None):
        self.write(cr, uid, ids, {'state': 'waiting',}) 
        return True

    def intervention_confirmed(self, cr, uid, ids, context = None):
        ''' Test if is not present ref, calculate and change status
        '''
        data={'state': 'confirmed',}
        ref=self.get_sequence_if_not_present(cr, uid, ids, context=context)
        if ref:
            data['ref']=ref
        self.write(cr, uid, ids, data) 
        return True

    def intervention_cancel(self, cr, uid, ids, context = None):
        self.write(cr, uid, ids, {'state': 'cancel',})
        return True

    def intervention_close(self, cr, uid, ids, context = None):
        self.write(cr, uid, ids, {'state': 'close',})
        return True

    def intervention_report_close(self, cr, uid, ids, context = None):
        ''' Test if is not present ref, calculate and change status
        '''
        self.write(cr, uid, ids, {'state': 'reported',})
        return True
    
    # Utiliy function for workflow:
    def get_sequence_if_not_present(self, cr, uid, ids, context = None):
        ''' test if ids element don't have ref setted, if not get next value
        '''
        item_proxy=self.browse(cr, uid, ids[0], context=context)
        if not item_proxy.ref:
           return self.get_intervent_number(cr, uid, context = context)
        return False

    def intervention_report_send_and_close(self, cr, uid, ids, context = None):
        ''' This function opens a window to compose an email, with the intervent template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'intervention_report', 'email_template_timesheet_intervent')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'hr.analytic.timesheet',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_intervent_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    # On change event:
    def on_change_name(self, cr, uid, ids, name, intervention_request, context = None):
        ''' Test if change name, then write it in intervention_request if empty
            No changes if name is empty
        '''
        if name and (not intervention_request or intervention_request=="Nuovo evento"):
           return {'value': {'intervention_request':name}}
        return {}

    def on_change_mode(self, cr, uid, ids, mode, context = None):
        ''' If change mode:
            test if is customer so trip is required
        '''
        res={}
        res['value']={'trip_require': mode == 'customer'} # True if customer
        return res

    def on_change_partner(self, cr, uid, ids, partner_id, account_id, context = None):
        ''' If change partner:
            set up account_id if there's default 
            change trip hour if mode setted up to 'customer'        
        '''  
        res={}
        res['value']= {}
        if not partner_id:
            res['value']['account_id'] = False
            res['value']['trip_hour'] = 0.0
            return res

        partner_proxy=self.pool.get("res.partner").browse(cr, uid, partner_id, context=context)
        res['value']['account_id'] = partner_proxy.default_contract_id.id if partner_proxy.default_contract_id else False
        res['value']['trip_hour'] = partner_proxy.trip_duration # hide if non required
        return res

    def on_change_account(self, cr, uid, ids, account_id, partner_id, 
            user_id=False, context=None):
        ''' Test if change account, then write, if present, to_invoice field
        '''
        res = {'value': {'partner_id': partner_id}} # default
        account_pool = self.pool.get('account.analytic.account')
        intervent_pool = self.pool.get('hr.analytic.timesheet')
        if account_id:
            account_proxy = account_pool.browse(
                cr, uid, account_id, context=context)
           
            # change only if present (else default pay intervent)    
            if account_proxy.default_to_invoice: 
                res['value']['to_invoice'] = account_proxy.default_to_invoice.id
               
                # -------------------
                # Status of contract:
                # -------------------
                intervent_ids = intervent_pool.search(cr, uid, [
                    ('account_id', '=', account_id),
                    ('state', '!=', 'cancel'),
                    ], context=context)
                total = sum(
                    [item.intervent_total for item in intervent_pool.browse(
                        cr, uid, intervent_ids, context=context)])    
                    
                try:    
                    res['value']['account_hour_status'] = ("%6.2f / %6.2f" % (
                        total,
                        account_proxy.total_hours,
                        )) if account_proxy.total_hours else False
                except:        
                    res['value']['account_hour_status'] = 'Error' 
               
        else: # return default value if empty
            res['value']['to_invoice'] = self.get_default_invoice_value(
                cr, uid, context=context)
            res['value']['account_hour_status'] = False
           
        return res

    def on_change_duration_elements(self, cr, uid, ids, intervent_duration,
            manual_total, manual_total_internal, trip_require, trip_hour,
            break_require,break_hour,context=None):
        ''' Calculate total duration and total intenal duration depending on 
            parameter passed
            (TODO: cost)
        '''
        res = {'value': {}}

        total = (
            intervent_duration or 0.0) - (
                break_hour if break_require else 0.0) + (
                    trip_hour if trip_require else 0.0)
            
        if not manual_total:
            res['value']['intervent_total'] = total
        if not manual_total_internal:
            res['value']['unit_amount'] = total
        return res        
        
    # default function:
    def get_default_invoice_value (self, cr, uid, context = None):
        ''' Get default invoice depend on xml data imported with module
        '''
        ids = self.pool.get('ir.model.data').search(cr, uid, [
           ('model', '=', 'hr_timesheet_invoice.factor'),
           ('name', '=', 'working_intervent_100')], context=context)
        if ids:
            res_id=self.pool.get('ir.model.data').read(cr, uid, ids, ('id','res_id'), context=context)            
            return res_id[0]['res_id']
        return # nothing (no default)    
    
    def get_intervent_number(self, cr, uid, context = None):
        ''' Get intervent sequence number
        '''
        res = self.pool.get('ir.sequence').get(cr, uid, 'hr.intervent.report')
        return res
       
    _columns={
        'ref':fields.char('Ref.', size=12, required=False, readonly=False, 
            help="ID for intervent, actually manually configured, after became a sequence"),
        'intervent_partner_id': fields.many2one('res.partner', 'Partner ref.'),
        'intervention_request': fields.text('Intervention request', 
            help="Keep track of the origina request"),
        'intervention': fields.text('Intervention description', 
            help="All description of the intervent, used for print report"),
        'internal_note': fields.text('Internal note', 
            help="Note for save some impression, no comunication to customer"),
        'date_start': fields.datetime('Date start'), # TODO check definition for data (override this?)
        'date_end': fields.datetime('Date end'),         # TODO evauluate if necessari
        'intervent_duration': fields.float('Duration intervent', 
            digits=(16, 6), help="Duration intervent without trip"),
        'intervent_total': fields.float('Duration intervent', digits=(16, 6), 
            help = "Duration intervent considering trip and break used for invoice (q. for customer)"),
        'manual_total':fields.boolean('Manual', required=False, 
            help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        'manual_total_internal':fields.boolean('Manual (internal)', 
            help="If true don't auto calculate total internal hour, if false, total hours=intervent + trip - pause hours"),
        'user_name': fields.related('user_id', 'name', type = 'char', 
            string='User'),
        'trip_require':fields.boolean('Trip'),
        'trip_hour': fields.float('Trip hour', digits=(16, 6)),
        'break_require': fields.boolean('Break',
            help='If intervention is split in 2 part for break'),
        'break_hour': fields.float('Break hour', digits=(16, 6), 
            help='Duration of break'),

        'extra_invoiced_total': fields.float('Duration of extra invoiced', 
            digits=(16, 3), 
            help = 'Extra invoiced of this contract intervent'),

        'request_by':fields.char('Request by', size=100, 
            help='List of people that request intervent'
            ),
        'request_reference':fields.char('Request reference', size=200, 
            help='Reference for request (asana link, mail ecc.)',
            ),            
        
        # Function fields (populated only in view not in DB:    
        'account_hour_status': fields.char('Account status', size=40),
            
        # Google maps trip manage:
        'google_from':fields.selection([
            ('previous','Previous'),
            ('home','Home'),
            ('company','Company'),
            ],'From', select=True, readonly=False, help = "Used for auto trace route 'from' with google maps"),        
        'google_to':fields.selection([
            ('next','Next'),
            ('home','Home'),
            ('company','Company'),
            ],'To', select=True, readonly=False, help = "Used for auto trace route 'to' with google maps"),        
        # Valutare se tenere:
        #'type_id':fields.many2one('intervention.type', 'Type', required=False),  
        # TODO valutare se è il caso di tenere un prodotto per il settore
        #'sector_id':fields.many2one('intervention.sector', 'Sector', required=False, help = "List of sector of intervent, used in sector study for division of activity intervents"),
        'not_in_report':fields.boolean('Not in report', 
            help = "It's not printed in monthly report"),
        'mode':fields.selection([
            ('phone','Phone'),
            ('customer','Customer address'),
            ('passenger','Customer (passenger)'),
            ('connection','Tele assistence'),
            ('company','Company address'),
            ], 'Mode', select=True, required=True),
        'state':fields.selection([
            ('cancel', 'Cancelled'),               # Appointment cancel
            ('draft', 'Draft'),                    # Intervent / appointment marked on agenda
            ('waiting', 'Await confirm'),  # Appointment await confirm from customer
            ('confirmed', 'Confirmed'),            # Appointment confirmet
            ('close', 'Close'),                 # Appointment close without sending intervent report
            ('reported', 'Close reported'),     # Appointment close with sending intervent report
        ],'State', select=True, readonly=True),    
        'extra_planned':fields.boolean('Extra Planned'),
    }
    
    _defaults={
         # set working data from xml file as default
         'name': lambda *a: False,
         'to_invoice': lambda s, c, uid, ctx: s.get_default_invoice_value(c, uid, context=ctx),
         #'ref': lambda s, c, uid, ctx: s.get_intervent_number(c, uid, context=ctx),
         'state': lambda *a: 'draft',
         'mode': lambda *a: 'connection',
         'manual_total': lambda *x: False,
         #'user_id': lambda obj, cr, uid, context: uid,
    }

class mail_compose_intervent_message(osv.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context = None):
        import netsvc
        context = context or {}
        if context.get('default_model') == 'hr.analytic.timesheet' and context.get('default_res_id') and context.get('mark_intervent_as_sent'):
            context = dict(context, mail_post_autofollow=True)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'hr.analytic.timesheet', context['default_res_id'], 'intervention_report_close', cr)
        return super(mail_compose_intervent_message, self).send_mail(cr, uid, ids, context=context)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
