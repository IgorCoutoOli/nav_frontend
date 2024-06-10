import diskcache, json, re, os, requests, time, platform, subprocess
from colorama import Fore, Style
from tabulate import tabulate
from termcolor import colored
from halo import Halo


class MK:
    def __init__(self):
        self.cache = diskcache.Cache('~/.cache/nav/save.temp')
        self.api_url = 'http://172.16.151.141:4001'
        self.token = self.cache.get('token')
        self.headers = {'Content-Type': 'application/json'}

    def search(self, command):
        try:
            dados = json.load(open(os.path.expanduser('~/.config/mk.json'), 'r'))
        except FileNotFoundError:
            print(Fore.RED + 'MK não configurado,\n'
                             'Essa é uma versão portatil, você precisa acessar versão completa para configurar '
                             'acesso.', Fore.RESET)
            return 2

        search = re.findall(r'"([^"]*)"|(\S+)', command)
        result = [pair[0] or pair[1] for pair in search if not pair[1].startswith('-')]

        if len(result) < 3 or result[1] == 'r' and len(result) < 4:
            if len(search) < 2:
                return self.help()

            if '-h' in command or '--help' in command:
                return self.help()

            print('Error: unknown command "d" for "mk"\n'
                  'Você não quis dizer mk a, mk i, mk r ou mk s?\n'
                  'Aprenda a usar usando mk -h ou mk --help')
            return 2

        # Validar se ip
        def validate_ip(ip):
            default_ip = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            return re.match(default_ip, ip) is not None

        # Enviar comandos para o equipamento
        def ssh(ip, command):
            radius_user = dados['radius_user']
            radius_password = dados['radius_password']

            timeout = 2
            config = {
                "user": radius_user,
                "password": radius_password,
                "timeout": timeout
            }

            try:
                output = subprocess.check_output(
                    ['sshpass', '-p', config["password"],
                     'ssh', '-o', 'StrictHostKeyChecking=no',
                     '-o', 'ConnectTimeout=' + str(config["timeout"]),
                     '-l', config["user"], ip, command],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                return output
            except subprocess.CalledProcessError as e:
                print("Erro ao executar o comando SSH: ", e.output)

        # Adotando equipamento.
        if result[1] == 'a':
            if validate_ip(result[2]) is None:
                print(Fore.RED + 'Informe um IP válido' + Fore.RESET)
                return 2

            spinner = Halo(text="Adotando a routerboard...", spinner="dots")
            spinner.start()

            ssh(result[2],
                f':if ([:len [/system scheduler find where name=adota]] != 0) do={{/system scheduler remove adota}}; :if ([:len [/file find where name=adota.rsc]] != 0) do={{/file remove adota.rsc}}; /system scheduler add name=adota on-event=":delay 10000ms ;/tool fetch mode=http url=\\"http://187.86.128.242/nova/mk/adota.rsc\\"; /import adota.rsc" policy=ftp,reboot,read,write,policy,test,password,sniff,sensitive interval=00:20:00; /tool fetch mode=http url="http://187.86.128.242/nova/mk/adota.rsc"; /import adota.rsc')

            spinner.stop()

            print("Routerboard adotada com sucesso.")
            return 2

        # Registrando equipamento sem precisar adotar.
        if result[1] == 'r':
            if validate_ip(result[2]) is None:
                print(Fore.RED + 'Informe um IP válido' + Fore.RESET)
                return 2
            
            if result[3] is None or result[3] == "":
                print(Fore.RED + 'Informe um nome para registrar equipamento' + Fore.RESET)
                return 2
            
            spinner = Halo(text="Registrando equipamento...", spinner="dots")
            spinner.start()

            data = {
                'token': self.token,
                'ip': result[2],
                'identify': result[3],
                'secret': dados
            }            
            response = requests.post(f'{self.api_url}/mk/register', data=json.dumps(data), headers=self.headers)
            spinner.stop()
            
            if response.status_code == 200:
                print('Equipamento registrado com sucesso com a senha ' + Fore.GREEN + response.json() + Fore.RESET)
            else:
                print('Não foi possivel adicionar equipamento.')
            return 2

        flags = {
            'backup': False,
            'inactive': False,
            'reset': False,
            'senha': False,
            'equipament': False,
        }

        if '-b' in command or '--backup' in command:
            flags['backup'] = True

        if '-i' in command or '--inactive' in command:
            flags['inactive'] = True

        if '-r' in command or '--reset' in command:
            flags['reset'] = True

        if '-s' in command or '--senha' in command:
            flags['senha'] = True

        data = {
            'token': self.token,
            'flags': flags,
            'search': result[2],
            'type': result[1],
            'secret': dados
        }
        response = requests.post(f'{self.api_url}/mk/search', data=json.dumps(data), headers=self.headers)

        # Listando os mikrotik
        def list_rb(rbs):
            tabela = [["ID", "IP Preferencial", "Nome", "Modelo", "Firmware", "Última Atualização"]]

            for rb in rbs:
                date = time.strptime(rb['updated_at'], "%Y-%m-%dT%H:%M:%S.000000Z")
                formatted_date = time.strftime("%d/%m/%Y", date)

                tabela.append([
                    rb['id'],
                    rb['ip_preferencial'],
                    rb['identity'],
                    rb['model'],
                    rb['firmware'],
                    formatted_date
                ])

            if len(tabela) == 1:
                print(colored("Não foi encontrado nenhum resultado para a pesquisa.", "red"))
                return 2

            print(tabulate(tabela, headers="firstrow", tablefmt="pretty"))

            try:
                selected_id = input(Style.BRIGHT + "Digite o ID da routerboard: " + Style.RESET_ALL)
            except:
                print('C^')
                return 2

            selected_routerboard = None
            for rb in routerboards:
                if str(rb['id']) == selected_id:
                    selected_routerboard = rb
                    break

            if selected_routerboard is None:
                selected_routerboard = rbs[0]

            return selected_routerboard

        # Verificar se solicitou a senha.
        def show_pass(rb):
            if flags['senha']:
                try:
                    if rb['password'] == '':
                        print('A senha desta routerboard não foi definida.')
                    else:
                        print(
                            'A senha da routerboard é: ' + Fore.YELLOW + rb['password'] + Fore.RESET)
                except:
                    print(Fore.RED + 'Funcionalidade de uso restrito ao Setor de Meme.' + Fore.RESET)
                return 2

        # Selecionar ip
        def select_ip(rb):
            print(Fore.YELLOW + Style.BRIGHT + "Escolha um IP para abrir o Winbox:", Fore.RESET, Style.RESET_ALL)

            for index, ip in enumerate(rb['ips']):
                print(f"{index + 1}. {ip}")
                try:
                    selected_ip_index = int(
                        input(
                            Style.BRIGHT + "Digite o número correspondente ao IP desejado: " + Style.RESET_ALL)) - 1
                except:
                    print('C^')
                    return 2

                if 0 <= selected_ip_index < len(rb['ips']):
                    selected_ip = rb['ips'][selected_ip_index]
                    return self.open_winbox(selected_ip, dados['radius_user'], dados['radius_password'],
                                            os.path.expanduser(dados['winbox_path']), dados['windows'])
                else:
                    selected_ip = rb['ips'][0]
                    return self.open_winbox(selected_ip, dados['radius_user'], dados['radius_password'],
                                            os.path.expanduser(dados['winbox_path']), dados['windows'])

        # Selecionar backup
        def backup(rb):
            if flags['backup']:
                send = {
                    'token': self.token,
                    'id': rb['id'],
                    'type': 0,
                    'index': 0,
                    'secret': dados
                }

                res1 = requests.post(f'{self.api_url}/mk/search/backup', data=json.dumps(send), headers=self.headers)
                if res1.status_code == 200:
                    backups = res1.json()
                    backup_table = []
                    for i, backup in enumerate(backups):
                        backup_date = time.strptime(backup['created_at'], "%Y-%m-%dT%H:%M:%S.000000Z")
                        formatted_date = time.strftime("%d %b %Y", backup_date)
                        backup_table.append([i, formatted_date])

                    print(tabulate(backup_table, headers=["Índice", "Data"], tablefmt="pretty"))
                    try:
                        backup_index = int(
                            input(Style.BRIGHT + "Digite o índice do Backup que deseja acessar: " + Style.RESET_ALL))
                    except:
                        backup_index = 0

                    send['type'] = 1
                    send['index'] = backup_index
                    res2 = requests.post(f'{self.api_url}/mk/search/backup', data=json.dumps(send),
                                         headers=self.headers)
                    if res2.status_code == 200:
                        backup = res2.json()

                        savefile = f"./backup-MK/{rb['identity']}.txt"
                        os.makedirs(os.path.dirname(savefile), exist_ok=True)
                        with open(savefile, "w") as f:
                            f.write(backup)
                            
                        print(savefile)

                return 2

        # Resetar ip preferencial
        def resetIP(rb):
            if flags['reset']:
                send = {
                    'token': self.token,
                    'id': rb['id'],
                    'secret': dados
                }

                res = requests.post(f'{self.api_url}/mk/resetip', data=json.dumps(send), headers=self.headers)
                if res.status_code == 200:
                    print('IP resetado com sucesso.')

                return 2

        if result[1] == 's':
            if response.status_code == 200:
                routerboards = response.json()

                selected = list_rb(routerboards)
                if selected == 2:
                    return 2

                r1 = show_pass(selected)
                if r1 == 2:
                    return 2

                r2 = backup(selected)
                if r2 == 2:
                    return 2

                r3 = resetIP(selected)
                if r3 == 2:
                    return 2

                return select_ip(selected)

        if result[1] == 'i':
            if response.status_code == 200:
                routerboard = response.json()

                result = show_pass(routerboard)

                if result == 2:
                    return 2

                if routerboard['ip_preferencial'] is not None:
                    return self.open_winbox(routerboard['ip_preferencial'], dados['radius_user'],
                                            dados['radius_password'],
                                            os.path.expanduser(dados['winbox_path']), dados['windows'])

                return select_ip(routerboard)
            return 2

        return self.help()

    def help(self):
        print("Essa aplicação tem como propósito executar terefas de gerenciamento de Routerboards Mikrotik.\n\n"
              "Usage:\n"
              "  mk [command]\n\n"
              "Available Commands:\n"
              "  a\tPermite adotar uma routerboard informando o IP da mesma. Exemplo: mk a 192.168.0.1\n"
              "  i\tAcessa uma routerboard pelo id. Exemplo: mk i 1234\n"
              "  s\tRealiza uma busca por routerboards. Exemplo: mk s 'Tergrasa CE' ou mk s 172.16.20.168\n\n"
              "  r\tPermite que adote uma routerboard sem ela estar online, mas apenas funciona nessa versão do mk. Exemplo: mk r 172.16.20.168 'Tergrasa CE'\n\n"
              "Flags:\n"
              "  -b, --backup\t\tLista os últimos 10 backups de uma Routerboard e permite selecionar um deles para download.\n"
              "  \t\t\tExemplo:\n"
              "  \t\t\t\tmk i 1234 -b\n"
              "  \t\t\t\tmk s Teste -b\n"
              "  -h, --help\t\tExibe essas informações.\n"
              "  -i, --inactive\t\tExibe as routerboards inativas a mais de 7 dias.\n"
              "  -r, --reset\t\tReseta a informação de IP Preferencial.\n"
              "  \t\t\tExemplo:\n"
              "  \t\t\t\tmk s Teste -r\n"
              "  \t\t\t\tmk i 1234 -r\n"
              "  -s, --senha\t\tExibe a senha da routerboard.\n",
              Fore.RED + "Aviso: Esse é uma versão portatil da ferramenta mk.", Fore.RESET
              )
        return 2

    def open_winbox(self, ip, user, password, path, windows):
        if windows:
            winbox = f'"{path}" {ip} {user} {password} 2>&1 > NUL'
        else:
            wine_debug = "-all" if platform.system() == "Linux" else ""
            winbox = f'WINEDEBUG={wine_debug} wine {path} {ip} {user} {password} 2>&1 > /dev/null &'

        try:
            if platform.system() == "Windows":
                subprocess.run([path, ip, user, password], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            else:
                subprocess.Popen(f'{winbox}', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao abrir Winbox")
        except InterruptedError as e:
            print(e)

        return 2
