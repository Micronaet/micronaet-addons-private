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

class AccountAnalyticAccount(orm.Model):
    """ Model name: Analytic account 
    """
    
    _inherit = 'account.analytic.account'
    
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
            ids = self.search(cr, uid, [
                ('code', 'ilike', name),
                ] + args, limit=limit)
        if not ids:
            ids = self.search(cr, uid, [
                ('name', operator, name),
                ] + args, limit=limit)
        return self.name_get(cr, uid, ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        """ Return a list of tupples contains id, name.
            result format : {[(id, name), (id, name), ...]}
            
            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of ids for which name should be read
            @param context: context arguments, like lang, time zone
            
            @return: returns a list of tupples contains id, name
        """
        
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            if context.get('with_code', False):
                res.append((record.id, '[%s] %s' % (record.code, record.name)))
            else:
                res.append((record.id, record.name))
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
