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

import logging
from osv import fields, osv
from datetime import datetime

_logger = logging.getLogger(__name__)


class hr_analytic_timesheet_trip_wizard(osv.osv_memory):
    """ Wizard: select range of date
                select user or all
                Generate trip element per day used for compute trip
    """

    _name = "hr.analytic.timesheet.trip.wizard"

    # Button function:
    def create_trip(self, cr, uid, ids, context=None):
        """ Create trip for chosen day and users (deleting previous elements)
        """
        # Pool used:
        trip_pool = self.pool.get('hr.analytic.timesheet.trip')

        _logger.warning('Cleaning cache for this generation:')
        trip_pool._map_cache = {}

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        domain = [
            ('mode', '=', 'customer'),
        ]  # todo what about state?
        if not wiz_proxy.all_user:
            domain.append(
                ('user_id', '=', wiz_proxy.user_id.id))
        if wiz_proxy.from_date:
            domain.append(
                ('date_start', '>=', "%s 00:00:00" % wiz_proxy.from_date))
        if wiz_proxy.to_date:
            domain.append(
                ('date_start', '<', "%s 00:00:00" % wiz_proxy.to_date))

        date_list_for_user = {}
        user_get_from_id={}

        user_ids = self.pool.get("res.users").search(cr, uid, [
            ('compute_office_trip', '=', True),
            ], context=context)
        for user in self.pool.get("res.users").browse(
                cr, uid, user_ids, context=context):
            date_list_for_user[user.id] = []
            user_get_from_id[user.id] = user.name

        intervent_pool = self.pool.get('hr.analytic.timesheet')
        trip_pool = self.pool.get('hr.analytic.timesheet.trip')

        intervent_ids = intervent_pool.search(
            cr, uid, domain, order="date_start", context=context)
        intervent_proxy = intervent_pool.browse(
            cr, uid, intervent_ids, context=context)

        trip_list = []  # used to reactivate or compute google trip km
        for intervent in intervent_proxy:
            # save day if user is a compunte office trip:
            if (intervent.user_id.id in date_list_for_user) and (
                    intervent.date_start[:10] not in
                    date_list_for_user[intervent.user_id.id]):
                # todo non aggiungere se la commessa è di ferie!!!!!
                #  (calcolare se l'orario è uguale a 8 ore!!!
                date_list_for_user[intervent.user_id.id].append(
                    intervent.date_start[:10])

            # search or create intervent:
            trip_id = trip_pool.search(cr, uid, [
                ('date', '=', intervent.date_start[:10]),
                ('user_id', '=', intervent.user_id.id)
                ], context=context)
            if not trip_id:  # create trip_header before:
                trip_id = trip_pool.create(cr, uid, {
                    'date': "%s-%s-%s" % (
                        intervent.date_start[:4],
                        intervent.date_start[5:7],
                        intervent.date_start[8:10],
                        ),
                    'user_id': intervent.user_id.id,
                    'name': "%s [%s]" % (
                        intervent.date_start[:10],
                        intervent.user_id.name,
                        ),
                    'refund_day': intervent.user_id.refund_user,
                    }, context=context) # draft mode

            else: # find list (one only)
                if len(trip_id) != 1:
                    # todo comunicate error
                    trip_id = trip_id[0]
                else:
                    trip_id = trip_id[0]
            if intervent.trip_id.id != trip_id:
                intervent_pool.write(cr, uid, intervent.id, {
                    'trip_id': trip_id,
                    }, context=context)  # associate trip_id to intervent
                # todo reactivate WF

            if trip_id not in trip_list:
                trip_list.append(trip_id)

        # todo Add day for office work: #######################################
        from datetime import datetime, timedelta
        if wiz_proxy.from_date and wiz_proxy.to_date:
            from_parse_date = datetime.strptime(
                wiz_proxy.from_date, "%Y-%m-%d")
            to_parse_date = datetime.strptime(
                wiz_proxy.to_date, "%Y-%m-%d")
            if from_parse_date < to_parse_date:
                while from_parse_date != to_parse_date:  # jump last day
                    # todo verificare se è sabato!
                    day = from_parse_date.strftime("%Y-%m-%d")
                    for key in date_list_for_user: # for all users:
                        # work day not present
                        if (datetime.weekday(from_parse_date) in [
                               0, 1, 2, 3, 4]) and (day not in
                                                    date_list_for_user[key]):
                            # Create empty trip
                            trip_ids = trip_pool.search(cr, uid, [
                                ('date', '=', day),
                                ('user_id', '=', key),
                                ], context=context)

                            if trip_ids:  # create trip_header before:
                                trip_id = trip_ids[0]
                            else:
                                trip_id = trip_pool.create(cr, uid, {
                                    'date': "%s-%s-%s" % (
                                        day[:4], day[5:7], day[8:10]),
                                    'user_id': key,
                                    'name': "%s [%s]" % (
                                        day, user_get_from_id[key]),
                                    'refund_day': False,  # no trip refunded
                                }, context=context)  # draft mode
                            trip_list.append(trip_id)
                    # next day
                    from_parse_date = from_parse_date + timedelta(days=1)

        # Regenerate all step for trip computation:
        trip_pool.calculate_step_list(cr, uid, trip_list, context=context)
        return True

    # On change function:
    def on_change_month(self, cr, uid, ids, month, context=None):
        """
        """
        import time

        res = {'value': {}}
        if month:
            res['value'] = {
                'from_date': "%s-%02d-01 00:00:00" % (
                    time.strftime('%Y'), int(month)),
                'to_date': "%04d-%02d-01 00:00:00" % (
                    int(time.strftime('%Y')) if month != "12"
                    else int(time.strftime('%Y')) + 1,
                    int(month) + 1 if month != "12" else 1,)
                }

        return res

    _columns = {
        'all_user': fields.boolean('All user'),
        'user_id': fields.many2one('res.users', 'User'),
        'from_date': fields.date('From date (>=)', required=True),
        'to_date': fields.date('To date (<)', required=True),

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
        ], 'Month', select=True),
    }
    _defaults = {
        'all_user': lambda *a: True,
        'month': lambda *a: "%02d" % (
            int(datetime.now().strftime('%m')) - 1) if
        datetime.now().strftime('%m') != '01' else '12',  # prev. month
    }
