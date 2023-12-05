# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
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
        'timesheet_id':fields.many2one('hr.analytic.timesheet', 'Timesheet linked', required=False),#, ondelete="cascade"),
    }

class hr_analytic_timesheet_calendar(osv.osv):
    ''' Add extra fields to intervent
    '''
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'

    # -----------------
    # Utility function:
    # -----------------
    def create_meeting_linked(self, cr, uid, item_id, context=None):
        ''' Create a meeting and linked to intervent with his informations
        '''
        intervent_proxy = self.browse(cr, uid, item_id, context=context)
        meeting_pool = self.pool.get('crm.meeting')
        customer = intervent_proxy.intervent_partner_id.name if intervent_proxy.intervent_partner_id else _('Customer')
        try:
            date_deadline = meeting_pool.onchange_dates(cr, uid, 0, intervent_proxy.date_start, intervent_proxy.intervent_duration, False, False)['value']['date_deadline']
        except:
            date_deadline = intervent_proxy.date_start # duration 1 hour in case of error

        meeting_id = meeting_pool.create(cr, uid, {
            'name': "%s (%s)" % (intervent_proxy.name, customer),
            'date': intervent_proxy.date_start,
            'date_deadline': date_deadline,
            'duration': intervent_proxy.intervent_duration,
            'description': intervent_proxy.intervention,
            'user_id': intervent_proxy.user_id.id,
            'location': customer if intervent_proxy.mode == 'customer' else _('Company'),
            'timesheet_id': item_id,
        }, context=context)

        # Update intervent with link to meeting
        self.write(cr, uid, item_id, {
            'meeting_id': meeting_id,
            'meeting_sync': True,
        }, context=context)
        return

    # -------------
    # Button event:
    # -------------
    def create_linked_meeting(self, cr, uid, ids, context=None):
        ''' Create manually the link (for old intervent)
        '''
        self.create_meeting_linked(cr, uid, ids[0], context=context)
        return True

    # -------------
    # Override ORM:
    # -------------
    def create(self, cr, uid, vals, context=None):
        """
        Create a new record for a model ModelName
        @param cr: cursor to database
        @param uid: id of current user
        @param vals: provides a data for new record
        @param context: context arguments, like lang, time zone

        @return: returns a id of new record
        """
        res_id = super(hr_analytic_timesheet_calendar, self).create(cr, uid, vals, context=context)
        if vals.get('meeting_sync', False): # Create sync meeting
            self.create_meeting_linked(cr, uid, res_id, context=None)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        """
        Update redord(s) comes in {ids}, with new value comes as {vals}
        return True on success, False otherwise

        @param cr: cursor to database
        @param uid: id of current user
        @param ids: list of record ids to be update
        @param vals: dict of new values to be set
        @param context: context arguments, like lang, time zone

        @return: True on success, False otherwise
        """
        # if vals('meeting_sync', False):

        res = super(hr_analytic_timesheet_calendar, self).write(cr, uid, ids, vals, context)
        return res

    _columns = {
        # No more used!:
        'meeting_sync': fields.boolean('Sync with meeting'),
        'meeting_id': fields.many2one(
            'crm.meeting', 'Meeting linked', required=False),
        #, ondelete="set null"),
    }

    _defaults = {
        'meeting_sync': lambda *a: True,
    }
