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
from openerp import SUPERUSER_ID


_logger = logging.getLogger(__name__)

state_list = [
    ('draft', 'Draft'),
    ('todo', 'To do'),
    ('assigned', 'Assigned'),
    ('returned', 'Return to sender'),
    ('working', 'Working'),
    ('completed', 'Completed'),
    ('cancel', 'Cancel'),
]

class task_sector(osv.osv):
    ''' List of possibile sector of activity
    '''
    _name = 'task.sector'
    _description = 'Task sector'
    _order = 'name'

    _columns = {
        'name': fields.char('Sector', size=64, required=True, readonly=False),
        'manager_id': fields.many2one('res.users', 'Manager for the sector', required=True, help="Set up also manager for task intervent"),
        'note': fields.text('Note', help="Note about sector"),
    }

class task_sector_category(osv.osv):
    ''' List of possibile sector of activity
    '''
    _name = 'task.sector.category'
    _description = 'Task sector category'
    _order = 'name'

    _columns = {
        'name': fields.char('Sector', size=64, required=True, readonly=False),
        'sub_manager_id': fields.many2one('res.users', 'Manager for the sector', 
            required=False, 
            help="Set up also manager for task intervent, empty set sector manager"),
        'sector_id': fields.many2one('task.sector', 'Sector', required=False),
        'note': fields.text('Note', help="Note about sector category"),
    }

class task_sector(osv.osv):
    ''' *2many fields
    '''
    _name = 'task.sector'
    _inherit = 'task.sector'

    _columns = {
        'category_ids':fields.one2many('task.category', 'sector_id', 
            'Category', required=False),
    }

class task_customer_state(osv.osv):
    ''' List of possibile humor state for customer
    '''
    _name = 'task.partner.mood'
    _description = 'Partner mood'
    _order = 'name'

    _columns = {
        'name': fields.char('Mood', size=64, required=True, readonly=False),
        'note': fields.text('Note', help="Note about partner mood"),
    }

class task_media(osv.osv):
    ''' List of possibile media for start the tasks and close the task
    '''
    _name = 'task.media'
    _description = 'Task receive media'
    _order = 'name'

    _columns = {
        'name': fields.char('Media', size=64, required=True, readonly=False),
        'note': fields.text('Note', help="Note about media that generate task"),
    }


