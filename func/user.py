from colorama import Fore, Style
from getpass import getpass
import diskcache, requests, json, os, sys, re
from prettytable import PrettyTable


class User:
    def __init__(self):
        self.cache = diskcache.Cache('~/.cache/nav/save.temp')
        self.api_url = 'http://172.16.151.141:4001'
        self.ACCESS = self.cache.get('access')

    def login(self):
        headers = {'Content-Type': 'application/json'}

        token = self.cache.get('token')
        if not token:
            while True:
                try:
                    username = input("LOGIN# Username: ")
                    password = getpass("LOGIN# Password: ")
                except:
                    print('')
                    os._exit(0)

                data = json.dumps({'username': username, 'password': password})
                response = requests.post(f'{self.api_url}/users/login', data, headers=headers)

                if response.status_code == 200:
                    result = response.json()

                    self.cache['username'] = result['username']
                    self.cache['token'] = result['token']
                    self.cache['access'] = result['access']
                    self.cache['sector'] = result['sector']
                    if password == 'mudar123' or password == 'mudar' or password == 'mudar12345':
                        print(
                            Fore.RED + Style.BRIGHT + 'Aviso: Você esta com a senha padrão, use o comando "passwd"\
                             para alterá-la' + Style.RESET_ALL, Fore.RESET)
                    break
                else:
                    print(Fore.RED + f'Usuário ou senha inválido.', Fore.RESET)
        else:
            response = requests.post(f'{self.api_url}/users/login', data=json.dumps({'token': token}),
                                     headers=headers)

            if response.status_code == 200:
                result = response.json()

                self.cache['username'] = result['username']
                self.cache['access'] = result['access']
                self.cache['sector'] = result['sector']
            else:
                self.cache['token'] = ''
                self.login()
                return
        return

    def logout(self) -> int:
        self.cache.delete('token')
        python = sys.executable
        os.execl(python, python, *sys.argv)
        return 2

    def passwd(self) -> int:
        print(f'Changing password for {self.cache.get("name")}')

        try:
            current = getpass('Current password: ')
            new = getpass('New password: ')
            renew = getpass('Retype new password: ')
        except:
            print('')
            return 2

        if new != renew:
            print('Sorry, passwords do not match.')
            return 2

        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.api_url}/terminal/passwd',
                                 data=json.dumps({'current': current, 'password': new, 'token': self.cache.get('token')}),
                                 headers=headers)

        if response.status_code == 200:
            print('passwd: password updated successfully')
            self.logout()
        else:
            print('passwd: password unchanged')
        return 2

    def logs(self, command) -> int:
        if self.ACCESS < 2:
            return 0

        cm = re.findall(r'(?:[^\s"]+|"[^"]*")+', command)

        if len(cm) < 2:
            print('logs: search invalid')
            return 2

        username = cm[2].strip('"') if len(cm) > 2 else ''
        search = cm[1].strip('"')

        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.api_url}/users/log',
                                 data=json.dumps({'search': search, 'username': username, 'token': self.cache.get('token')}),
                                 headers=headers)
        if response.status_code == 200:
            result = response.json()
            tabela = PrettyTable()
            tabela.field_names = ["LOG", "EQUIPAMENTO", "USERNAME", "DATE"]

            for item in result:
                tabela.add_row([item['Log'], item['Equipament'], item['Username'], item['Data']])
            print(tabela)
        else:
            print('logs: access unauthorized')

        return 2

    def createuser(self, command) -> int:
        if self.ACCESS < 3:
            return 0

        args = command.strip().split(' ')

        if len(args) == 2:
            if args[1] == '-h':
                print('Criação de usuário:\n\t' + args[
                    0] + ' [USERNAME] [ACCESS] [GROUP]\n\n\tOPTION : { USERNAME\t: Nome do usuário.\n\t\t   ACCESS\t: Administrador, Moderador ou Usuário\n\t\t   GROUP\t: NOC, STI ou Suporte }')
                return 2

        if len(args) != 4:
            print(f'{args[0]}: invalid parameters. Use: {args[0]} -h')
            return 2

        if args[1].isspace() or args[2].lower() != 'administrador' and args[2].lower() != 'moderador' and args[
            2].lower() != 'usuário' or args[3].lower() != 'noc' and args[3].lower() != 'sti' and args[
            3].lower() != 'suporte':
            print(f'{args[0]}: invalid parameters. Use: {args[0]} -h')
            return 2

        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.api_url}/users/createuser', data=json.dumps(
            {'username': args[1].lower(), 'group': args[3].lower(), 'access': args[2].lower(), 'token': self.cache.get('token')}), headers=headers)
        if response.status_code == 200:
            print(Fore.GREEN + f'Usuário criado com sucesso.\nUsuario: {args[1].lower()}\nPassword: mudar123')
        else:
            print(f'createuser: creation failed')

        return 2

    def changeuser(self, command) -> int:
        if self.ACCESS < 3:
            return 0

        name = ''
        access = ''
        group = ''
        password = ''
        args = command.strip().split(' ')

        if len(args) == 1:
            print(f'{args[0]}: invalid parameters. Use: {args[0]} -h')
            return 2
        if len(args) == 2:
            if args[1] == '-h':
                print('Edição de usuario:\n\t' + args[
                    0] + ' [USERNAME] -a [ACCESS] -s [GROUP] -p [PASSWORD]\n\n\tOPTION : { USERNAME\t: Nome do usuario.\n\t\t   ACCESS\t: Administrador, Moderador ou Usuário\n\t\t   GROUP\t: NOC, STI ou Suporte\n\t\t   PASSWORD\t: Nova senha do usuário. }')
                return 2
            else:
                print(f'{args[0]}: invalid parameters. Use: {args[0]} -h')
                return 2
        if len(args) >= 3:
            name = args[1]
        if len(args) >= 4:
            if args[2] == '-a':
                access = args[3]
            if args[2] == '-s':
                group = args[3]
            if args[2] == '-p':
                password = args[3]
        if len(args) >= 6:
            if args[4] == '-a':
                access = args[5]
            if args[4] == '-s':
                group = args[5]
            if args[4] == '-p':
                password = args[5]
        if len(args) >= 8:
            if args[6] == '-a':
                access = args[7]
            if args[6] == '-s':
                group = args[7]
            if args[6] == '-p':
                password = args[7]

        if name.isspace() or access != '' and access.lower() != 'administrador' and access.lower() != 'moderador' and access.lower() != 'usuário' or group != '' and group.lower() != 'noc' and group.lower() != 'sti' and group.lower() != 'suporte':
            print(f'{args[0]}: invalid parameters. Use: {args[0]} -h')
            return 2

        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.api_url}/terminal/changeuser', data=json.dumps(
            {'username': name, 'group': group.lower(), 'access': access.lower(), 'password': password,
             'token': self.cache.get('token')}), headers=headers)
        if response.status_code == 200:
            print(Fore.GREEN + f'Usuário editado com sucesso.')
        else:
            print(f'deleteuser: edited failed')
        return 2

    def deleteuser(self, command) -> int:
        if self.ACCESS < 3:
            return 0

        args = command.strip().split(' ')

        if len(args) > 1:
            if args[1] == '-h':
                print('Remoção de usuário:\n\t' + args[
                    0] + ' [USERNAME]\n\n\tOPTION : { USERNAME : Nome do usuário. }')
                return 2

            headers = {'Content-Type': 'application/json'}
            response = requests.post(f'{self.api_url}/terminal/deleteuser',
                                     data=json.dumps({'username': args[1], 'token': self.cache.get('token')}), headers=headers)
            if response.status_code == 200:
                print(Fore.GREEN + f'Usuário deletado com sucesso.')
            else:
                print(f'deleteuser: deleted failed')
        else:
            print(f'{args[0]}: invalid parameters. Use: {args[0]} -h')

        return 2

    def list(self) -> int:
        if self.ACCESS < 3:
            return 0

        headers = {'Content-Type': 'application/json'}
        response = requests.post(f'{self.api_url}/terminal/userslist', data=json.dumps({'token': self.cache.get('token')}),
                                 headers=headers)

        if response.status_code == 200:
            result = response.json()

            tabela = PrettyTable()
            tabela.field_names = ["USERNAME", "ACESSO", "SETOR"]

            for item in result:
                tabela.add_row([item['Username'], item['Acesso'], item['Setor']])
            print(tabela)
        else:
            print('user list: access unauthorized')

        return 2
