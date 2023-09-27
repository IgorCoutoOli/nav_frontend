import diskcache, re, requests, json
from colorama import Fore, Back


class Olt:
    def __init__(self):
        self.cache = diskcache.Cache('~/.cache/nav/save.temp')
        self.ACCESS = self.cache.get('access')
        self.api_url = 'http://172.16.151.141:4001'

    def search(self, command) -> int:
        if self.ACCESS < 2:
            return 0

        pesquisa = re.findall(r'(?:[^\s"]+|"[^"]*")+', command)
        flags = {
            'olt': '',
            'info': False,
            'serial': False,
            'client': False,
            'mng': False
        }

        if len(pesquisa) < 3:
            return self.help()

        if pesquisa[1] != 's':
            return self.help()

        if pesquisa[2] == '-i' or pesquisa[2] == '--info' or pesquisa[2] == '-s' or pesquisa[2] == '--serial' or \
                pesquisa[2] == '-c' or pesquisa[2] == '--client' or pesquisa[2] == '-m' or pesquisa[2] == '--mng' or \
                pesquisa[2] == '-o' or pesquisa[2] == '--olt':
            print(Back.RED + 'Informe sua pesquisa. Exemplo olt s Pesquisa.' + Back.RESET)
            return 2

        if '-i' in pesquisa or '--info' in pesquisa:
            flags['info'] = True
        if '-s' in pesquisa or '--serial' in pesquisa:
            flags['serial'] = True
        if '-c' in pesquisa or '--client' in pesquisa:
            flags['client'] = True
        if '-m' in pesquisa or '--mng' in pesquisa:
            flags['mng'] = True
        if '-o' in pesquisa or '--olt' in pesquisa:
            if '23' in pesquisa:
                flags['olt'] = '23'
            elif '24' in pesquisa:
                flags['olt'] = '24'
            elif '25' in pesquisa:
                flags['olt'] = '25'
            elif '34' in pesquisa:
                flags['olt'] = '34'
            elif '35' in pesquisa:
                flags['olt'] = '35'
            elif '36' in pesquisa:
                flags['olt'] = '36'
            elif '37' in pesquisa:
                flags['olt'] = '37'
            elif '38' in pesquisa:
                flags['olt'] = '38'
            else:
                print(Back.RED + 'Informe uma olt na sua pesquisa. Exemplo olt s Pequisa OLT -o.' + Back.RESET)
                return 2
        return self.find(pesquisa[2], flags)

    def help(self) -> int:
        print("Ferramenta de gerenciamento e acesso de OLT's ZTE.\n\n" +
              "Usage:\n" +
              "  olt [command]\n\n" +
              "Available Commands:\n" +
              "  help\tHelp about any command\n" +
              "  s\tBusca informação passada no último backup feito das OLT.\n\n" +
              "Flags:\n" +
              "  -c, --client\tLocaliza para qual cliente esta provisionado o serial.\n" +
              "\tExemplo:\n" +
              "\t     olt s Serial -c\n" +
              "  -h, --help\thelp for olt\n" +
              "  -i, --info     Lista as configurações da ONU.\n" +
              "\tExemplo:\n" +
              "\t     olt s Cliente -i\n" +
              "  -m, --mng      Retorna 'pon-onu-mng' da placa e posição informadas.\n" +
              "\tExemplo:\n" +
              "\t     olt s x/x/x:x -m\n" +
              "  -o, --olts     Define a pesquisa para apenas uma OLT especifica.\n" +
              "\tExemplo:\n" +
              "\t     olt s Pesquisa OLT -o\n" +
              "  -s, --serial   Retorna o modelo e serial da ONU do cliente pela gpon e porta.\n"
              "\tExemplo:\n" +
              "\t     olt s x/x/x:x -s\n"
              )
        return 2

    def find(self, search, flags) -> int:
        olt = ['23', '24', '25', '34', '35', '36', '37', '38']
        c = False

        for i in olt:
            if i != flags['olt'] and flags['olt'] != '':
                continue

            if flags['mng']:
                result = self.route(search, 'mng', i)
            elif flags['client']:
                result = self.route(search, 'client', i)
            elif flags['info']:
                result = self.route(search, 'info', i)
            elif flags['serial']:
                result = self.route(search, 'serial', i)
            else:
                result = self.route(search, 'default', i)

            if result == 'exit':
                return 2

            if result != '':
                c = True
                print(Fore.BLUE + f'Pesquisa OLT {i}' + Fore.WHITE)
                print(Fore.YELLOW + f'{result}')

        if not c:
            print(Back.RED + 'Nada encontrado.' + Back.RESET)
        return 2

    def route(self, search, flag, olt) -> str:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.api_url}/olt/search/' + flag, data=json.dumps(
            {'search': search.replace('"', ''), 'olt': olt, 'token': self.cache.get('token')}), headers=headers)
        if response.status_code == 200:
            result = response.text.replace('\\n', '\n').rstrip()

            if result == '"109"':
                print(Fore.RED+'Não foi possivel ler backup da OLT.')
                return 'exit'
            else:
                return result
        else:
            print(Fore.WHITE + Back.RED + 'olt s: command error' + Back.RESET)
            return 'exit'
