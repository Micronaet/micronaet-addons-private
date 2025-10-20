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
import requests
import json
import pdb
try:
    import ConfigParser
except:
    import configparser as ConfigParser

# ----------------------------------------------------------------------------------------------------------------------
# Read configuration parameter:
# ----------------------------------------------------------------------------------------------------------------------
# From config file:
cfg_file = os.path.expanduser('./config.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
ROOT_URL = config.get('cbsolt', 'url')
API_TOKEN = config.get('cbsolt', 'token')

# 3. Headers standard per la richiesta
HEADERS = {
    "X-API-Token": API_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def get_data_with_token(url, headers, mode='get', verbose=False):
    """ Esegue una richiesta GET a un endpoint API utilizzando un token
        di autenticazione nell'header.
    """
    if verbose:
        print("Tentativo di connessione a: {}".format(url))

    pdb.set_trace()
    try:
        if mode == 'get':
            response = requests.get(url, headers=headers)
        elif mode == 'post':
            response = requests.get(url, headers=headers)
        else:
            print('No mode {}'.format(mode))
            return ''

        response.raise_for_status()
        if verbose:
            print("Richiesta riuscita. Codice di stato:", response.status_code)

        try:
            json_data = response.json()
        except:
            json_data = json.loadd(response.content)
        return json_data

    except requests.exceptions.HTTPError as errh:
        print("Errore HTTP: {}".format(errh))
        print("Contenuto della risposta: {}".format(response.text))
    except requests.exceptions.ConnectionError as errc:
        print("Errore di connessione: {}".format(errc))
    except requests.exceptions.Timeout as errt:
        print("Timeout della richiesta: {}".format(errt))
    except requests.exceptions.RequestException as err:
        print("Si è verificato un errore generico: {}".format(err))
    return None


if __name__ == "__main__":
    # ------------------------------------------------------------------------------------------------------------------
    # Load Domain list:
    # ------------------------------------------------------------------------------------------------------------------
    domain_url = '{}/domains'.format(ROOT_URL)
    domain_reply = get_data_with_token(domain_url, HEADERS, mode='post')

    domain_data = {}

    # Loop to read Domain extra data:
    loop = [
        ('email', 'email_accounts'),
        ('alias', 'alias_email_accounts'),
    ]

    if domain_reply:
        for domain in domain_reply['resources']:

            # ----------------------------------------------------------------------------------------------------------
            # Load domain emails:
            # ----------------------------------------------------------------------------------------------------------
            domain_code = domain['code']
            domain_name = domain['name']
            print('\n\nReading Domain: {}'.format(domain_name))

            domain_data[domain_name] = {
                'detail': domain,
                'email': [],
                'alias': [],
            }
            for key, endpoint in loop:
                email_url = '{}/domains/{}/{}'.format(ROOT_URL, domain_code, endpoint)
                email_payload = HEADERS.copy()
                page = 1

                while True:
                    email_payload['page'] = page
                    reply = get_data_with_token(email_url, HEADERS, mode='get')
                    if reply:
                        for email in reply['resources']:
                            domain_data[domain_name][key].append(email)

                        total_pages = reply['pagination']['total_pages']
                        page += 1
                        if page > total_pages:
                            print('Max page raised {}'.format(total_pages))
                            break
                        else:
                            print('Read next page {} of {}'.format(page, total_pages))
                    else:
                        print('No mail for domain {}'.format(domain_code))
                        break

                # ------------------------------------------------------------------------------------------------------
                # Show extract date:
                # ------------------------------------------------------------------------------------------------------
                print('\n > Data: {}'.format(key))
                for email in domain_data[domain_name][key]:
                    if key == 'email':
                        print('{} created: {} Dim.: {} Stato: {}'.format(
                            email['email_address'],
                            email['created_at'],
                            email['max_email_quota'] / (1024 ** 3),
                            'ATTIVA' if email['status'] == 'enabled' else 'DISATTIVATA',
                            # lastauth_datetime
                        ))
                    elif key == 'alias':
                        # {'created_at': '2025-09-03T11:32:26.000+02:00', 'updated_at': '2025-09-03T11:32:30.000+02:00',
                        # 'domain_name': 'bassanidotti.com', 'destinations': ['paolo@bassanidotti.com'],
                        # 'status': 'enabled', 'status_detail': 'ok', 'code': 'AE51749109', 'name': 'info'}
                        print('{}@{} created: {} Redirect: [{}] Stato: {}'.format(
                            email['name'],
                            domain_name,
                            email['created_at'],
                            ', '.join(email['destinations']),
                            'ATTIVA' if email['status'] == 'enabled' else 'DISATTIVATA',

                            # lastauth_datetime
                        ))

        # print(json.dumps(domain_reply, indent=4))
    else:
        print("\nImpossibile recuperare i dati dall'API.")