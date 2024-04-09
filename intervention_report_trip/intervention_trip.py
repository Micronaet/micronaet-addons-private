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
import os
import pdb
import sys
import logging
import openerp
import urllib
import json
from osv import osv, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare,
    )

_logger = logging.getLogger(__name__)


class hr_analytic_timesheet_trip(osv.osv):
    """ Trip for intervent daily for user
    """
    _name = 'hr.analytic.timesheet.trip'
    _description = 'HR timesheet trip'
    _order = 'date,user_id'

    _map_cache = {}  # Map cache for similar calls

    # -------------------------------------------------------------------------
    # Button function (and wizard action called):
    # -------------------------------------------------------------------------
    def calculate_step_list(self, cr, uid, ids, context=None):
        """ Delete all steps an compute from intervent list
        """
        # ---------------------------------------------------------------------
        # Utility functions:
        # ---------------------------------------------------------------------
        def create_record(
                self, cr, uid, from_partner, to_partner, trip_id,
                seq, company_trip=False, context=None):
            """ Create record:
                from_id = id res.partner
                to_id = id res.partner
                trip_id = id of parent record
            """
            if to_partner and from_partner and trip_id:
                total_trip = self.distance_between_partner(
                    cr, uid, from_partner, to_partner, context=context)
                data = {
                    'from_id': from_partner.id,
                    'to_id': to_partner.id,
                    'name': '%02d. %s > %s' % (
                        seq,
                        from_partner.map_partner_name or from_partner.name,
                        to_partner.map_partner_name or to_partner.name,
                        ),
                    'total_trip': total_trip,
                    }
                if company_trip:
                    data['company_trip_id'] = trip_id
                    data['trip_id'] = False
                else:
                    data['company_trip_id'] = False
                    data['trip_id'] = trip_id

                self.pool.get('hr.analytic.timesheet.trip.step').create(
                    cr, uid, data, context=context)
                return True
            return False

        # ---------------------------------------------------------------------
        # Start procedure
        # ---------------------------------------------------------------------
        step_pool = self.pool.get('hr.analytic.timesheet.trip.step')

        # ---------------------------------------------------------------------
        # Excel log file:
        # ---------------------------------------------------------------------
        try:
            del self._excel_log
        except:
            pass

        # Create new Excel log block for manage file:
        self._excel_log = {
            'wb': self.pool.get('excel.writer'),
            'row': 0,
            'ws_name': 'Log viaggi',
            'format': {},
            }
        self._excel_log['wb'].create_worksheet(self._excel_log['ws_name'])
        self._excel_log['wb'].write_xls_line(
            self._excel_log['ws_name'],
            self._excel_log['row'],
            ['Da', 'A', 'Errore', 'Link'],
            )
        self._excel_log['row'] += 1

        for trip in self.browse(cr, uid, ids, context=context):
            # -----------------------------------------------------------------
            # COMMON PART
            # -----------------------------------------------------------------
            # Get parameters from home and company
            home_partner = trip.user_id.partner_id
            company_partner = trip.user_id.company_id.partner_id

            # delete all
            step_ids = step_pool.search(
                cr, uid, [
                    '|',
                    ('trip_id', '=', trip.id),
                    ('company_trip_id', '=', trip.id)
                    ], context=context)
            if step_ids:
                step_pool.unlink(cr, uid, step_ids, context=context)

            # -----------------------------------------------------------------
            # FROM HOME TO HOME
            # -----------------------------------------------------------------
            # Generate all the steps
            previous_partner = home_partner # Always home first start
            next_destination = False
            seq = 1
            for intervent in trip.intervent_ids:
                if intervent.mode == 'customer' and \
                        not intervent.extra_planned:  # only for customer
                    # ---------------------------------------------------------
                    # FROM part
                    # ---------------------------------------------------------
                    if intervent.google_from == 'home':
                        from_partner = home_partner

                    elif intervent.google_from == 'company':
                        if seq == 1:  # first step home-company
                            if create_record(
                                    self, cr, uid, home_partner,
                                    company_partner, trip.id, seq,
                                    context=context):
                                seq += 1
                        from_partner = company_partner

                    elif intervent.google_from == 'previous' and \
                            previous_partner:
                        from_partner = previous_partner
                    else:
                        continue  # jump intervent! # todo Error no previuos_id

                    # ---------------------------------------------------------
                    # Create part A:
                    # ---------------------------------------------------------
                    if create_record(
                            self, cr, uid, from_partner,
                            intervent.intervent_partner_id, trip.id, seq,
                            context=context):
                        seq += 1

                    # save parameters:  (next not home or company)
                    previous_partner = intervent.intervent_partner_id

                    # ---------------------------------------------------------
                    # TO part
                    # ---------------------------------------------------------
                    if intervent.google_to == 'home':
                        create_record(
                            self, cr, uid,
                            intervent.intervent_partner_id, home_partner,
                            trip.id, seq, context=context)
                        previous_partner = home_partner
                        seq += 1
                    elif intervent.google_to == 'company':
                        create_record(
                            self, cr, uid,
                            intervent.intervent_partner_id,
                            company_partner, trip.id, seq,
                            context=context)
                        previous_partner = company_partner
                        seq += 1

            # Last step (to home)
            if seq == 1:  # create home-company-home records
                create_record(
                    self, cr, uid, home_partner, company_partner,
                    trip.id, 1, context=context)
                create_record(
                    self, cr, uid, company_partner, home_partner,
                    trip.id, 2, context=context)
            else:
                # not home (last destination)
                if previous_partner != home_partner:
                    create_record(
                        self, cr, uid, previous_partner, home_partner, trip.id,
                        seq, context=context)

            # -----------------------------------------------------------------
            #                        FROM COMPANY TO COMPANY
            # -----------------------------------------------------------------
            # Generate all the steps
            previous_partner = company_partner  # Always company first step
            next_destination = False
            seq = 1
            update_refund = False
            for intervent in trip.intervent_ids:
                if intervent.mode == 'customer':  # only for customer
                    # After create step need to update refund for this trip
                    update_refund = True
                    # ---------------------------------------------------------
                    # FROM part
                    # ---------------------------------------------------------
                    if intervent.google_from in ('home', 'company'):
                        from_partner = company_partner

                    elif intervent.google_from == 'previous' \
                            and previous_partner:
                        from_partner = previous_partner
                    else:
                        continue  # jump intervent! # todo Error no previuos_id

                    # Create part A:
                    if create_record(
                            self, cr, uid, from_partner,
                            intervent.intervent_partner_id, trip.id, seq,
                            True, context=context):
                        seq += 1

                    # save parameters:  (next not home or company)
                    previous_partner = intervent.intervent_partner_id

                    # ---------------------------------------------------------
                    # TO part
                    # ---------------------------------------------------------
                    if intervent.google_to in ('home', 'company'):
                        create_record(
                            self, cr, uid,
                            intervent.intervent_partner_id,
                            company_partner, trip.id, seq,
                            True, context=context)
                        previous_partner = company_partner
                        seq += 1

            if update_refund:
                self.write(
                    cr, uid, trip.id, {
                        'refund_day': True,
                        }, context=context)

        # Return log file:
        return self._excel_log['wb'].return_attachment(
            cr, uid, 'Trip Log',
            name_of_file='trip_log', version='7.0', php=True, context=context)

    # -------------------------------------------------------------------------
    # Utility function:
    # -------------------------------------------------------------------------
    def distance_between_partner(
            self, cr, uid, origin, destination, context=None):
        """ Master function that calculate distance between origin and
            destination partner id
            NOTE: correct function evaluate start and to elements
            Use Map Quest web site (need a registration and a Key management)
        """
        # ---------------------------------------------------------------------
        # Private function:
        # ---------------------------------------------------------------------
        def prepare_element(self, cr, uid, partner, context=None):
            """ Generate a string with all address parameter used for compute
                distances
            """
            if context is None:
                context = {}

            partner_pool = self.pool.get('res.partner')
            ctx = context.copy()
            ctx['dry_run'] = True  # Force GET only if not present!

            result = partner_pool.get_lat_lon(
                cr, uid, [partner.id], context=ctx)
            return result['lon'], result['lat']

        def distance_query(self, cr, uid, origin, destination, context=None):
            """ Generate query string for compute km from origin to destination
                element in string ask for return json object
            """
            url_mask = ''
            try:
                # Note: lon1, lat1, lon2, lat2
                lon1, lat1 = prepare_element(
                    self, cr, uid, origin, context=context)
                lon2, lat2 = prepare_element(
                    self, cr, uid, destination, context=context)
                url_mask = \
                    'https://router.project-osrm.org/table/v1/' \
                    'driving/{},{};{},{}?' \
                    'sources=0'.format(lon1, lat1, lon2, lat2)
                _logger.info('Call maps quest page: %s' % url_mask)

                return url_mask
            except IOError:
                _logger.error('Error generate google page: %s' % url_mask)
                return None

        # ---------------------------------------------------------------------
        # Call Google page:
        # ---------------------------------------------------------------------
        # Read parameters:
        # company = origin.company_id
        # endpoint = company.map_endpoint
        # key = company.map_key
        # secret = company.map_secret
        # unit = company.map_route_unit
        # routeType = company.map_route_type

        error = payload = False
        distance_km = 0.0
        query = distance_query(
            self, cr, uid, origin, destination, context=context)
        try:
            if query in self._map_cache:
                distance_km = self._map_cache[query]
            else:
                reply = urllib.urlopen(query)
                response_json = reply.read()
                payload = json.loads(response_json)
        except:
            error = 'MAP Quest generic error!'

        # ---------------------------------------------------------------------
        # Check if not correct call:
        # ---------------------------------------------------------------------
        if distance_km:  # Cache mode found!
            _logger.info('Cache mode: %s >> %s' % (distance_km, query))
            return distance_km

        # Not in cache:
        if not error:
            try:
                if reply.code == 400:
                    error = 'Error calling URL: %s' % reply.url
            except:
                error = 'Generic error reading MAPS reply message!'
            try:
                if payload.get('code', '').lower() != 'ok':
                    error = 'Error in call'
                else:
                    distance_km = payload.get(
                        'destinations')[1].get('distance')
                self._map_cache[query] = distance_km  # Always save also errors
            except:
                error = 'Error getting KM returned!'

        if error:  # Error present:
            self._excel_log['wb'].write_xls_line(
                self._excel_log['ws_name'], self._excel_log['row'],
                [origin.name, destination.name, error, query])
            self._excel_log['row'] += 1
        return distance_km

    # fields function:
    def _function_calculate_total(
            self, cr, uid, ids, field, name,
            context=None):
        """ Return number of elements per header trip
        """
        res = {}
        for trip in self.browse(cr, uid, ids, context=context):
            res[trip.id] = {}
            res[trip.id] = len(trip.intervent_ids)
        return res

    def _function_calculate_distance(
            self, cr, uid, ids, field, name, context=None):
        """ Return total of distance
        """
        res = {}
        for trip in self.browse(cr, uid, ids, context=context):
            res[trip.id] = {}
            res[trip.id]['total_trip'] = sum(
                [item.total_trip for item in trip.step_ids])
            res[trip.id]['total_trip_company'] = sum(
                [item.total_trip for item in trip.company_step_ids])
        return res

    # onchange function:
    def on_change_create_name(self, cr, uid, user_id, date, context=None):
        """ Create name from date and user_id
        """
        res = {'value': {}}
        # todo completare (anche se non li creeremmo mai da qui
        return

    # Workflow function:
    def intervention_trip_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft', })
        return True

    def intervention_trip_confirmed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed', })
        return True

    def intervention_trip_redraft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'redraft', })
        return True

    _columns = {
        'name': fields.char('Name', size=64),
        'user_id': fields.many2one('res.users', 'Users'),

        'date': fields.date('Date'),
        'refund_day': fields.boolean(
            'Refund day',
            help='If checked the itinerary will be reported in a report'),

        # Trip field from Home:
        'total_trip': fields.function(
            _function_calculate_distance,
            method=True, type='float', string='Tot. distance', multi=True),
        'manual_total': fields.boolean(
            'Manual',
            help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        'manual_total_trip': fields.float('Manual total trip', digits=(16, 6),
            help='Duration in Km of total trip, setted manual, used instead of Total trip'),

        # Trip field from Company:
        'total_trip_company': fields.function(
            _function_calculate_distance,
            method=True, type='float', string='Tot. distance company',
            multi=True),
        'manual_total_company': fields.boolean(
            'Manual company',
            help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        'manual_total_trip_company': fields.float('Manual total trip company',
            digits=(16, 6), help='Duration in Km of total trip, setted manual, used instead of Total trip'),

        'total_intervent': fields.function(_function_calculate_total,
            method=True, type='integer', string='Tot. intervent'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('redraft', 'Re-Draft'),
            ('confirmed', 'Confirmed'),
        ],'State', select=True, readonly=True),
    }

    _defaults = {
         'name': lambda *a: '',
         'state': lambda *a: 'draft',

         # Trip field from Home:
         'total_trip': lambda *x: 0.0,
         'manual_total': lambda *x: False,
         'manual_total_trip': lambda *x: 0.0,

         # Trip field from Company:
         'total_trip_company': lambda *x: 0.0,
         'manual_total_company': lambda *x: False,
         'manual_total_trip_company': lambda *x: 0.0,

         'refund_day': lambda *x: False,
    }


class hr_analytic_timesheet_extra_trip(osv.osv):
    """ Add extra fields to intervent
    """
    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'trip_id': fields.many2one(
            'hr.analytic.timesheet.trip', 'Day trip',
            ondelete='set null', ),  # reset if delete trip
        }


