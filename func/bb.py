import diskcache, requests, json, signal, socketio, threading, time, os, re
from prettytable import PrettyTable
from colorama import Fore, Back, Style

def validate_ip(ip):
    default_ip = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(default_ip, ip) is not None


def validate_url(url):
    default_url = r'^([a-zA-Z0-9]+(-[a-zA-Z0-9]+)*\.)+[a-zA-Z]{2,}$'
    return re.match(default_url, url) is not None


class Blockbit:
    def __init__(self):
        self.cache = diskcache.Cache('~/.cache/nav/save.temp')
        self.headers = {'Content-Type': 'application/json'}
        self.api_url = 'http://172.16.151.141:4001'
        self.BBID = 0
        self.BBNAME = ''
        self.ACTIVE = True
        self.LOOP = True
        self.token = self.cache.get('token')
        self.sio = socketio.Client()
        self.TIMECHECK = False

        USER = self.cache.get('username').title().split('.')
        self.USERNAME = f'{USER[0]} {USER[1]}'.upper()

    def interrupt(self, signal, frame):
        self.ACTIVE = False
        print('\r')
        raise Exception("Stop")

    def connect(self, val):
        cm = val.split()

        if len(cm) < 2:
            print('bbc [ID] or blockbit-connect [ID]')
            return

        data = {'id': cm[1], 'token': self.token}
        response = requests.post(f'{self.api_url}/bb/connect', data=json.dumps(data), headers=self.headers)
        if response.status_code == 200:
            result = response.json()
            self.BBID = cm[1]
            self.cache['EquipamentID'] = self.BBID
            self.BBNAME = result['identify']

        else:
            print('ID inválido.')
            return

        self.ACTIVE = True

        while self.ACTIVE:
            signal.signal(signal.SIGINT, self.interrupt)
            try:
                comando = input(Fore.RED + Style.NORMAL + f"{self.USERNAME} [{self.BBNAME}]# " + Fore.WHITE)

                result = self.command(comando)

                if result == 1:
                    break

                elif result == 2:
                    continue

                print(comando + ': command not found.')
            except Exception as e:
                print('C^')
                break

        return 2

    def search(self, val):
        cm = val.split()

        if len(cm) < 2:
            print('bbs [Pesquisa] or blockbit-search [Pesquisa]')
            return 2

        data = {'search': cm[1], 'token': self.token}
        response = requests.post(f'{self.api_url}/bb/search', data=json.dumps(data), headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            tabela = PrettyTable()
            tabela.field_names = ["ID", "Identify", "IP", "Modelo"]

            count = 0
            id_zero = ''

            for item in result:
                if count == 0:
                    id_zero = item['id']

                tabela.add_row([item['id'], item['identify'], item['ip'], item['modelo']])
                count += 1

            if count == 0:
                print(Style.BRIGHT + Back.RED + Fore.BLACK + 'Nada encontrado.' + Style.RESET_ALL, Back.RESET,
                      Fore.RESET)
                return 2

            print(tabela)
            try:
                id = input("Digite o ID: ")
            except:
                print('C^')
                return 2

            if id == '':
                self.connect(f'bbc {id_zero}')
            elif id.isdigit():
                self.connect(f'bbc {id}')

        return 2

    def command(self, val) -> int:
        if val == 'exit':
            return 1
        elif val == 'help':
            print(Fore.CYAN + '• Lista de comandos.')
            print(Fore.WHITE + '\t• debug-firewall.')
            print(Fore.WHITE + '\t• debug-dhcp.')
            print(Fore.WHITE + '\t• debug-ppp.')
            print(Fore.WHITE + '\t• debug-vpn.')
            print(Fore.WHITE + '\t• debug-sdwan.')
            print(Fore.WHITE + '\t• ping.')
            print(Fore.WHITE + '\t• tcpdump.')
            print(Fore.WHITE + '\t• traceroute.')
            print(Fore.WHITE + '\t• mtr.')
            print(Fore.WHITE + '\t• ip.')
            print(Fore.WHITE + '\t• ifconfig.')
            print(Fore.WHITE + '\t• uptime.')
            return 2
        elif val.startswith('ping'):
            return self.ping(val)
        elif val.startswith('debug-'):
            value = val.replace('debug-', '')
            return self.debug(value)
        elif val.startswith('mtr'):
            return self.mtr(val)
        elif val.startswith('traceroute'):
            return self.traceroute(val)
        elif val == 'uptime':
            return self.command_request('uptime', '', '')
        elif val == 'ifconfig':
            return self.command_request('ifconfig', '', '')
        elif val == 'ip monitor':
            return self.ip_monitor()
        elif val == 'tcpdump':
            return self.tcpdump()
        elif val.startswith('ip'):
            return self.ip(val)

    def ip_monitor(self):
        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.event
        def monitor(data):
            print(data)

        @self.sio.event
        def monitor_exit(data):
            print(data)
            self.LOOP = False

        def wait_for_events():
            data = {
                'id': self.BBID,
                'token': self.cache.get('token')
            }
            self.sio.emit(f'monitor', data)
            self.sio.wait()

        def handle_interrupt(signal, frame):
            self.LOOP = False
            print('\r')

        signal.signal(signal.SIGINT, handle_interrupt)
        events_monitor = threading.Thread(target=wait_for_events, name='Monitor')
        events_monitor.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_monitor.join()
        return 2

    def tcpdump(self):
        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.event
        def tcpdump(data):
            print(data)

        @self.sio.event
        def tcpdump_exit(data):
            print(data)
            self.LOOP = False

        def wait_for_events():
            data = {
                'id': self.BBID,
                'token': self.cache.get('token')
            }
            self.sio.emit(f'tcpdump', data)
            self.sio.wait()

        def handle_interrupt(signal, frame):
            self.LOOP = False
            print('\r')

        signal.signal(signal.SIGINT, handle_interrupt)
        events_tcpdump = threading.Thread(target=wait_for_events, name='tcpdump')
        events_tcpdump.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_tcpdump.join()
        return 2

    def ip(self, val) -> int:
        args = val.strip().split(' ')

        if len(args) == 1:
            print(Fore.YELLOW +
                  'Usage: ip [ OPTIONS ]\n' +
                  'where  \tOBJECT := { link | address | route | rule | neigh | ntable |\n' +
                  '\t\tmaddress | mrule | monitor }\n'
                  '\tOPTIONS := { -br }', Fore.RESET)
        if len(args) == 2:
            if (args[1].startswith('a') and args[1] in 'address' or
                    args[1].startswith('r') and args[1] in 'route' or
                    args[1].startswith('l') and args[1] in 'link' or
                    args[1].startswith('ru') and args[1] in 'rule' or
                    args[1].startswith('n') and args[1] in 'neigh' or
                    args[1].startswith('nt') and args[1] in 'ntable' or
                    args[1].startswith('ma') and args[1] in 'maddress' or
                    args[1].startswith('mr') and args[1] in 'mrule'):
                return self.command_request('ip', args[1], '')
            else:
                print(Fore.YELLOW +
                      'Usage: ip [ OPTIONS ]\n' +
                      'where  \tOBJECT := { link | address | route | rule | neigh | ntable |\n' +
                      '\t\tmaddress | mrule | monitor }\n'
                      '\tOPTIONS := { -br }')
        if len(args) == 3:
            if args[1].startswith('r') and args[1] in 'route' and args[2].startswith('g') and args[2] in 'get':
                print('need at least a destination address')
            else:
                if args[1] == '-br':
                    if (args[2].startswith('a') and args[2] in 'address' or
                            args[2].startswith('r') and args[2] in 'route' or
                            args[2].startswith('l') and args[2] in 'link' or
                            args[2].startswith('ru') and args[2] in 'rule' or
                            args[2].startswith('n') and args[2] in 'neigh' or
                            args[2].startswith('nt') and args[2] in 'ntable' or
                            args[2].startswith('ma') and args[2] in 'maddress' or
                            args[2].startswith('mr') and args[2] in 'mrule'):
                        return self.command_request('ip', args[2], '-br')
                    else:
                        print(f'Object {args[2]} is unknown, try "ip help"')
                else:
                    print(Fore.YELLOW +
                          'Usage: ip [ OPTIONS ]\n' +
                          'where  \tOBJECT := { link | address | route | rule | neigh | ntable |\n' +
                          '\t\tmaddress | mrule | monitor }\n'
                          '\tOPTIONS := { -br }')
        if len(args) == 4:
            if args[1].startswith('r') and args[1] in 'route' and args[2].startswith('g') and args[2] in 'get':
                return self.command_request('ip', args[1], f'get {args[3]}')
            else:
                print(Fore.YELLOW +
                      'Usage: ip [ OPTIONS ]\n' +
                      'where  \tOBJECT := { link | address | route | rule | neigh | ntable |\n' +
                      '\t\tmaddress | mrule | monitor }\n'
                      '\tOPTIONS := { -br }')
        return 2

    def command_request(self, val1, val2, val3) -> int:
        data = {
            'id': self.BBID,
            'command': val1,
            'args': val2,
            'flag': val3,
            'token': self.token
        }
        response = requests.post(f'{self.api_url}/bb/command', data=json.dumps(data), headers=self.headers)
        if response.status_code == 200:
            result = response.json()
            for i in result:
                print(i)
        else:
            print(f'{val1}: unknown err')

        return 2

    def ping(self, val) -> int:
        cm = val.split()

        if len(cm) < 2:
            print('ping: usage error: Destination address required')
            return 2

        ip = cm[1]
        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.event
        def ping_exit(data):
            self.LOOP = False
            if data != '':
                print(data)

        @self.sio.event
        def ping(data):
            if 'min/avg/max/mdev' in data:
                self.LOOP = False
            print(data.replace('admin  >', ''))

        def handle_interrupt(signal, frame):
            self.sio.emit('ping_exit', '')

        def wait_for_events():
            data = {
                "ip": ip,
                "id": self.BBID,
                "token": self.token
            }
            self.sio.emit('ping', data)
            self.sio.wait()

        signal.signal(signal.SIGINT, handle_interrupt)
        events_ping = threading.Thread(target=wait_for_events, name='Ping')
        events_ping.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_ping.join()
        return 2

    def debug(self, val) -> int:
        cm = val.split()

        if len(cm) < 3 and (val == 'vpn' or val == 'dhcp'):
            if val == 'vpn':
                print(f'Use -t [ipsec or ssl]')
            elif val == 'dhcp':
                print(f'Use -t [dhcpd or radius]')
            return 2

        if len(cm) > 1:
            if 'vpn' in val:
                if val == 'vpn -t ipsec' or val == 'vpn -t ssl':
                    pass
                elif 'vpn -t' in val:
                    print(f'Use -t [ipsec or ssl]')
                    return 2
                else:
                    print(f'debug-{val}: usage error: value invalid')
                    return 2

            if 'dhcp' in val:
                if val == 'dhcp -t dhcpd' or val == 'dhcp -t radius':
                    pass
                elif 'dhcp -t' in val:
                    print(f'Use -t [dhcpd or radius]')
                    return 2
                else:
                    print(f'debug-{val}: usage error: value invalid')
                    return 2

        if cm[0] == 'sdwan':
            if val != 'sdwan -i targets':
                print(f'Use -i [targets]')
                return 2

        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.event
        def debug(data):
            print(data)

        @self.sio.event
        def debug_exit(data):
            print(data)
            self.LOOP = False

        def wait_for_events():
            data = {
                'id': self.BBID,
                'type': val,
                'token': self.cache.get('token')
            }
            self.sio.emit(f'debug', data)
            self.sio.wait()

        def handle_interrupt(signal, frame):
            self.LOOP = False
            print('\r')

        signal.signal(signal.SIGINT, handle_interrupt)
        events_debug = threading.Thread(target=wait_for_events, name='Debug')
        events_debug.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_debug.join()
        return 2

    def mtr(self, val) -> int:
        cm = val.split()

        if len(cm) < 2:
            print('mtr: usage error: Destination address required')
            return 2

        ip = cm[1]

        if not validate_ip(ip):
            if not validate_url(ip):
                print('Failed to resolve host: Name or service not known')
                return 2

        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.on('mtr')
        def mtr(data):
            print(data)

        @self.sio.event()
        def mtr_exit(data):
            print(data)
            self.LOOP = False

        def wait_for_events():
            data = {
                'ip': ip,
                'id': self.BBID,
                'token': self.cache.get('token')
            }
            self.sio.emit('mtr', data)
            self.sio.wait()

        def handle_interrupt(signal, frame):
            self.sio.emit('mtr_exit', '')
            os.system("clear")
            print("\033[2J\n", end="")
            self.LOOP = False

        signal.signal(signal.SIGINT, handle_interrupt)
        events_mtr = threading.Thread(target=wait_for_events)
        events_mtr.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_mtr.join()
        return 2

    def traceroute(self, val) -> int:
        cm = val.split()

        if len(cm) < 2:
            print('mtr: usage error: Destination address required')
            return 2

        ip = cm[1]

        if not validate_ip(ip):
            if not validate_url(ip):
                print('Failed to resolve host: Name or service not known')
                return 2

        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.event
        def traceroute_exit(data):
            print(data)
            self.LOOP = False

        @self.sio.event
        def traceroute(data):
            linhas = data.split("\n")
            for linha in linhas:
                linha_format = linha.strip().ljust(80)
                print(linha_format)

        def wait_for_events():
            data = {
                'ip': ip,
                'id': self.BBID,
                'token': self.cache.get('token')
            }
            self.sio.emit(f'traceroute', data)
            self.sio.wait()

        events_traceroute = threading.Thread(target=wait_for_events)
        events_traceroute.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_traceroute.join()
        return 2
