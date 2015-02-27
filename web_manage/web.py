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

from osv import osv, fields

class res_partner_web_type(osv.osv):
    '''Type of cms used for generate website
    '''
    _name = 'res.partner.web.type'
    _description = 'Type of website'    
    
    _columns={
        'name':fields.char('Tipo', size=50, required=True),
        'note':fields.text('Note'),            
            }
 
class res_partner_web(osv.osv):
    '''
    '''
    _name = 'res.partner.web'
    _description = 'Website'
    _order = 'name'

    _columns={
        'name':fields.char('URL', size=80, required=True),
        'deadline':fields.date('Scadenza dominio'),
        'pay_date':fields.date('Data di pagamento'),
        'note':fields.text('Note'),
        'active':fields.boolean('Attivo'),
        'whois':fields.text('Record whois'),
        'partner_id':fields.many2one('res.partner', 'Partner', required=True),
        'hosting_id':fields.many2one('res.partner', 'Provider', required=True),
        'type_id':fields.many2one('res.partner.web.type', 'Type'),
        'on_line':fields.boolean('On-line'),
        'status':fields.char('Stato', size=80, readonly=True),
        'create_domain':fields.datetime('Data creazione', readonly=True),
        'last_update':fields.datetime('Ultimo aggiornamento', readonly=True),
        'expire_date':fields.datetime('Data termine', readonly=True),
        'contact_name':fields.char('Nome amministratore', size=40, readonly=True),
        'technical_contact':fields.char('Nome tecnico', size=40, readonly=True),
        'organization':fields.char("Nome organizzazione", size=40, readonly=True),
        'alias':fields.boolean('Alias'),
        'webmail':fields.char('Webmail', size=100),
        'webmail_admin':fields.char('Webmail admin', size=100),
        'hosted':fields.boolean('Domiciliato'),
            }
            
    _defaults={
        'hosted': lambda *a:True,     
             }

    def button_whois(self, cr, uid, ids, context=None):
        '''
        '''
        import subprocess

        for web_proxy in self.browse(cr, uid, ids):
            web_proxy.name

            data = {'whois':''}
            proc = subprocess.Popen(['whois', web_proxy.name], shell=False, stdout=subprocess.PIPE)

            empty_line=0

            for line in proc.stdout:
                data['whois'] += line
                if not line.strip():
                    empty_line+=1
                    continue
                if empty_line==2:     # Primo paragrafo senza nome:
                    if line[0:6].lower()=='status':
                        data['status'] = line.split(':')[1].strip()

                    if line[0:7].lower()=='created':
                        data['create_domain'] = line.split(': ')[1].strip()

                    if line[0:11].lower()=='last update':
                        data['last_update'] = line.split(': ')[1].strip()    

                    if line[0:11].lower()=='expire date':
                        data['expire_date'] = line.split(': ')[1].strip()

                elif empty_line==4:    # Admin Contact
                    if line.strip()[0:4].lower()=='name':
                        data['contact_name'] = line.split(':')[1].strip() 

                elif empty_line==5:    # Technical Contacts
                    #import pdb; pdb.set_trace()
                    if line.strip()[0:12].lower()=='organization':
                        data['technical_contact'] = line.split(':')[1].strip()

                elif empty_line==6:    # Registrar
                    if line.strip()[0:12].lower()=='organization':
                        data['organization'] = line.split(':')[1].strip()

            proc.wait()

            self.write(cr, uid, web_proxy.id, data, context=context)

    def scheduler_whois (self, cr, uid, context=None):
        '''
        '''
        domain_ids = self.search(cr, uid, [], context=context)
        self.button_whois (cr, uid, domain_ids, context=context)

        return True

class res_partner_web_password(osv.osv):
    '''Password linked to website
    '''
    _name = 'res.partner.web.password'
    _description = 'Password'

    _columns={
        'name':fields.char('Username', size=30, required=True),
        'password':fields.char('Password', size=30, required=True),
        'address':fields.char('Indirizzo', size=80, required=True),
        'note':fields.text('Note'),
        'extra_info':fields.text('Extra info'),
        'type_id':fields.many2one('res.partner.web.password.type', 'Password type'),
        'web_id':fields.many2one('res.partner.web', 'Web'),
            }
                   
class res_partner_web_mail(osv.osv):
    '''Gestione mail
    '''

    _name='res.partner.web.mail'
    _description=''
    
    _columns={
        'name':fields.char('Indirizzo mail', size=40, required=True),
        'password':fields.char('Password', size=40, required=True),
        'account':fields.char('Account', size=40, required=True),
        'note':fields.text('Note'),
        'web_id':fields.many2one('res.partner.web', 'Web'),
        'postmaster':fields.boolean('Postmaster'),
             }

    _defaults={
        'postmaster':lambda *a :False,
            }             

class res_partner_web_mail_server(osv.osv):
    '''Gestion server mail
    '''
    
    _name='res.partner.web.mail.server'
    _description=''
    
    _columns={
        'name':fields.char('Name', size=50, required=True),
        'protocollo':fields.selection([
                                    ('pop3', 'POP3'), 
                                    ('smtp', 'SMTP'),
                                    ('imap','IMAP'),
                                    ('pop3s', 'POP3s'), 
                                    ('smtps', 'SMTPs'),
                                    ('imaps','IMAPs'),
                                   ], 'Protocollo', select=True),
        'port':fields.char('Port', size=5),
        'ssl':fields.boolean('SSL'),
        'authentication':fields.boolean('Authentication'),
        'web_id':fields.many2one('res.partner.web', 'Web'),
             }

class res_partner_web(osv.osv):
    '''
    '''
    _name = "res.partner.web"
    _inherit = "res.partner.web"
    
    _columns={
        'password_ids':fields.one2many('res.partner.web.password', 'web_id', 'Password'),
        'mail_ids':fields.one2many('res.partner.web.mail', 'web_id', 'Mail'),
        'mail_server_ids':fields.one2many('res.partner.web.mail.server', 'web_id', 'Server mail'),
             }
    
class res_partner(osv.osv):
    '''Extra relation fields
    '''
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns={
        'web_ids':fields.one2many('res.partner.web', 'partner_id', 'Webs'),
        'provider_web_ids':fields.one2many('res.partner.web', 'hosting_id', 'Web farmed'),
        'is_provider':fields.boolean('Is provider')
            }
                 
    _defaults={
        'is_provider': lambda *a: False,
              }       
class res_partner_web_password_type(osv.osv):
    '''
    '''
    _name = 'res.partner.web.password.type'

    _columns={
        'name':fields.char('Nome', size=64, required=True),
        'note':fields.text('Note', size=64),
            }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
