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
import logging
import requests
import json
import pdb
from osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP)
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class ResPartnerInherit(orm.Model):
    """ *2many in Partner
    """
    _inherit = 'res.partner'

    def open_crm_helpdesk_list(self, cr, uid, ids, context=None):
        """ Helpdesk button open domain list
        """
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'

        # ir_model_data = self.pool.get('ir.model.data')
        # template_id = ir_model_data.get_object_reference(
        # cr, uid, 'intervention_report', 'email_template_timesheet_intervent')[1]

        partner_id = ids[0]
        if context is None:
            context = {}

        form_view_id = tree_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'crm.helpdesk',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('partner_id', '=', partner_id)],
            # 'target': '',
            'context': context,
        }

    def open_crm_claims_list(self, cr, uid, ids, context=None):
        """ Partner CRM Claims open domain list
        """
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'

        # ir_model_data = self.pool.get('ir.model.data')
        # template_id = ir_model_data.get_object_reference(
        # cr, uid, 'intervention_report', 'email_template_timesheet_intervent')[1]

        partner_id = ids[0]
        if context is None:
            context = {}

        form_view_id = tree_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'crm.claim',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('partner_id', '=', partner_id)],
            # 'target': '',
            'context': context,
        }