class hr_analytic_timesheet_trip_step(osv.osv):
    """ Step computed for the trip
    """
    _name = 'hr.analytic.timesheet.trip.step'
    _description = 'Trip step'

    _columns = {
        'name': fields.char('Description', size=80),
        'total_trip': fields.float(
            'Distance', digits=(16, 6),
            help='Distance in Km from google maps'),
        'from_id': fields.many2one('res.partner', 'From partner', ),
        'to_id': fields.many2one('res.partner', 'To partner', ),
        'seq': fields.integer('Sequence'),

        'trip_id': fields.many2one('hr.analytic.timesheet.trip', 'Trip'),
        'company_trip_id': fields.many2one(
            'hr.analytic.timesheet.trip',
            'Company Trip'),  # ondelete='cascade',), #
    }

    _defaults = {
         'total_trip': lambda *x: 0.0,
    }


class hr_analytic_timesheet_trip(osv.osv):
    """ Trip for intervent daily for user
    """
    _inherit = 'hr.analytic.timesheet.trip'

    _columns = {
         'intervent_ids': fields.one2many(
             'hr.analytic.timesheet', 'trip_id', 'Intervent'),
         'step_ids': fields.one2many(
             'hr.analytic.timesheet.trip.step', 'trip_id', 'Trip step'),
         'company_step_ids': fields.one2many(
             'hr.analytic.timesheet.trip.step', 'company_trip_id',
             'Company Trip step'),
        }


