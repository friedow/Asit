
import random
import time
import requests

import logging
import logging.config

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger('core')

def forge_basic_url(language, world):
    if language == 'de':
        return 'http://welt' + self.world + '.freewar.de/freewar/internal/'
    elif language == 'en':
        return 'http://world' + self.world + '.freewar.com/freewar/internal/'

def forge_header(language, world):
    if language == 'de':
        return {'Host': 'welt' + self.world + '.freewar.de', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}
    elif language == 'en':
        return {'Host': 'world' + self.world + '.freewar.com', 'Connection': 'keep-alive', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}

class Account:

    # C'tor
    def __init__(self, language, world, user, password, ability):
        # def standard account variables
        self.cookie = ''
        self.language = language
        self.world = world
        self.user = user
        self.password = password
        self.ability = ability
        # preparing header and basic url for get and post requests
        self.basic_url = forge_basic_url(self.language, self.world)
        self.header = forge_header(self.language, self.world)

    def login(self):
        logger.info('Logging in')
        login_url = self.basic_url + 'index.php'
        # really annoying
        if self.language == 'de':
            login_submit = 'Einloggen'
        elif self.language == 'en':
            login_submit = 'Login'
        # login payload / post parameters
        login_payload = {'name': self.user, 'password': self.password, 'submit': login_submit}
        # login request
        login_request = requests.post(login_url, data = login_payload, headers = self.header)
        # nesseccary for session management in other requests
        self.cookie = login_request.cookies
        logger.info('Login successful')
        return 0

    # nesseccary to access all other links in fw main window after login
    def redirect(self):
        logger.info('Redirecting')
        redirect_url = self.basic_url + 'frset.php'
        requests.get(redirect_url, headers = self.header, cookies = self.cookie)
        logger.info('Redirect successful')
        return 0

    # function to train characters abilities
    def train(self):
        # the training sequence
        logger.info('Training')
        train_url = self.basic_url + 'ability.php'
        train_payload = {'action': 'train', 'ability_id': self.ability}
        requests.get(train_url, params = train_payload, headers = self.header, cookies = self.cookie)
        logger.info('Training successful')

        # preparing for the training status request
        status_payload = {'action': 'show_ability', 'ability_id': self.ability}
        # requesting content of main frame
        status_request = requests.get(train_url, params = status_payload, headers = self.header, cookies = self.cookie)

        if self.language == 'de':
            search_parameters = ['Aktuelle Stufe: ', 'Maximale Stufe: ']
        # TODO: online den genauen text nachschlagen
        elif self.language == 'en':
            search_parameters = ['actual level: ', 'maximal level: ']

        output = '\tActual level: '
        first = True

        # looking for search parameters in http response
        for search_text in search_parameters:
            # exception handling
            try:
                position = status_request.text.find(search_text)
                if (position == -1):
                    raise RuntimeError('Bad Request')
            except RuntimeError:
                logger.info('Could not found ability level.')
                return 1
            # TODO: Hier gehts weiter
            text_length = len(search_text)
            ability_level = status_request.text[position + text_length : position + text_length + 3]
            # geting a clean output
            ability_level = ability_level.strip('<')
            ability_level = ability_level.strip('/')
            ability_level = ability_level.strip('b')
            output += ability_level
            if first:
                first = False
                output += ' / '

        logger.info(output)
        return 0

    # function to pick up accounts oil if he's on the right field for that
    def oil(self):
        logger.info('Picking up oil')
        # requesting content of main frame
        main_url = self.basic_url + 'main.php'
        main_request = requests.get(main_url, headers = self.header, cookies = self.cookie)

        # something called exception handling
        try:
            position = main_request.text.find('checkid=')
            if (position == -1):
                raise RuntimeError('wrong position')
        except RuntimeError:
            logger.info("Oil isn't ready yet or account is on the wrong position.")
            return 1

        # pincking up the oil
        oil_url = self.basic_url + 'main.php'
        oil_payload = {'arrive_eval': 'drink', 'checkid': main_request.text[position + 8 : position + 15]}
        requests.get(oil_url, params = oil_payload, headers = self.header, cookies = self.cookie)
        return 0

    # for a clean session
    def logout(self):
        logger.info('Logging out')
        logout_url = self.basic_url + 'logout.php'
        requests.get(logout_url, headers = self.header, cookies = self.cookie)
        logger.info('Logged out')
        return 0

    def automatic_sit(self):
        try:
            self.login()
            self.redirect()
            self.train()
            self.oil()
            self.logout()
        except:
            logger.critical('Connection Error.')
            return 1


class ManageAccounts:

    def __init__(self, account_path):
        self.accounts = []
        self.later = []
        # filling the list of credentials
        with open(account_path, 'r') as account_file:
            for line in account_file:
                splitted_line = line.strip('\n').split(', ')
                #print(splitted_line)
                if len(splitted_line) == 5:
                    self.accounts.append(splitted_line)

    def manage(self):
        while len(self.accounts) > 0:
            for language, world, user, password, ability in self.accounts:
                # skipping credentials of the same world
                skip = False
                for account in self.accounts:
                    if (account[1] == world) and (account[2] != user):
                        self.later.append(account)
                        self.accounts.remove(account)
                        skip = True
                if skip:
                    continue

                # if not skipped, handling the credential
                logger.info('World: ' + world + '     Account: ' + user + '     Server: ' + language)
                FWAccount = Account(language, world, user, password, ability)
                if FWAccount.automatic_sit():
                    return 1

            # writing memorized credentials back to be handled
            if len(self.later) > 0:
                random_time = random.randint(180, 300)
                logger.info('Wating ' + str(random_time) + ' Seconds to log other accounts savely.')
                time.sleep(random_time)
                self.accounts = self.later
                self.later.clear()
            else:
                self.accounts.clear()
