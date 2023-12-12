import diskcache, json, re, os, requests, time, platform, subprocess
from tabulate import tabulate
from termcolor import colored


class Datacom:
    def __init__(self):
        self.cache = diskcache.Cache('~/.cache/nav/save.temp')
        self.headers = {'Content-Type': 'application/json'}
        self.api_url = 'http://172.16.151.141:4001'
        self.token = self.cache.get('token')

    def search(self, command):
        search = re.findall(r'"([^"]*)"|(\S+)', command)
        result = [pair[0] or pair[1] for pair in search if not pair[1].startswith('-')]

        def list_dt(dts):
            tabela = [["IP", "Nome", "Modelo", "Firmware", "Serial", "MAC", "Senha"]]
            for dt in dts:
                tabela.append([
                    dt['ip'],
                    dt['name'],
                    dt['model'],
                    dt['firmware'],
                    dt['serial'],
                    dt['mac'],
                    dt['password']
                ])

            if len(tabela) == 1:
                print(colored("Não foi encontrado nenhum resultado para a pesquisa.", "red"))
                return 2

            print(tabulate(tabela, headers="firstrow", tablefmt="pretty"))

        if len(result) > 1:
            data = {
                'token': self.token,
                'search': result[1]
            }
            response = requests.post(f'{self.api_url}/datacom/search', data=json.dumps(data), headers=self.headers)

            if response.status_code == 200:
                datacom_list = response.json()
                list_dt(datacom_list)
        else:
            print('Error: unknown search.')
        return 2