class res_users_trip(osv.osv):
    """ Extra field for user
    """
    _inherit = 'res.users'

    _columns = {
         'compute_office_trip': fields.boolean(
             'Compute office trip',
             help='Compute office trip, all day will be tranfer in analytic trip for this user'),
         'refund_user': fields.boolean(
             'Refund user', help='Used that have refund day on intervent'),
        }


class ResPartner(osv.osv):
    """ Company parameter
    """
    _inherit = 'res.partner'

    def url_open_map(self, cr, uid, ids, context=None):
        """ Open URL
        """
        partner = self.browse(cr, uid, ids, context=context)[0]

        # Parameter:
        map = 15
        url = 'www.openstreetmap.org'

        url_mask = 'https://{url}/?mlat={lat}&mlon={lon}#map={map}/{lat}/{lon}'
        url_get = url_mask.format(
            url=url,
            lat=partner.map_latitude,
            lon=partner.map_longitude,
            map=map,
        )
        return {
            'name': 'Open MAP',
            'type': 'ir.actions.act_url',
            'url': url_get,
            # 'target': 'self',
            }

    def get_lat_lon(self, cr, uid, ids, context=None):
        """ Partner get lat lon
            context parameter:
            dry_run: Force GET only if not present
        """
        if context is None:
            context = {}
        dry_run = context.get('dry_run')

        partner = self.browse(cr, uid, ids, context=context)[0]

        if dry_run and partner.map_latitude and partner.map_longitude:
            lat = partner.map_latitude
            lon = partner.map_longitude
        else:
            url = 'nominatim.openstreetmap.org'
            address = '{}+{}+{}+{}'.format(
                partner.street,
                partner.zip,
                partner.city,
                partner.state_id.code or '',
                ).replace(' ', '+')

            url_mask = 'https://{url}/search?q={address}&format=json&' \
                       'polygon=1&addressdetails=1'

            query = url_mask.format(url=url, address=address)
            try:
                reply = urllib.urlopen(query)
                _logger.info('Calling: %s' % query)
                response_json = reply.read()
                response = json.loads(response_json)
                if len(response) > 1:
                    _logger.error('More than one address!: %s' % str(response))
                lat = response[0]['lat']
                lon = response[0]['lon']
                display_name = response[0]['display_name']
            except:
                raise osv.except_osv(
                    'Errore recuperando Lat / Lon:',
                    'Errore:\n%s' % str(sys.exc_info()),
                )

            # Save in Partner
            self.write(cr, uid, ids, {
                'map_longitude': lon,
                'map_latitude': lat,
                'map_diplay_name': display_name,
            }, context=context)

        return {'lon': lon, 'lat': lat}

    _columns = {
        'map_partner_name': fields.char('Partner name for map', size=64),
        'map_latitude': fields.char('Map Latitude', size=18),
        'map_longitude': fields.char('Map Longitude', size=18),
        'map_diplay_name': fields.char('Map diplay name', size=180),
        }


class ResCompany(osv.osv):
    """ Company parameter
    """
    _inherit = 'res.company'

    _columns = {
        'map_endpoint': fields.char('Map End point', size=180),
        'map_key': fields.char('Map Customer Key', size=40),
        'map_secret': fields.char('Map Customer Secret', size=40),
        'map_route_unit': fields.selection([
            ('k', 'Km'),
            ('m', 'Miles'),
            ], 'Unit', required=True),
        'map_route_type': fields.selection([
            ('fastest', 'Quickest driving'),
            ('shortest', 'Shortest driving'),
            ('pedestrian', 'Walking'),
            ('bicycle', 'Bicycle'),
            ('multimodal', 'Combination walk and public transit'),
            ], 'Unit', required=True),
        }

    _defaults = {
        'map_route_unit': lambda *x: 'k',
        'map_route_type': lambda *x: 'fastest',
        }
