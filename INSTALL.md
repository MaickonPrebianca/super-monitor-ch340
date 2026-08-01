# Guia de Instalação e Configuração — Super Monitor

Este guia orienta o passo a passo para instalar os requisitos, configurar permissões de portas seriais no Linux, instalar as fontes numéricas e configurar a execução automática ao ligar o computador.

---

## 1. Pré-requisitos do Sistema

No Ubuntu, Debian, Linux Mint ou distribuições derivadas, instale os pacotes necessários via `apt`:

```bash
sudo apt update
sudo apt install python3 python3-tk python3-pip python3-pil python3-pil.imagetk fonts-dseg -y
```

Em seguida, instale a biblioteca PySerial via pip ou apt:

```bash
pip3 install pyserial
# ou via pacote do sistema:
# sudo apt install python3-serial
```

---

## 2. Permissão de Acesso à Porta Serial USB (CH340 / CH341)

Para que o script acesse os dispositivos em `/dev/ttyUSB*` sem requerer privilégios de `root` (`sudo`), adicione seu usuário ao grupo `dialout`:

```bash
sudo usermod -aG dialout $USER
```

> ⚠️ **Importante:** Após executar este comando, **faça logoff e login novamente** (ou reinicie o sistema) para que a alteração do grupo surta efeito.

---

## 3. Instalação do Modelo de Fonte Estilo 7 Segmentos

Para obter a melhor fidelidade visual estilo painel digital, o aplicativo detecta e utiliza fontes de 7 segmentos como **DSEG7 Classic**, **Digital-7** ou **VT323**.

### Opção A: Instalação via pacote do repositório (Recomendado)
O pacote `fonts-dseg` instalado no passo 1 já disponibiliza a família DSEG no sistema.

### Opção B: Download manual da fonte
1. Baixe a fonte [DSEG7 Classic](https://www.dafont.com/pt/dseg.font) ou [Digital-7](https://www.dafont.com/pt/digital-7.font).
2. Extraia o arquivo `.ttf`.
3. Mova o arquivo `.ttf` para a pasta de fontes do seu usuário:
   ```bash
   mkdir -p ~/.local/share/fonts
   cp DSEG7Classic-Bold.ttf ~/.local/share/fonts/
   fc-cache -f -v
   ```

---

## 4. Executando o Aplicativo

Certifique-se de dar permissão de execução ao script principal:

```bash
chmod +x main.py
./main.py
```

---

## 5. Configuração de Início Automático com o Sistema (Autostart)

Para que o **Super Monitor** inicie automaticamente ao fazer login na sua sessão de área de trabalho (GNOME, KDE, XFCE, Cinnamon), crie um arquivo de inicialização `.desktop`:

1. Crie o arquivo `supermonitor.desktop` em `~/.config/autostart/`:
   ```bash
   mkdir -p ~/.config/autostart
   nano ~/.config/autostart/supermonitor.desktop
   ```

2. Cole o conteúdo abaixo (ajuste os caminhos para onde você salvou o projeto):

   ```ini
   [Desktop Entry]
   Type=Application
   Name=Super Monitor Water Cooler
   Comment=Monitorador e Controlador do Display do Water Cooler
   Exec=/usr/bin/python3 /caminho/absoluto/para/seu/projeto/main.py
   Path=/caminho/absoluto/para/seu/projeto/
   Terminal=false
   Icon=utilities-system-monitor
   Categories=Utility;System;
   X-GNOME-Autostart-enabled=true
   ```

3. Dê permissão de execução ao arquivo de atalho:
   ```bash
   chmod +x ~/.config/autostart/supermonitor.desktop
   ```

Pronto! Na próxima inicialização do sistema o aplicativo será carregado automaticamente em segundo plano.