class task_activity(osv.osv):
    ''' Master task activity
    '''
    _name = 'task.activity'
    _description = 'Task activity'
    _order = 'priority,deadline_date'
    _inherit = ['mail.thread']

    # --------------------------------------------------------------------------
    #                              Utility function
    # --------------------------------------------------------------------------
    def write_thread_note(self, cr, uid, task_ids, context=None):
        ''' Write info in thread list (used in WF actions)
        '''
        task_proxy = self.browse(cr, uid, task_ids, context=context)[0]

        # Default part of message:
        message = { 
            'subject': _("Task %s: %s") % ( #_("Task [[ID#%s]]: %s [%s]") % (
                task_proxy.state,
                task_proxy.name,
                #task_proxy.id,
                ),
            'body': _("Changing state comunication"),
            #'type': 'notification',
            'type': 'comment',
            #'type': 'email',
            'subtype': False,  #parent_id, #attachments,
            'content_subtype': 'html',
            'partner_ids': [],            
            'email_from': 'openerp@micronaet.it', #wizard.email_from,
            'context': context,
            }
        if task_proxy.state == 'assigned':
            # Set notification for worker
            message['partner_ids'].append(task_proxy.assigned_user_id.partner_id.id)
            notification = True 
            
            # Change message:
            message.update({
                #'type': 'comment',
                'body': _(
                    "Worker: <b>%s</b><br/>"
                    "Deadline: <b>%s [Dur. %s]</b><br/>"
                    "Ref.: <b>%s</b><br/>"
                    "Priority: %s"
                    "%s") % (
                        task_proxy.assigned_user_id.name,
                        task_proxy.deadline_date,
                        task_proxy.max_duration,                    
                        task_proxy.sequence or "",
                        task_proxy.priority or "",
                        _("<br/>Partner: %s") % task_proxy.partner_id.name if task_proxy.partner_id else "",
                        ), })

            # Put assigned as follower:
            self.message_subscribe_users(
                cr, uid, task_ids, 
                user_ids=[uid, task_proxy.assigned_user_id.id, ],# me and assigned
                context=context)
        elif task_proxy.state in ('completed', 'working', 'returned', 'cancel', 'todo'):
            # Set notification for manager
            message['partner_ids'].append(task_proxy.manager_user_id.partner_id.id)
            notification = True
            
        else: # other states (draft, todo (restart)) 
            notification = False
                        
        msg_id = self.message_post(cr, uid, task_ids, ** message)

        if notification: 
            _logger.info(">> Send mail notification! [%s]" % message['partner_ids'])
            self.pool.get(
                'mail.notification')._notify(cr, uid, msg_id, 
                message['partner_ids'], 
                context=context
                )       

    def get_activity_sequence(self, cr, uid, context = None):
        ''' Get activity sequence number
        '''
        res = self.pool.get('ir.sequence').get(cr, uid, 'task.activity')
        return res

    def get_user_from_email(self, cr, uid, email, context=None):
        ''' Return user id for the mail passed, else administrator 
        '''
        try:
            if email:
                email = email.split("<")[-1].split(">")[0]
                user_id = self.pool.get('res.users').search(cr, uid, [('email','=',email)], context=context)
                if user_id:
                    return user_id[0]
        except: 
            pass
        return SUPERUSER_ID
        
    # --------------------------------------------------------------------------
    #                              Mail-Gateway function
    # --------------------------------------------------------------------------
    #def message_new(self, cr, uid, msg, custom_values=None, context=None):
    #    """ Overrides mail_thread message_new that is called by the mailgateway
    #        through message_process.
    #        This override updates the document according to the email.
    #    """
    #    #desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
    #    #TODO
    #    defaults = {
    #        'name':  "Oggetto", #msg.get('subject') or _("No Subject"),
    #        'description': "Descrizione", #desc,
    #        'email_from': "openerp@micronaet.it", #msg.get('from'),
    #        'email_cc': "nicola.riolini@gmail.com", #msg.get('cc'),
    #        'partner_id': 1, #msg.get('author_id', False),
    #        'user_id': False,
    #    }
    #    defaults.update(custom_values)
    #    return  super(task_activity, self).message_new(cr, uid, msg, custom_values=defaults, context=context)

    '''def message_post(self, cr, uid, thread_id, **kwargs):
        """ Override related to hr.analytic.timesheet. In case of email message, set it as
            private:
            - add the target partner in the message partner_ids
            - set thread_id as None, because this will trigger the 'private'
                aspect of the message (model=False, res_id=False)
        """
        #if kwargs.get('type') == 'email':
        #    partner_ids = kwargs.get('partner_ids', [])
        #    if thread_id not in [command[1] for command in partner_ids]:
        #        partner_ids.append((4, thread_id))
        #    kwargs['partner_ids'] = partner_ids
        #    thread_id = False
        
        try:
            user_id = self.get_user_from_email(cr, uid, kwargs.get('from', False))<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            self.create(cr, uid, {
                'name': kwargs.get('subject', _('New request')),
                'start_date': kwargs.get('date', datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                'note': kwargs.get('body', False),
                'user_id': user_id,
                'assigned_user_id': user_id,
            }, context=context)
            return True #super(task_activity, self).message_post(cr, uid, thread_id, **kwargs)
        except:
            raise osv.except_osv(_('Error!'), _('Error downloading email.'))
        return     '''

    # --------------------------------------------------------------------------
    #                               Workflow event
    # --------------------------------------------------------------------------
    def activity_draft(self, cr, uid, ids, context=None):
        ''' Task activity draft
        '''
        return self.write(cr, uid, ids, {
            'state': 'draft',
            'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'todo_date': False,
            'working_date': False,
            'assigned_date': False,
            'completed_date': False,
            })

    def activity_todo(self, cr, uid, ids, context=None):
        ''' Task activity active
        '''
        data = {
            'state': 'todo', 
            'todo_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'return_date': False,
            }

        # Insert sequence only if exit draft state:
        if not self.browse(cr, uid, ids, context=context)[0].sequence:
            data['sequence'] = self.get_activity_sequence(
                cr, uid, context=context)

        self.write(cr, uid, ids, data, context=context)

        # Write mail.thread info
        self.write_thread_note(cr, uid, ids, context=context)
        return True

    def activity_assigned(self, cr, uid, ids, context=None):
        ''' Task activity assigned
        '''
        self.write(cr, uid, ids, {
            'state': 'assigned',
            'assigned_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'return_date': False,
            })
        self.write_thread_note(cr, uid, ids, context=context)
        return True

    def activity_returned(self, cr, uid, ids, context=None):
        ''' Task activity return to sender not completed
        '''
        self.write(cr, uid, ids, {
            'state': 'returned',
            'return_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'assigned_date': False,
            'working_date': False,            
            })
        self.write_thread_note(cr, uid, ids, context=context)
        return True

    def activity_working(self, cr, uid, ids, context=None):
        ''' Task activity working
        '''
        self.write(cr, uid, ids, {
            'state': 'working',
            'working_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        self.write_thread_note(cr, uid, ids, context=context)
        return True

    def activity_completed(self, cr, uid, ids, context=None):
        ''' Task activity completed
        '''
        self.write(cr, uid, ids, {
            'state': 'completed',
            'completed_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        self.write_thread_note(cr, uid, ids, context=context)
        return True

    def activity_cancel(self, cr, uid, ids, context=None):
        ''' Task activity cancel
        '''
        self.write(cr, uid, ids, {
            'state': 'cancel',
            # No data modification
            })
        self.write_thread_note(cr, uid, ids, context=context)
        return True

    _columns = {
        'sequence': fields.char('Ref.', size=14, required=False, 
            readonly=True),
            
        # TODO remove:
        #'email_cc': fields.char('Title', size=64, required=False, readonly=False),
        #'email_from': fields.char('Title', size=64, required=False, readonly=False),
        #'description': fields.char('Title', size=64, required=False, readonly=False),
        #'returned_date': fields.datetime('Date'),
        # TODO
        
        'name': fields.char('Title', size=64, required=True, 
            readonly=False),
        'note': fields.text('Description', 
            help="Large description of activity"),
        'obsolete':fields.boolean('Obsolete', required=False, 
            help="Hide task for old elements that don't need to be showed"),

        #TODO : import time required to get currect date
        # Workflow date event:
        'start_date': fields.datetime('Creation date'),
        'todo_date': fields.datetime('To do date'),
        'assigned_date': fields.datetime('Assigned date'),
        'working_date': fields.datetime('Working date'),
        'return_date': fields.datetime('Return'),
        'completed_date': fields.datetime('Completed'),
        # Partner date info:
        'deadline_date': fields.datetime('Deadline', required=False),
        'max_duration': fields.float('Max duration', digits=(16, 2), 
            help="Max time for coplete task, extra time ask help"),
        'priority': fields.selection([
            ('locked', 'Locked'),            
            ('high', 'High'),
            ('normal', 'Normal'),
            ('low', 'Low'),
        ], 'Priority', select=True, readonly=False),
        'media_in_id': fields.many2one('task.media', 'Contact media',
            required=False, help="Media that start tasks (ex.: phone)"),
        'media_out_id': fields.many2one('task.media', 'Response media',
            required=False, help="Set the type of response (by phone, by intervent etc.)"),
        'to_recontact':fields.boolean('To recontact', required=False, 
            help="Call customer or he recall after?"),

        'partner_id': fields.many2one('res.partner', 'Partner', 
            required=False),
        'contact_id': fields.many2one('res.partner', 'Contact', 
            required=False),
        'partner_ref': fields.char('Partner reference', size=64, required=False, 
            readonly=False),

        'user_id': fields.many2one('res.users', 'Create by', required=False),
        'assigned_user_id': fields.many2one('res.users', 'Assigned to', 
            required=False),
        'manager_user_id': fields.many2one('res.users', 'Managed by', 
            required=False),
        'sector_id': fields.many2one('task.sector', 'Sector', required=False, 
            help = "Split in sector the task list"),
        'sector_category_id': fields.many2one('task.sector.category', 'Category', 
            required=False, help = "Split sector in a category list"),

        'customer_opt_in':fields.boolean('Customer opt in', required=False, 
            help="Send notification to customer of workflow work in progress"),
        'manager_opt_in':fields.boolean('Manager opt in', required=False, 
            help="Send notification to manager of workflow work in progress"),

        'parent_id': fields.many2one('task.activity', 'Parent activity', 
            required=False, help="Set a parent activity for structured tasks"),

        'perc_state': fields.float('State (100%)', digits=(5, 2)),
        'state':fields.selection(state_list, 'State', select=True, 
            readonly=True),
    }

    _defaults = {
        'obsolete': lambda *x: False,
        'state': lambda *x: 'draft',
        # User info:
        'user_id': lambda s, cr, uid, ctx: uid,
        'assigned_user_id': lambda s, cr, uid, ctx: uid,
        'manager_user_id': lambda s, cr, uid, ctx: uid,
    }

class task_activity_message(osv.osv):
    ''' Task activity message        
    '''
    _name = 'task.activity.message'
    _description = 'Task activity message'

    """def message_post(self, cr, uid, ids, **kwargs):
        ''' Raise event when fetch mail
        ''' 
        #kwargs['body'].split("[[")[1].split("]]")[0].replace("<br>", "").replace("\n","").replace("  ", " ")
        #try: # If message is linked to task, subj: subject [[TASK#1]]
        #    task_pool = self.pool.get("task.activity")
        #    task_id = task_pool.create(cr, uid, {
        #        'name': kwargs['subject'],
        #        #'user_id', msg['email_from']
        #        },)# context)            
        #except: # not a task ID message
        #    # Create new task and link there the message
        #    pass # TODO gestire bene l'errore            
        return True
        
    def message_new(self, cr, uid, msg, custom_values, context=None):
        ''' Try to identificate task and create new message or WF actions
            Subject must parsed as: "task [[TASK#1]] subject"
        '''
        #TODO debug #['body', 'from', 'attachments', 'cc', 'email_from', 'to', 'date', 'author_id', 'type', 'message_id', 'subject']
        #try: # If message is linked to task, subj: subject [[TASK#1]]
        #    msg_part = msg['subject'].split("[[")[1]
        #    msg_part = msg_part.split("]]")[0]
        #    task_id = int(msg_part.split("#")[1])
        #except: # not a task ID message
        #    # Create new task with message:
        #    #task_pool = self.pool.get("task.activity")
        #    #task_id = task_pool.create(cr, uid, {
        #    #    'name': msg['subject'],
        #    #    #'user_id', msg['email_from']
        #    #    }, context)            
        #    return False #True
        
        # TODO verificare cosa fa questa parte!!!
        #self.create(cr, uid, {
        #    'name': msg['subject'],
        #    'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        #    'user_id': SUPERUSER_ID, # Search uid from mail msg['from'],
        #    'note': msg['body'],
        #    'task_id': task_id,
        #    }, context=context)        
        return True"""
        
    # -----------------
    # Workflow trigger:
    # -----------------
    def message_draft(self, cr, uid, ids, context=None):
        ''' message activity draft
        '''
        self.write(cr, uid, ids, {'state': 'draft', })
        return True
        
    def message_done(self, cr, uid, ids, context=None):
        ''' message activity completed
        '''
        self.write(cr, uid, ids, {'state': 'done', })
        return True

    def message_internal(self, cr, uid, ids, context=None):
        ''' message activity internal
        '''
        self.write(cr, uid, ids, {'state': 'internal', })
        return True

    _columns = {
        'name': fields.char('Message', size=64, required=True, readonly=False),
        'date': fields.datetime('Creation date'),
        'user_id': fields.many2one('res.users', 'Create by', required=False),
        'note': fields.text('Details', help="Large detailed message"),
        'task_id': fields.many2one('task.activity', 'Task', required=False),
        'state':fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('internal', 'Internal'),
        ], 'State', select=True, readonly=True),
    }
    _defaults = {
        'user_id': lambda s, cr, uid, ctx: uid,
        'date': lambda *x: datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        'state': lambda *x: 'draft',
    }

class task_activity(osv.osv):
    ''' Master task activity *2many fields
    '''
    _name = 'task.activity'
    _inherit = 'task.activity'

    _columns = {
        'task_ids': fields.one2many('task.activity', 'parent_id', 
            'Child activity', required=False),
        'task_message_ids': fields.one2many('task.activity.message', 'task_id', 
            'Messages', required=False),
    }

"""class hr_analytic_timesheet_extra(osv.osv):
    def unlink(self, cr, uid, ids, context=None):
        # delete thread before:
        if type(ids) not in (list, tuple):
            ids = [ids]

        msg_ids = self.pool.get('mail.message').search(cr, uid, [('model', '=', 'hr.analytic.timesheet'),('res_id', 'in',ids)], context=context)
        self.pool.get('mail.message').unlink(cr, uid, msg_ids, context=context)
        return super(hr_analytic_timesheet_extra, self).unlink(cr, uid, ids, context)


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

class mail_compose_intervent_message(osv.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context = None):
        import netsvc
        context = context or {}
        if context.get('default_model') == 'hr.analytic.timesheet' and context.get('default_res_id') and context.get('mark_intervent_as_sent'):
            context = dict(context, mail_post_autofollow=True)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'hr.analytic.timesheet', context['default_res_id'], 'intervention_report_close', cr)
        return super(mail_compose_intervent_message, self).send_mail(cr, uid, ids, context=context)"""
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
