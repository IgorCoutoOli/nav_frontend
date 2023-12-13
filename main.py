from colorama import init, Fore, Back, Style
import os, diskcache, signal, readline, sys, atexit, requests, shutil, time, subprocess
from func.user import User
from func.olt import Olt
from func.tools import Tools
from func.bb import Blockbit
from func.mk import MK
from func.datacom import Datacom
from tqdm import tqdm


def interrupt(signal, frame):
    if not cache.get('lock') or not ISMAIN:
        sys.exit()


def save_history():
    readline.write_history_file(history_file)


def start():
    global ISMAIN

    while True:
        signal.signal(signal.SIGINT, interrupt)
        cache['EquipamentID'] = 0
        ISMAIN = True

        try:
            comando = input(Fore.WHITE + Style.NORMAL + Back.RESET + f"{USERNAME}# ")
        except:
            break

        ISMAIN = False
        result = command(comando)

        if result == 2:
            continue

        if result == 1:
            break

        text = os.popen(comando).read()

        if text != '':
            print(text.rstrip())


def autocompletar(texto, estado):
    if cache.get('EquipamentID') != 0:
        palavras = ['help', 'debug-dhcp', 'debug-firewall', 'debug-ppp', 'debug-vpn', 'debug-sdwan', 'tcpdump',
                    'uptime', 'ip', 'mtr', 'traceroute', 'ping', 'exit']
    else:
        palavras = ['help', 'blockbit-connect', 'blockbit-search', 'bbc', 'bbs', 'passwd', 'logout', 'lock', 'mk',
                    'exit']

        if ACCESS > 2:
            palavras += ['users-list', 'createuser', 'd', 'changeuser']

        if ACCESS > 1:
            palavras += ['olt', 'logs', 'testasenha', 'a10', 'datacom']

    opcoes = [p for p in palavras if p.startswith(texto)]
    if estado < len(opcoes):
        return opcoes[estado]
    else:
        return None


def command(comando) -> int:
    if comando.startswith('olt'):
        return oltClass.search(comando)
    if comando == 'exit':
        return 1
    if comando == 'logout':
        return userClass.logout()
    if comando.startswith('mk'):
        return mkClass.search(comando)
    if comando == 'passwd':
        return userClass.passwd()
    if comando == 'lock':
        if cache.get('lock'):
            cache['lock'] = False
            print(Fore.WHITE + 'lock: disable')
        else:
            cache['lock'] = True
            print(Fore.WHITE + 'lock: enable')
        return 2
    if comando == 'help':
        print(Fore.CYAN + '• Lista de comandos.', Fore.RESET)
        print('\t• blockbit-connect %Id [bbc %Id] - Conecta o usuário no blockbit selecionado.')
        print('\t• blockbit-search %Pesquisa [bbs %Pesquisa] - Lista todos blockbit que temos na rede atualmente.')
        print('\t• lock - Desabilita/Habilita a saída com CTRL+C.')
        print("\t• mk - Versão portatil do MK.")
        if ACCESS > 1:
            print('\t• olt s [%Pesquisa] - Procura nas logs do ultimo backup das OLT.')
            print('\t• testasenha [%IP] - Descobre a senha do rádio indicado.')
            print('\t• a10 - Abre interface para gerar ou adicionar os RDR no A10.')
            print("\t• datacom %Pesquisa - Lista todos os datacom com o nome passado na pesquisa.")
        if ACCESS > 2:
            print('\t• logs [%Pesquisa] [%Username?] - Procura nas logs do sistema.')
            print('\t• users-list - Lista todos os usuários.')
            print('\t• createuser - Adiciona novo usuário.')
            print('\t• deleteuser - Remove algum usuário.')
            print('\t• changeuser - Altera informações do usuário.')
        return 2
    if comando.startswith('testasenha'):
        return toolsClass.testasenha(comando)
    if comando.startswith('logs'):
        return userClass.logs(comando)
    if comando.startswith('createuser'):
        return userClass.createuser(comando)
    if comando.startswith('changeuser'):
        return userClass.changeuser(comando)
    if comando.startswith('deleteuser'):
        return userClass.deleteuser(comando)
    if comando == 'users-list':
        return userClass.list()
    if comando == 'a10':
        toolsClass.a10()
        return 2
    if comando.startswith('bbc') or comando.startswith('blockbit-connect'):
        return bbClass.connect(comando)
    if comando.startswith('bbs') or comando.startswith('blockbit-search'):
        return bbClass.search(comando)
    if comando.startswith('datacom'):
        return datacomClass.search(comando)


