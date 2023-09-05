# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009-2011 company (http://sitename) All Rights Reserved.
#                    General contacts <author.name@company.com>
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

{
    'name': 'Intervention Report',
    'version': '0.2',
    'category': 'Report',
    'description': ''' Module for manage calendar appointment, for fix 
          date of intervention, a little workflow that can set up state of
          intervention, from planning, customer comunication, and report
          for complete intervention
          ''',
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'report_aeroo',
        # 'report_aeroo_ooo',
        'hr',
        'hr_timesheet_invoice',
        'invervention_code_search',  # Extra search for code
        ],
    'init_xml': [],
    'demo_xml': [],
    'data': [
        'security/intervent_group.xml',
        'security/ir.model.access.csv',


        'intervent_sequence.xml',
        'intervention.xml',
        'intervention_workflow.xml',
        'ticket.xml',

        'data/counter.xml',
        ],
    'active': False,
    'installable': True,
    }
