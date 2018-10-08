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
import sys
import logging
import openerp
import urllib    
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
    ''' Trip for intervent daily for user
    '''
    _name = 'hr.analytic.timesheet.trip'
    _description = 'HR timesheet trip'
    _order = 'date,user_id'
    
    # Button function (and wizard action called):
    def calculate_step_list(self, cr, uid, ids, context=None):
        ''' Delete all steps an compute from intervent list
        '''
        # Utility functions: ###################################################
        def create_record(self, cr, uid, from_id, to_id, trip_id, seq, from_name, to_name, company_trip=False, context=None):
            ''' Create record:
                from_id = id res.partner
                to_id = id res.partner
                trip_id = id of parent record
            '''
            if to_id and from_id and trip_id:
                total_trip = self.distance_between_partner(cr, uid, from_id, to_id, context=context)
                data={
                    'from_id': from_id,
                    'to_id': to_id,
                    'name': "%02d. %s > %s"%(seq, from_name, to_name),
                    'total_trip': total_trip,
                }
                if company_trip:
                    data['company_trip_id']=trip_id
                    data['trip_id']=False
                else:
                    data['company_trip_id']=False
                    data['trip_id']=trip_id

                self.pool.get('hr.analytic.timesheet.trip.step').create(cr, uid, data, context=context)
                return True
            return False    
            
        # ---------------------------------------------------------------------
        # Start procedure
        # ---------------------------------------------------------------------
        company_name = "Company"
        home_name = "Home"
        for trip in self.browse(cr, uid, ids, context=context): 
            # -----------------------------------------------------------------
            # COMMON PART
            # -----------------------------------------------------------------
            # Get parameters from home and company
            home_partner_id = trip.user_id.partner_id.id
            company_partner_id = trip.user_id.company_id.partner_id.id
            # delete all            
            step_ids=self.pool.get('hr.analytic.timesheet.trip.step').search(cr, uid, [
                '|',
                ('trip_id', '=', trip.id),
                ('company_trip_id', '=', trip.id)
            ],context=context)
            if step_ids:
                self.pool.get('hr.analytic.timesheet.trip.step').unlink(cr, uid, step_ids, context=context)

            # -----------------------------------------------------------------
            # FROM HOME TO HOME
            # -----------------------------------------------------------------
            # Generate all the steps
            previous_id = home_partner_id # Always home first start
            previous_name = home_name
            next_destination = False
            seq = 1
            for intervent in trip.intervent_ids:
                if intervent.mode == 'customer' and not intervent.extra_planned: # only for customer
                
                    # FROM part ################################################
                    if intervent.google_from=='home':
                        from_id = home_partner_id
                        from_name = home_name
                        
                    elif intervent.google_from == 'company':
                        if seq==1: # first step home-company
                            if create_record(self, cr, uid, home_partner_id, company_partner_id, trip.id, seq, home_name, company_name, context=context):
                                seq += 1                             
                        from_id = company_partner_id
                        from_name = company_name
                        
                    elif intervent.google_from == 'previous' and previous_id: 
                        from_id = previous_id
                        from_name = previous_name
                    else:
                        continue # jump intervent!!! #pass # TODO Error no previuos_id


                    # Create part A:
                    if create_record(self, cr, uid, from_id, intervent.intervent_partner_id.id, trip.id, seq, from_name, intervent.intervent_partner_id.name, context=context):
                        seq += 1

                    # save parameters:  (next not home or company) 
                    previous_id = intervent.intervent_partner_id.id
                    previous_name = intervent.intervent_partner_id.name

                    # TO part ##################################################                    
                    if intervent.google_to == 'home':
                        create_record(self, cr, uid, intervent.intervent_partner_id.id, home_partner_id, trip.id, seq, intervent.intervent_partner_id.name, home_name, context=context)
                        previous_id = home_partner_id
                        previous_name = home_name
                        seq += 1
                    elif intervent.google_to == 'company':
                        create_record(self, cr, uid, intervent.intervent_partner_id.id, company_partner_id, trip.id, seq, intervent.intervent_partner_id.name, company_name, context=context)
                        previous_id = company_partner_id
                        previous_name = company_name
                        seq += 1
                    
            # Last step (to home)
            if seq == 1: # create home-company-home records
                create_record(
                    self, cr, uid, home_partner_id, company_partner_id, trip.id, 1, home_name, company_name, context=context)
                create_record(
                    self, cr, uid, company_partner_id, home_partner_id, trip.id, 2, company_name, home_name, context=context)
            else:
                if previous_id != home_partner_id: # not home (last destination)
                    create_record(
                        self, cr, uid, previous_id, home_partner_id, trip.id, seq, previous_name, home_name, context=context)            

            ####################################################################
            # FROM COMPANY TO COMPANY ##########################################
            ####################################################################
            # Generate all the steps
            previous_id = company_partner_id # Always company first step
            previous_name = company_name
            next_destination = False
            seq = 1
            update_refund = False
            for intervent in trip.intervent_ids:
                if intervent.mode == 'customer': # only for customer
                    update_refund = True # after create step need to update refund for this trip
                    # FROM part ################################################
                    if intervent.google_from in ('home', 'company'):
                        from_id = company_partner_id
                        from_name = company_name
                        
                    elif intervent.google_from == 'previous' and previous_id: 
                        from_id = previous_id
                        from_name = previous_name
                    else:
                        continue # jump intervent!!! #pass # TODO Error no previuos_id

                    # Create part A:
                    if create_record(self, cr, uid, from_id, intervent.intervent_partner_id.id, trip.id, seq, from_name, intervent.intervent_partner_id.name, True, context=context):
                        seq += 1

                    # save parameters:  (next not home or company) 
                    previous_id = intervent.intervent_partner_id.id
                    previous_name = intervent.intervent_partner_id.name

                    # TO part ##################################################                    
                    if intervent.google_to in ('home', 'company'):
                        create_record(self, cr, uid, intervent.intervent_partner_id.id, company_partner_id, trip.id, seq, intervent.intervent_partner_id.name, company_name, True, context=context)
                        previous_id = company_partner_id
                        previous_name = company_name
                        seq += 1

            if update_refund:                
                self.write(cr, uid, trip.id, {
                    'refund_day': True,
                }, context=context)
                            
        return True
        
    # Utility function:
    def distance_between_partner(self, cr, uid, origin, destination, context=None):
        ''' Master function that calculate distance between origin and detination
            partner id
            NOTE: correct function evalute start and to elements 
        '''
        # private function
        def prepare_element(self, cr, uid, partner_id, context=None):
            ''' Generate a string with all address parameter used for compute 
                distances
            '''
            partner = self.pool.get('res.partner').browse(cr, uid, [partner_id], context=context)[0]
            
            value = "%s %s %s %s"%(partner.street, partner.zip, partner.city, "Italia")
            return value.strip().replace(' ', '+').replace(',', '') # remove comma and transform blank in plus
            
        def distance_query(origin, destination):
            ''' Generate query string for compute km from origin to destination
                element in string ask for return json object
            '''
            try:
                header = u'http://maps.googleapis.com/maps/api/distancematrix/json?'
                google_page = header + "origins=" + prepare_element(self, cr, uid, origin, context=context) + "&destinations=" + prepare_element(self, cr, uid, destination, context=context) + "&sensor=false"
                _logger.warning('Call google page: %s' % google_page)
                return google_page
            except IOError:
                _logger.error('Error generate google page: %s' % google_page)
                return None

        # ---------------------------------------------------------------------        
        # Call Google page:
        # ---------------------------------------------------------------------        
        query = distance_query(origin, destination)
        try:
            response = eval(urllib.urlopen(query).read())
        except:
            raise osv.except_osv(
                _('Google error'), 
                _('Error asking: %s' % query),
                )
                
        # ---------------------------------------------------------------------        
        # Check if not correct call:
        # ---------------------------------------------------------------------        
        if 'error_message' in response:
            raise osv.except_osv(
                _('Google error'),
                _('Call error: %s' % response.get(
                    'error_message', 'Generic error')),
                )
                    
        try:
            distance_km = response['rows'][0]['elements'][0]['distance']['value'] / 1000.0  # km
            return distance_km
        except:    
            return 0.0
    
    # fields function:
    def _function_calculate_total(self, cr, uid, ids, field, name, context=None):
        ''' Return number of elements per header trip
        '''
        res={}
        for trip in self.browse(cr, uid, ids, context=context):
            res[trip.id]={}
            res[trip.id]=len(trip.intervent_ids)
        return res 

    def _function_calculate_distance(self, cr, uid, ids, field, name, context=None):
        ''' Return total of distance
        '''
        res={}
        for trip in self.browse(cr, uid, ids, context=context):
            res[trip.id]={}
            res[trip.id]['total_trip']=sum([item.total_trip for item in trip.step_ids])            
            res[trip.id]['total_trip_company']=sum([item.total_trip for item in trip.company_step_ids])
        return res 
   
    # onchange function:
    def on_change_create_name(self, cr, uid, user_id, date, context=None):
        ''' Create name from date and user_id        
        '''
        res={'value':{}}
        # TODO completare (anche se non li creeremmo mai da qui
        return 
        
    # Workflow function:
    def intervention_trip_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft',}) 
        return True

    def intervention_trip_confirmed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed',}) 
        return True

    def intervention_trip_redraft(self, cr, uid, ids, context=None):     
        self.write(cr, uid, ids, {'state': 'redraft',}) 
        return True
        
    _columns={
        'name':fields.char('Name', size=64, required=False, readonly=False,),
        'user_id':fields.many2one('res.users', 'Users', required=False),
        
        'date': fields.date('Date'), 
        'refund_day':fields.boolean('Refund day', required=False, help="If checked the itinerary will be reported in a report"),

        # Trip field from Home:
        'total_trip': fields.function(_function_calculate_distance, method=True, type='float', string='Tot. distance', store=False, multi=True),
        'manual_total':fields.boolean('Manual', required=False, help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        'manual_total_trip': fields.float('Manual total trip', digits=(16, 6), help="Duration in Km of total trip, setted manual, used instead of Total trip"),

        # Trip field from Company:
        'total_trip_company': fields.function(_function_calculate_distance, method=True, type='float', string='Tot. distance company', store=False, multi=True),
        'manual_total_company':fields.boolean('Manual company', required=False, help="If true don't auto calculate total hour, if false, total hours=intervent + trip - pause hours"),
        'manual_total_trip_company': fields.float('Manual total trip company', digits=(16, 6), help="Duration in Km of total trip, setted manual, used instead of Total trip"),

        'total_intervent': fields.function(_function_calculate_total, method=True, type='integer', string='Tot. intervent', store=False),
        'state':fields.selection([
            ('draft', 'Draft'),              
            ('redraft', 'Re-Draft'),         
            ('confirmed', 'Confirmed'),      
        ],'State', select=True, readonly=True),    
    }
    
    _defaults={
         'name': lambda *a: "",
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
hr_analytic_timesheet_trip()

class hr_analytic_timesheet_extra_trip(osv.osv):
    ''' Add extra fields to intervent 
    '''
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'trip_id':fields.many2one('hr.analytic.timesheet.trip', 'Day trip', required=False, ondelete="set null",), # reset if delete trip
    }
hr_analytic_timesheet_extra_trip()

class hr_analytic_timesheet_trip_step(osv.osv):
    ''' Step computed for the trip
    '''
    _name = 'hr.analytic.timesheet.trip.step'
    _description = 'Trip step'

    _columns = {
        'name':fields.char('Description', size=80, required=False, readonly=False),
        'total_trip': fields.float('Distance', digits=(16, 6), help="Distance in Km from google maps"),
        'from_id':fields.many2one('res.partner', 'From partner', required=False),
        'to_id':fields.many2one('res.partner', 'To partner', required=False),         
        'seq': fields.integer('Sequence'),
        
        'trip_id':fields.many2one('hr.analytic.timesheet.trip', 'Trip', required=False, ), #ondelete="cascade",), # 
        'company_trip_id':fields.many2one('hr.analytic.timesheet.trip', 'Company Trip', required=False, ), #ondelete="cascade",), # 
    }
    _defaults = {
         'total_trip': lambda *x: 0.0,
    }
hr_analytic_timesheet_trip_step()

class hr_analytic_timesheet_trip(osv.osv):
    ''' Trip for intervent daily for user
    '''
    _name = 'hr.analytic.timesheet.trip'
    _inherit = 'hr.analytic.timesheet.trip'

    _columns = {
         'intervent_ids':fields.one2many('hr.analytic.timesheet', 'trip_id', 'Intervent', required=False),
         'step_ids':fields.one2many('hr.analytic.timesheet.trip.step', 'trip_id', 'Trip step', required=False),
         'company_step_ids':fields.one2many('hr.analytic.timesheet.trip.step', 'company_trip_id', 'Company Trip step', required=False),
    }
hr_analytic_timesheet_trip()

class res_users_trip(osv.osv):
    ''' Extra field for user
    '''
    _name = 'res.users'
    _inherit = 'res.users'

    _columns = {
         'compute_office_trip':fields.boolean('Compute office trip', required=False, help="Compute office trip, all day will be tranfer in analytic trip for this user"),
         'refund_user':fields.boolean('Refund user', required=False, help="Used that have refund day on intervent"),         
    }
res_users_trip()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
