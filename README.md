
# NAV Frontend

Uma interface **CLI interativa** desenvolvida para ser utilizada em uma **empresa de internet** pelos times de **suporte N1 até N3**.  
O objetivo é **agilizar processos de atendimento**, facilitar o gerenciamento de equipamentos de rede e **garantir a proteção dos dados dos clientes**.  

O projeto centraliza operações comuns em um único ponto, oferecendo **autocompletar de comandos, histórico persistente e integração com ferramentas externas**.  

---

## 📌 Funcionalidades

- **CLI com autocompletar** (setas e tab)  
- **Gestão de usuários e níveis de acesso (N1 → N3)**  
- **Gerenciamento de OLTs** (ZTE, Datacom, etc.)  
- **Integração com Mikrotik** via Winbox (Wine)  
- **Conexões seguras SSH** com `sshpass`  
- **Ferramentas auxiliares** (clipboard, logs, cache)  
- **Histórico persistente** em `~/.config/nav/history`  
- **Cache local** em `~/.cache/nav/`  

---

## 🛠️ Estrutura do Projeto

```
nav_frontend/
├── func/              # Módulos principais de cada função
│   ├── mk.py          # Integração com Mikrotik
│   ├── olt.py         # Operações em OLTs
│   ├── tools.py       # Ferramentas auxiliares
│   ├── user.py        # Gestão de usuários e níveis de acesso
│   └── ...            # Outros módulos (datacom, bb, etc.)
├── main.py            # CLI principal com roteamento de comandos
├── requirements.txt   # Dependências do projeto
```

---

## 🚀 Instalação e Uso

### 1. Clone o repositório
```bash
git clone https://github.com/IgorCoutoOli/nav_frontend.git
cd nav_frontend
```

### 2. Crie um ambiente virtual (recomendado)
```bash
python3 -m venv venv
source venv/bin/activate   # Linux
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação
```bash
python main.py
```

---

## ⚡ Principais Comandos

- `mk` → Acessa funções relacionadas ao Mikrotik  
- `olt` → Gerenciamento de OLTs (ZTE, Datacom etc.)  
- `a10` → Operações específicas de rede A10  
- `tools` → Utilitários auxiliares  
- `user` → Gerenciamento de usuários (N1 → N3)  

---

## 👤 Gestão de Usuários

O sistema possui níveis de acesso:  

- **N1** → Operações básicas de consulta  
- **N2** → Permissões intermediárias (execução de ações críticas)  
- **N3** → Administrador (controle total)  

Cada comando verifica o nível do usuário antes de ser executado, garantindo segurança e conformidade.  

---

## 📂 Armazenamento Local

- **Histórico de comandos** → `~/.config/nav/history`  
- **Cache persistente** → `~/.cache/nav/`  

---

## 🔧 Dependências Externas

Além das libs Python listadas em `requirements.txt`, são necessárias algumas ferramentas externas:  

- **wine** → execução do Winbox (Mikrotik)  
- **sshpass** → conexões automatizadas SSH  
- **xclip** → integração com clipboard no Linux  

---

## 📜 Licença

Este projeto é distribuído sob a licença **MIT**. Sinta-se à vontade para usar, modificar e contribuir!