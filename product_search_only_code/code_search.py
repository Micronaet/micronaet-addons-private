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
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

'''class ProductProduct(orm.Model):
    """ Model name: Product product
    """
    
    _inherit = 'product.product'
    
    def clean_domain_filter_from_text(self, cr, uid, name, context=None):
        """ Filter domain depend on name start
        """
        print '*********************'
        if name.startswith('+'):
            _logger.warning('Code and name mode (+)')
            name = name[1:]
            return [
                '|',
                ('default_code', 'ilike', name),                    
                ('name', 'ilike', name),
                ]
        elif name.startswith('<'):
            _logger.warning('Start mode (<)')
            name = name[1:]
            return [
                ('default_code', '=ilike', '%s%%' % name),
                ]
        elif name.startswith('>'):
            _logger.warning('End mode (>)')
            name = name[1:]
            return [
                ('default_code', '=ilike', '%%%s' % name),
                ]
        else:
            _logger.warning('Only code mode')
            return [
                ('default_code', 'ilike', name),
                ]
        
    def name_search(self, cr, uid, name, args=None, operator='ilike', 
            context=None, limit=80):
        """ Return a list of tupples contains id, name, as internally its calls 
            {def name_get}
            result format : {[(id, name), (id, name), ...]}
            
            @param cr: cursor to database
            @param uid: id of current user
            @param name: name to be search 
            @param args: other arguments
            @param operator: default operator is ilike, it can be change
            @param context: context arguments, like lang, time zone
            @param limit: returns first n ids of complete result, default it is 80
            
            @return: return a list of tupples contains id, name
        """
        
        if args is None:
            args = []
        if context is None:
            context = {}
        ids = []

        if name:
            domain = self.clean_domain_filter_from_text(
                cr, uid, name, context=context)
            ids = self.search(cr, uid, domain + args, limit=limit)
        return self.name_get(cr, uid, ids, context=context)'''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
