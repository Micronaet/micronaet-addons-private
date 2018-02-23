##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from report import report_sxw
from report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_objects': self.get_objects,
            'get_filter': self.get_filter,
            })
    
    def get_filter(self, data=None):
        ''' Get filter from data dict
        '''
        
        return ''
                
    def get_objects(self, data=None):
        ''' Load data filtered from dict
        '''
        ''' Load all data for analytic report
            Search all intervent in period
        '''
        # Readability:
        cr = self.cr
        uid = self.uid
        context = {}
        
        # Pool used:
        int_pool = self.pool.get('hr.analytic.timesheet')

        # ---------------------------------------------------------------------
        # Search depend on filter domain:
        # ---------------------------------------------------------------------
        detailed = data.get('detailed', True)
        domain = []
        if data['from_date']:
            domain.append(
                ('date_start', '>=', '%s 00:00:00' % data['from_date']))
        if data['to_date']:
            domain.append(
                ('date_start', '<', '%s 00:00:00' % data['to_date']))
                
        # TODO add filter for stat
        # TODO add filter for extra documents
        # TODO add filter for remove micronaet        

        if data.get('user_id', False):
            domain.append(('user_id', '=', data['user_id']))
        if data.get('partner_id', False):
            domain.append(('intervent_partner_id', '=', data['partner_id']))
        int_ids = int_pool.search(cr, uid, domain, context=context)
        
        # ---------------------------------------------------------------------
        # Sorted with key:
        # ---------------------------------------------------------------------
        items = sorted(
            # List of intervent in list:
            [item for item in int_pool.browse(
                cr, uid, int_ids, context=context)], 
                
            # Key order:    
            key = lambda item: (
                item.intervent_partner_id.name, # Partner
                'Contratti' if item.account_id.partner_id else 'Generico',
                item.account_id.name, # Analytic account
                item.user_id.name, # Users
                item.date_start, # Date
                ))
        
        # ---------------------------------------------------------------------
        # Prepare data list:    
        # ---------------------------------------------------------------------
        # Init operations:
        res = []
        
        totals = [
            # Total evaulated:
            0.0, # customer
            0.0, # type
            0.0, # account
            0.0, # user
            
            False, # previous record
            0, # # of intervent
            
            # Total invoiced:
            0.0, # customer
            0.0, # type
            0.0, # account
            0.0, # user            
            ]
            
        olds = [
            False, # customer
            False, # type
            False, # account
            False, # user
            ]
            
        # Master loop:
        i = 0
        for item in items:
            i += 1

            # Readability:
            partner_id = item.intervent_partner_id.id
            type_data = 'Contratti' if \
                item.account_id.partner_id else 'Generico'   
            account_id = item.account_id.id
            user_id = item.user_id.id
            
            # -----------------------------------------------------------------      
            # Break level check:
            # -----------------------------------------------------------------      
            level = 'nothing'

            # -------------------------------
            # break partner (or first record)
            # -------------------------------
            if olds[0] != partner_id or i == 1:           
                level = 'partner' # set break level partner
                
                # Total block:
                if i != 1: # no for first line:
                    res.append(('total', level, tuple(totals)))
                
                # save all current level starting from partner:
                olds[0] = partner_id
                olds[1] = type_data
                olds[2] = account_id
                olds[3] = user_id
                
                # reset all totals
                totals[0] = 0.0
                totals[1] = 0.0
                totals[2] = 0.0
                #totals[3] = 0.0

                totals[6] = 0.0
                totals[7] = 0.0
                totals[8] = 0.0
                #totals[9] = 0.0
            
            # -----------
            # break type: 
            # -----------
            else:
                if olds[1] != type_data:
                    level = 'type' # set break level type

                    # Total block:
                    res.append(('total', level, tuple(totals)))
                    
                    # save all current level starting from partner:
                    olds[1] = type_data
                    olds[2] = account_id
                    olds[3] = user_id
                    
                    # reset all totals
                    totals[1] = 0.0
                    totals[2] = 0.0
                    #totals[3] = 0.0

                    totals[7] = 0.0
                    totals[8] = 0.0
                    #totals[9] = 0.0
                else:    

                    # --------------
                    # break account:
                    # --------------
                    if olds[2] != account_id:
                        level = 'account' # set break level type

                        # Total block:
                        res.append(('total', level, tuple(totals)))
                        
                        # save all current level starting from partner:
                        olds[2] = account_id
                        olds[3] = user_id
                        
                        # reset all totals
                        totals[2] = 0.0
                        #totals[3] = 0.0
                    
                        totals[8] = 0.0
                        #totals[9] = 0.0

                    # -----------
                    # break user:
                    # -----------
                    # Do nothing (no totals)
                
            # -----------------------------------------------------------------
            # update with current totals:
            # -----------------------------------------------------------------
            # Readability:
            intervent_total = item.intervent_total
            intervent_invoiced = \
                intervent_total * item.to_invoice.factor / 100.0

            totals[0] += intervent_total
            totals[1] += intervent_total
            totals[2] += intervent_total
            #totals[3] += intervent_total XXX not used for not
            totals[4] = item # previous record
            #totals[5] += item.intervent_total XXX counter not used

            totals[6] += intervent_invoiced
            totals[7] += intervent_invoiced
            totals[8] += intervent_invoiced
            #totals[9] += intervent_invoiced

            # write data line:
            if detailed:
                res.append(('data', level, item))
        
        # write last total:
        if i:
            res.append(('total', level, tuple(totals))) # TODO
        return res
