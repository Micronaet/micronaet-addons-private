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


from osv import fields,osv
import netsvc

class intervent_report_collection_wizard(osv.osv_memory):
    """ Wizard that permit to:
        select type of report
        Filter element by some value (user, customer etc.)

        The wizard return aeroo report selected
    """

    _name = "intervent.report.collection.wizard"

    # On change function:
    def on_change_month(self, cr, uid, ids, month, context=None):
        """
        """
        import time

        res={'value':{}}
        if month:
            res['value']={'from_date':"%s-%02d-01 00:00:00"%(time.strftime('%Y'), int(month)),
                          'to_date': "%04d-%02d-01 00:00:00"%(int(time.strftime('%Y')) if month != "12" else int(time.strftime('%Y')) + 1, int(month) + 1 if month!="12" else 1,)}

        return res

    # Button function of the wizard:
    #    Extra function usefull:
    def _get_action_report_to_return(self, cr, uid, ids, intervent_ids, report_name, title, context=None):
        """ Compose action to return according to passed: intervent_ids, report_name, title
        """
        datas = {'ids': intervent_ids,}
        datas['model'] = 'intervention.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['title']= title

        # return action:
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name, # TODO one for all??
            'datas': datas,
        }

    def _get_filter_from_wizard(self, cr, uid, ids, with_partner=True, context=None):
        """ In wizard passed get the filter selected in normal domain format
            the with_partner parameter is used for parametrize this function
            for filter report or for load all partner of the filtered values
            (in this case, obviously there's no selection...)
        """
        if context is None:
            context = {}

        wiz_proxy = self.browse(cr, uid, ids)[0]
        domain=[]

        if wiz_proxy.partner_id and with_partner:
           domain += [('partner_id','=',wiz_proxy.partner_id.id)]

        if wiz_proxy.user_id:
           domain += [('user_id','=',wiz_proxy.user_id.id)]

        if wiz_proxy.from_date:
           domain += [('date_start','>=',"%s %s"%(wiz_proxy.from_date, "00:00:00"))]

        if wiz_proxy.to_date:
           domain += [('date_start','<',"%s %s"%(wiz_proxy.to_date, "00:00:00"))]

        if wiz_proxy.is_intervent: # only intervent
           domain += [('state','in', ('confirmed','closed','reported'))]

        if wiz_proxy.is_closed: # only intervent
           domain += [('state','in', ('closed','reported'))]

        return domain

    def _get_report_parameter_for_action(self, group_by):
        """ Return report parameter: (report_name, title, order)
            according to group_by clause passed
        """

        if group_by == 'state': # group state
            return ("intervent_report_state", "Intervent report list (group by state)", "partner_id,ref,date_start",)

        elif group_by == 'tipology': # group tipology
            return ("intervent_report_tipology", "Intervent report list (group by tipology)", "tipology_id,date_start",)

        elif group_by == 'partner': # group tipology
            return ("intervent_report_partner", "Intervent grouped by tipology" ,"partner_id,date")

        elif group_by == 'list': # group tipology
            return ("intervent_report", "Intervent report list (group by state)", "partner_id,date_start")

        else: # no report (case impossible)
            return (False,False,False) # comunicate error

    def print_load_partner(self, cr, uid, ids, context=None):
        """ Test filter selected and get partner list for intervent
        """
        domain=self._get_filter_from_wizard(cr, uid, ids, with_partner=False, context=context)
        intervent_ids = self.pool.get('intervention.report').search(cr, uid, domain, context=context)
        intervent_proxy = self.pool.get('intervention.report').browse(cr, uid, intervent_ids, context=context)

        partner_ids=[]
        for intervent in intervent_proxy:
            if intervent.partner_id and intervent.partner_id.id not in partner_ids:
               partner_ids.append(intervent.partner_id.id)

        if intervent_ids:
           # write new list of elements
           self.write(cr, uid, ids, {'partner_ids': [(6, 0, partner_ids)]})
        return True

    def print_save_partner_report(self, cr, uid, ids, context=None):
        """ Save partner report (state and intervent) for that period
            Call each partner (pre loaded) and save for each of it 2 report
            status report and intervent report
        """
        import time, base64, xmlrpclib

        user_proxy=self.pool.get('res.users').browse(
            cr, uid, [uid], context=context)[0]
        db = cr.dbname
        uid = uid
        pwd = user_proxy.password
        model = 'intervention.report'

        # report_name="intervent_report"
        report_to_print={}
        report_to_print['state'] = self._get_report_parameter_for_action('state')
        report_to_print['list'] = self._get_report_parameter_for_action('list')

        wiz_proxy=self.browse(cr, uid, ids)[0]

        printsock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/report')

        #domain = self._get_filter_from_wizard(cr, uid, ids, with_partner=False, context=context)
        for partner in wiz_proxy.partner_ids: #self.pool.get('intervention.report').search(cr, uid, domain, order=order, context=context)
            # get intervent_ids for this partner
            domain = self._get_filter_from_wizard(cr, uid, ids, with_partner=False, context=context)
            domain += [('partner_id', '=', partner.id)]
            for key in report_to_print.keys():
                (report_name, title, order) = report_to_print[key]
                intervent_ids = self.pool.get(model).search(cr, uid, domain, order=order, context=context)
                #self._get_action_report_to_return(cr, uid, ids, intervent_ids, report_name, title, context=context)
                if intervent_ids:
                    action = self._get_action_report_to_return(
                        cr, uid, ids, intervent_ids, report_name, title,
                        context=context)
                    action['report_type'] = 'pdf'
                    action['model'] = model
                    id_report = printsock.report(
                        db, uid, pwd, report_name, intervent_ids, action)
                    # ids   {'model': model, 'report_type':'pdf'})
                    time.sleep(5)
                    state = False
                    attempt = 0
                    while not state:
                        report = printsock.report_get(db, uid, pwd, id_report)
                        state = report['state']
                        if not state:
                            time.sleep(1)
                            attempt += 1
                        if attempt > 200:
                            print('Printing aborted, too long delay !')

                        string_pdf = base64.decodestring(report['result'])
                        file_name = \
                            '/home/administrator/pdf/%s %s - %s.pdf' % (
                                wiz_proxy.month, partner.name,
                                "Riepilogo" if key == "state" else
                                "Rapportini")
                        file_pdf = open(file_name,'w')
                        file_pdf.write(string_pdf)
                        file_pdf.close()
        return False

    def print_intervent_report(self, cr, uid, ids, context=None):
        """ With filter parameter select all intervent searched
            Create data element to call after the aeroo report
        """

        if context is None:
            context = {}

        wiz_proxy = self.browse(cr, uid, ids)[0]
        order="date_start" # TODO depend on report (put in parser??)
        title="RIEPILOGO ORE DIVISO PER STATO INTERVENTO:"

        # Domain filter: *******************************************************
        # get the filter
        domain = self._get_filter_from_wizard(cr, uid, ids, with_partner=True, context=context)

        # get the parameter:
        (report_name, title, order) = self._get_report_parameter_for_action(wiz_proxy.report_type)

        # get the intervent list according to filter and parameter:
        intervent_ids = self.pool.get('intervention.report').search(cr, uid, domain, order=order, context=context)

        # create datas element and return report action:
        if intervent_ids:
            return self._get_action_report_to_return(cr, uid, ids, intervent_ids, report_name, title, context=context)
        return False   # error no intervent!

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=False),
        'partner_id': fields.many2one('res.partner', 'Partner', required=False),
        'partner_ids':fields.many2many('res.partner', 'intervent_partner_rel', 'intervent_id', 'partner_id', 'Partner', help="List of partner for the period selected"),
        'month': fields.selection([
            ('01','January'),
            ('02','February'),
            ('03','March'),
            ('04','April'),
            ('05','May'),
            ('06','June'),
            ('07','July'),
            ('08','August'),
            ('09','September'),
            ('10','October'),
            ('11','November'),
            ('12','December'),
        ],'Month', select=True, readonly=False),
        'from_date': fields.date('From date (>=)',),
        'to_date': fields.date('To date (<)',),
        'is_intervent': fields.boolean("Is intervent"),
        'is_closed': fields.boolean("Is closed"),
        'report_type': fields.selection([('state', 'Report by state'),
                                         ('tipology', 'Report by tipology'),
                                         ('partner', 'Report by customer'),
                                         ('list','List of intervent')], 'Report type (group by)', readonly=False, required=True,),
    }
    _defaults = {
        'is_intervent': lambda *x: False,
        'is_closed': lambda *x: False,

    }
intervent_report_collection_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
