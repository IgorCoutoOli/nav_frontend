import sys

import diskcache, re, requests, json, threading, time, signal, socketio
import clipboard
from halo import Halo
from colorama import Fore

import PySimpleGUI as sg

interrupted = False


class Tools:
    def __init__(self):
        self.cache = diskcache.Cache('~/.cache/nav/save.temp')
        self.api_url = 'http://172.16.151.141:4001'
        self.ACCESS = self.cache.get('access')
        self.clip = ''
        self.clip_code = ''
        self.LOOP = True
        self.sio = socketio.Client()

    def testasenha(self, command) -> int:
        if self.ACCESS < 2:
            return 0

        cm = re.findall(r'(?:[^\s"]+|"[^"]*")+', command)
        ip = cm[1]

        self.LOOP = True
        self.sio.connect(self.api_url)

        @self.sio.event
        def pass_result(data):
            spinner.stop()
            print(data)
            self.LOOP = False

        def wait_for_events():
            data = {
                'ip': ip,
                'token': self.cache.get('token')
            }

            self.sio.emit(f'testasenha', data)
            self.sio.wait()

        def handle_interrupt(signal, frame):
            self.LOOP = False
            spinner.stop()
            print('Cancelado...\r')

        spinner = Halo(text="Procurando senha.", spinner="dots")
        spinner.start()

        signal.signal(signal.SIGINT, handle_interrupt)
        events_testasenha = threading.Thread(target=wait_for_events, name='TestaSenha')
        events_testasenha.start()

        while self.LOOP:
            time.sleep(0.1)

        self.sio.disconnect()
        events_testasenha.join()
        return 2

    def a10(self):
        def adding(value):
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({
                'value': value,
                'status': 0 if values['-checkbox-'] else 3,
                'token': self.cache.get('token')
            })

            response = requests.post(f'{self.api_url}/tools/a10', data, headers=headers)

            if response.status_code == 200:
                window['-box-'].update('')
                if not values['-checkbox-']:
                    result = response.json()
                    result_print = ''
                    self.clip = result['response']

                    for linha in result['lines']:
                        if linha != 'enable' and linha != '' and linha != 'conf t':
                            result_print += linha + '\n'

                    self.clip_code = result_print
                    window['-box-'].update(value=result_print)
                else:
                    result = response.json()
                    self.clip = result['response']
                    window['-box-'].update(value='Adicionado com sucesso!')

        def removing(value):
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({
                'value': value,
                'status': 1 if values['-checkbox-'] else 4,
                'token': self.cache.get('token')
            })

            response = requests.post(f'{self.api_url}/tools/a10', data, headers=headers)

            if response.status_code == 200:
                window['-box-'].update('')
                if not values['-checkbox-']:
                    result = response.json()
                    result_print = ''
                    for line in result['lines']:
                        if line != 'enable' and line != '' and line != 'conf t':
                            result_print += line + '\n'

                    self.clip_code = result_print
                    window['-box-'].update(value=result_print)
                else:
                    window['-box-'].update(value='Removido com sucesso!')

        layout_window = [
            [sg.Text('IP :', size=(5, 0)), sg.Input(size=(15, 0), key='ip'), sg.Button('+', enable_events=True, key='-plus-')], #py.Button('-', enable_events=True, key='-minus-', disabled=True)],
            [sg.Frame('Lista de Porta', [
                [sg.Column(layout=[
                    [sg.Text('Porta Interna:', size=(15, 0)), sg.Input(size=(15, 0), key='port_interna_1'),
                     sg.Text('Porta Externa:', size=(15, 0)), sg.Input(size=(15, 0), key='port_externa_1')]
                ])]
            ], key='-COL01-')],
            [sg.Text('Você deseja fazer o que?', )],
            [sg.Button('Adicionar', key='-add-'), sg.Button('Remover', key='-remove-')],
            [sg.Checkbox(" Adicionar automaticamente.", key='-checkbox-', default=False)],
            [sg.Frame('Linhas do A10', [[sg.Multiline(size=(65, 20), key='-box-', disabled=True)]], key='-COL02-')],
            [sg.Button('Copiar resposta', key='-clip-'), sg.Button('Copiar codigo', key='-clip_code-')]
        ]

        count_port = 1

        window = sg.Window("RDR", layout=layout_window, element_justification='c')
        while True:
            event, values = window.read()

            if event in (sg.WIN_CLOSED, 'Fechar'):
                break

            elif event == '-minus-':
                if count_port > 1:
                    count_port -= 1
                else:
                    return

                window[f'column_{(count_port+1)}'].Widget.destroy()

                if count_port < 2:
                    window['-minus-'].update(disabled=True)

                if count_port < 11:
                    window['-plus-'].update(disabled=False)
            elif event == '-plus-':
                if count_port < 11:
                    count_port += 1
                else:
                    return

                window.extend_layout(
                    window['-COL01-'],
                    [
                        [sg.Column(layout=[[
                            sg.Text(f'Porta Interna:', size=(15, 0), key=f'text_i_{count_port}'),
                            sg.Input(size=(15, 0), key=f'port_interna_{count_port}'),
                            sg.Text(f'Porta Externa:', size=(15, 0), key=f'text_e_{count_port}'),
                            sg.Input(size=(15, 0), key=f'port_externa_{count_port}')]
                        ], key=f'column_{count_port}')]
                    ]
                )
                if count_port > 10:
                    window['-plus-'].update(disabled=True)
            elif event == '-add-':
                if values['-checkbox-']:
                    layout_popup = [
                        [sg.Text('Você tem certeza que deseja adicionar essas portas no A10?')],
                        [sg.Button('Sim', key='-accept-'), sg.Button('Não', key='-recuse-')]]

                    popup = sg.Window(title='Aviso', layout=layout_popup, element_justification='c')

                    while True:
                        event, val = popup.read()

                        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel') or event == '-recuse-':
                            break
                        if event == '-accept-':
                            window['-box-'].update(value='Adicionando... Aguarde!')
                            popup.Close()
                            adding(values)
                            break

                    popup.Close()
                else:
                    adding(values)
            elif event == '-remove-':
                if values['-checkbox-']:
                    layout_popup = [
                        [sg.Text('Você tem certeza que deseja remover essas portas no A10?')],
                        [sg.Button('Sim', key='-accept-'), sg.Button('Não', key='-recuse-')]]

                    popup = sg.Window(title='Aviso', layout=layout_popup, element_justification='c')

                    while True:
                        event, val = popup.read()

                        if event in (sg.WIN_CLOSED, 'Exit', 'Cancel') or event == '-recuse-':
                            break
                        if event == '-accept-':
                            window['-box-'].update(value='Removendo... Aguarde!')
                            popup.Close()
                            removing(values)
                            break

                    popup.Close()
                else:
                    removing(values)
            elif event == '-clip-':
                ask = ''

                for line in self.clip:
                    ask += f'{line}\n'

                try:
                    clipboard.copy(""+ask)
                except:
                    print(Fore.RED+'[ERRO] Não foi encontrado o xclip, instale apt install xclip.'+Fore.RESET)
            elif event == '-clip_code-':
                try:
                    clipboard.copy(self.clip_code)
                except:
                    print(Fore.RED+'[ERRO] Não foi encontrado o xclip, instale apt install xclip.'+Fore.RESET)

        window.close()
        return 2
