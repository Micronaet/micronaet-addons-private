# -*- coding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

{
    'name': 'Intervention analysis',
    'version': '0.1',
    'category': 'Report',
    'description': """
        Add extra element for analysis in intervention report        
        """,
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'intervention_report',
        'intervention_report_invoice',
        'report_webkit',
        'report_aeroo',
        'excel_export', # Extract XLSX file
        ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [
        #'security/ir.model.access.csv',
        'analysis_view.xml',  
        'report/status_webkit.xml',
        'report/status_intervent.xml',
        'wizard/intervention_status_wizard.xml',                    
        'wizard/import_excel_file_view.xml',
        'wizard/extract_personal_stats_view.xml',
        ],
    'active': False,
    'installable': True,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