def update(old_version):
    try:
        api_url = 'http://172.16.151.141:4001'
        response = requests.get(f'{api_url}/version.txt')
        print(sys.argv[0])

        if response.status_code == 200:
            new_version = response.text.split("\n")[0].strip()

            if new_version != old_version:
                print(
                    Fore.WHITE + f'Version: ' + Fore.RED + old_version + ' -> ' + Fore.GREEN + new_version + Fore.YELLOW)
                url_arquivo = f'{api_url}/nav'

                caminho_local = sys.argv[0]

                caminho_novo = sys.argv[0] + '.new'
                response = requests.get(url_arquivo, stream=True)
                tamanho_arquivo = int(response.headers.get("Content-Length", 0))
                try:
                    with open(caminho_novo, "wb") as arquivo:
                        with tqdm(total=tamanho_arquivo, unit="B", unit_scale=True) as barra_progresso:
                            for chunk in response.iter_content(chunk_size=1024):
                                if chunk:
                                    arquivo.write(chunk)
                                    barra_progresso.update(len(chunk))
                    time.sleep(2)
                    shutil.move(caminho_local, caminho_local + '.bak')
                    shutil.move(caminho_novo, caminho_local)
                    subprocess.run(['chmod', '+x', caminho_local], check=True)

                except Exception as e:
                    print("Ocorreu um erro ao tentar atualizar. \n", str(e))
                    os._exit(0)

                return 1
            else:
                print(Fore.WHITE + f'Version: ' + Fore.GREEN + new_version)
        return 0
    except:
        print(Fore.RED + 'Failed connected api nav.' + Fore.WHITE)
        os._exit(0)


# Variaveis
cache = diskcache.Cache('~/.cache/nav/save.temp')
VERSION = '0.1.9'

os.system("clear")
print("\033[2J\n", end="")
background = '''
     ███╗░░██╗░█████╗░██╗░░░██╗
     ████╗░██║██╔══██╗██║░░░██║
     ██╔██╗██║███████║╚██╗░██╔╝
     ██║╚████║██╔══██║░╚████╔╝░
     ██║░╚███║██║░░██║░░╚██╔╝░░
     ╚═╝░░╚══╝╚═╝░░╚═╝░░░╚═╝░░░
'''.split('\n')
background_print = "\n".join(filter(lambda linha: linha.strip(), background))
print(Fore.GREEN + Style.BRIGHT + background_print)
print(Fore.WHITE + 'Navigation and Verification © copyright - 2022 ~ 2023')

# Class
userClass = User()
userClass.login()

oltClass = Olt()
toolsClass = Tools()
bbClass = Blockbit()
mkClass = MK()
datacomClass = Datacom()

if update(VERSION) == 1:
    print(Fore.WHITE + 'Terminal atualizado com sucesso.')
    os._exit(0)

version = cache.get('version')

if version != VERSION:
    cache['version'] = VERSION
    print(Fore.BLUE + '\n----- Changelog version 0.1.9 -----', Fore.RESET)
    print(Style.BRIGHT + '\n* Adicionado opção para copiar código gerado no A10.')
    print(Style.BRIGHT + '\n* Adicionado comando para listar datacom registrados.')
    print(Style.BRIGHT + '\n* Refeito sistema de login; é necessário solicitar novo acesso ao NOC.')
    print(Style.BRIGHT + '\n* Corrigido algumas inconsistências na busca do olt s.')
    print('\n* Corrigido alguns problemas no processo de atualização.', Style.RESET_ALL)

USER = cache.get('username').title().split('.')
ACCESS = cache.get('access')
USERNAME = f'{USER[0]} {USER[1]}'.upper()
cache['name'] = USERNAME
ISMAIN = True
history_file = os.path.expanduser('~/.config/nav_history.txt')

print(Fore.YELLOW +
      f'Nível de acesso: {"Administrador" if ACCESS == 3 else "Moderador" if ACCESS == 2 else "Usuário"}.', Fore.RESET)
print(f'Seja bem vindo {USER[0]} {USER[1]}.')

readline.set_history_length(1000)
readline.set_completer(autocompletar)
readline.set_completer_delims(' \t\n`@#$%^&*()=+[{]}\\|;:\'",<>?')
readline.parse_and_bind("tab: complete")
atexit.register(save_history)

try:
    readline.read_history_file(history_file)
except FileNotFoundError:
    open(history_file, 'a').close()

init()
start()

print('\nAdeus.👋')
