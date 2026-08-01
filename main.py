#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import Toplevel, Label, Button, Frame

# Importação condicional do PySerial
try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

# Importação condicional do Pillow para suporte a múltiplos formatos de imagem (caso instalado)
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ==============================================================================
# CONSTANTES E REGRAS DE NEGÓCIO
# ==============================================================================
USB_VID_QINHENG = 0x1A86
USB_PIDS_CONHECIDOS = {0x5523: "CH341", 0x5512: "CH341", 0x7523: "CH340", 0x7584: "CH340S"}
BAUDRATE_PADRAO = 115200

REG_TEMP = 0x01
DISPLAY_OFF = bytes((0x02, 0x00, 0x01))
KEEPALIVE = bytes((0x02, 0x01, 0x00))
ACK_WRITE = 0x21

TEMP_MIN, TEMP_MAX = 0.0, 99.9
RPM_MAX = 9999

FAN_BASE = 500
PUMP_MIN, PUMP_MAX = 800, 2800
PUMP_POR_FAN = 1.6
KEEPALIVE_INTERVAL = 69.0

# Limites para a escala visual dos arcos
FAN_MAX_GAUGE = 2800.0

# Caminho da imagem de doação (ajuste se o nome do arquivo for diferente)
DONATION_IMAGE_FILENAME = "image.png"


def pump_from_fan(fan_rpm: int) -> int:
    """Calcula Pump Speed por proporção direta do Fan Speed."""
    pump = PUMP_MIN + (fan_rpm - FAN_BASE) * PUMP_POR_FAN
    return int(max(PUMP_MIN, min(PUMP_MAX, round(pump))))


# ==============================================================================
# LEITURA DE SENSORES E COMUNICAÇÃO HARDWARE
# ==============================================================================
class WaterCooler:
    def __init__(self, port: str | None = None, baud: int = BAUDRATE_PADRAO):
        self.port = port
        self.baud = baud
        self._ser = None

    @staticmethod
    def autodetect() -> str | None:
        if list_ports is None:
            return None
        for p in list_ports.comports():
            if p.vid == USB_VID_QINHENG:
                return p.device
        return None

    def open(self):
        if serial is None:
            return
        if not self.port:
            self.port = self.autodetect()
        if not self.port:
            return
        try:
            self._ser = serial.Serial(
                port=self.port, baudrate=self.baud,
                bytesize=8, parity="N", stopbits=1,
                timeout=0.15, write_timeout=1.0
            )
        except Exception:
            self._ser = None

    def close(self):
        if self._ser and self._ser.is_open:
            self._ser.close()

    def _cmd(self, pkt: bytes) -> bytes:
        if not self._ser or not self._ser.is_open:
            return b""
        try:
            self._ser.reset_input_buffer()
            self._ser.write(pkt)
            self._ser.flush()
            time.sleep(0.1)
            return self._ser.read(16)
        except Exception:
            return b""

    def keepalive(self):
        return self._cmd(KEEPALIVE)

    def set_status(self, temp_c: float, pump_rpm: int | None, fan_rpm: int | None) -> bool:
        temp_c = max(TEMP_MIN, min(TEMP_MAX, temp_c))
        raw = int(round(temp_c * 10))
        pkt = bytearray((0x01, REG_TEMP, raw >> 8, raw & 0xFF))
        if pump_rpm is not None:
            p = max(0, min(RPM_MAX, int(pump_rpm)))
            pkt += bytes((p >> 8, p & 0xFF))
            if fan_rpm is not None:
                f = max(0, min(RPM_MAX, int(fan_rpm)))
                pkt += bytes((f >> 8, f & 0xFF))
        resp = self._cmd(bytes(pkt))
        return bytes([ACK_WRITE]) in resp


def read_cpu_cores_avg() -> float | None:
    valores = []
    for hwmon in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        try:
            with open(os.path.join(hwmon, "name")) as f:
                name = f.read().strip()
        except OSError:
            continue
        if name not in ("coretemp", "k10temp", "zenpower"):
            continue
        for cand in sorted(glob.glob(os.path.join(hwmon, "temp*_input"))):
            try:
                with open(cand.replace("_input", "_label")) as f:
                    label = f.read().strip().lower()
            except OSError:
                continue
            if not (label.startswith("core") or label.startswith("tccd")):
                continue
            try:
                with open(cand) as f:
                    valores.append(int(f.read().strip()) / 1000.0)
            except (OSError, ValueError):
                continue
    return sum(valores) / len(valores) if valores else None


def read_first_fan_rpm() -> int | None:
    for hwmon in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        for fan_input in sorted(glob.glob(os.path.join(hwmon, "fan*_input"))):
            try:
                with open(fan_input) as f:
                    rpm = int(f.read().strip())
                    if rpm > 0:
                        return rpm
            except (OSError, ValueError):
                continue
    return None


# ==============================================================================
# INTERFACE GRÁFICA (GUI - TKINTER)
# ==============================================================================
class WaterCoolerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Super Monitor")
        self.geometry("360x390")
        self.resizable(False, False)
        self.configure(bg="#0a0a0a")

        # Seleção de fonte digital estilo 7 segmentos
        self.digital_font_family = self.get_digital_font()

        # Canvas principal para renderizar o design customizado
        self.canvas = tk.Canvas(self, width=360, height=350, bg="#0a0a0a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=False)

        self.draw_static_design()

        # Elementos dinâmicos numéricos (Usando a fonte de 7 segmentos)
        font_digits_sm = (self.digital_font_family, 16, "bold")
        font_digits_lg = (self.digital_font_family, 36, "bold")

        self.fan_text = self.canvas.create_text(131, 146, text="0000", fill="#FFFFFF", font=font_digits_sm)
        self.pump_text = self.canvas.create_text(231, 146, text="0000", fill="#FFFFFF", font=font_digits_sm)
        self.temp_text = self.canvas.create_text(175, 263, text="00.0", fill="#FFFFFF", font=font_digits_lg)
        self.status_text = self.canvas.create_text(180, 335, text="Iniciando...", fill="#555555", font=("Arial", 8))

        # Painel inferior de botões
        self.bottom_frame = Frame(self, bg="#0a0a0a")
        self.bottom_frame.pack(fill="x", side="bottom", pady=5)

        self.btn_about = Button(
            self.bottom_frame, text="Sobre / Doação", command=self.open_about_window,
            bg="#1e1e1e", fg="#00FF7F", activebackground="#2a2a2a", activeforeground="#00FF7F",
            relief="flat", font=("Arial", 9, "bold"), cursor="hand2", padx=10, pady=2
        )
        self.btn_about.pack()

        # Referência da janela Sobre (evita abrir múltiplas)
        self.about_window = None

        # Controle de Thread e Hardware
        self.running = True
        self.wc = None
        self.monitor_thread = threading.Thread(target=self.bg_monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_digital_font(self) -> str:
        """Verifica se há fontes estilo 7 segmentos instaladas no sistema."""
        available_fonts = set(tkfont.families(self))
        preferred_fonts = ["Digital-7", "DSEG7 Classic", "VT323", "Courier New", "FreeMono"]
        for f in preferred_fonts:
            if f in available_fonts:
                return f
        return "Courier"

    def get_temp_color(self, temp: float) -> str:
        """Retorna uma cor de acordo com o valor da temperatura da CPU."""
        if temp < 40.0:
            return "#00BFFF"  # Azul claro / Frio
        elif temp < 60.0:
            return "#00FF7F"  # Verde / Normal
        elif temp < 70.0:
            return "#FFD700"  # Amarelo / Quente
        else:
            return "#FF3333"  # Vermelho / Crítico

    def draw_static_design(self):
        """Desenha na tela o layout vetorial do painel com fundo estático e elementos dinâmicos."""
        # Anéis externos
        self.canvas.create_oval(20, 20, 340, 340, outline="#ffffff", width=3)
        self.canvas.create_oval(30, 30, 330, 330, outline="#222222", width=1)

        # Fundo estático escuro para os HUDs laterais
        self.canvas.create_arc(32, 32, 328, 328, start=140, extent=80, outline="#222222", width=16, style="arc")
        self.canvas.create_arc(32, 32, 328, 328, start=-40, extent=80, outline="#222222", width=16, style="arc")

        # HUD Esquerdo (FAN SPEED) - Arco Dinâmico
        self.fan_arc = self.canvas.create_arc(32, 32, 328, 328, start=220, extent=0, outline="#00BFFF", width=16, style="arc")

        # HUD Direito (PUMP SPEED) - Arco Dinâmico
        self.pump_arc = self.canvas.create_arc(32, 32, 328, 328, start=-40, extent=0, outline="#00FF7F", width=16, style="arc")

        # Logo do Monitor
        self.canvas.create_text(180, 60, text="SUPER MONITOR", fill="#FFFFFF", font=("Arial", 16, "italic bold"))

        # Círculo FAN SPEED (Esquerda)
        self.canvas.create_oval(90, 105, 170, 185, outline="#ffffff", width=2)
        self.canvas.create_text(130, 120, text="FAN", fill="#FFFFFF", font=("Arial", 8, "bold"))
        self.canvas.create_text(130, 170, text="RPM", fill="#FFFFFF", font=("Arial", 8, "bold"))

        # Círculo PUMP SPEED (Direita)
        self.canvas.create_oval(190, 105, 270, 185, outline="#ffffff", width=2)
        self.canvas.create_text(231, 120, text="PUMP", fill="#FFFFFF", font=("Arial", 8, "bold"))
        self.canvas.create_text(232, 170, text="RPM", fill="#FFFFFF", font=("Arial", 8, "bold"))

        # Círculo inferior CPU TEMP - Fundo estático
        self.canvas.create_arc(95, 205, 265, 325, start=0, extent=180, outline="#222222", width=6, style="arc")

        # Círculo inferior CPU TEMP - Arco Dinâmico
        self.temp_arc = self.canvas.create_arc(95, 205, 265, 325, start=180, extent=0, outline="#00BFFF", width=6, style="arc")

        self.canvas.create_text(245, 255, text="°C", fill="#FFFFFF", font=("Arial", 11, "bold"))
        self.canvas.create_text(180, 310, text="CPU TEMP", fill="#FFFFFF", font=("Arial", 11, "bold"))

    def update_gui(self, temp: float, fan: int, pump: int, status_msg: str):
        """Atualiza com segurança os elementos de texto e arcos dinâmicos na interface."""
        # 1. Atualização dos textos
        self.canvas.itemconfig(self.fan_text, text=f"{fan:04d}")
        self.canvas.itemconfig(self.pump_text, text=f"{pump:04d}")
        self.canvas.itemconfig(self.temp_text, text=f"{temp:04.1f}")
        self.canvas.itemconfig(self.status_text, text=status_msg)

        # 2. Atualização do Arco Dinâmico da Temperatura da CPU
        temp_clamped = max(0.0, min(100.0, temp))
        temp_extent = -(temp_clamped / 100.0) * 180.0  # Mapeia 0-100ºC para 0 a -180 graus
        temp_color = self.get_temp_color(temp_clamped)

        self.canvas.itemconfig(self.temp_arc, extent=temp_extent, outline=temp_color)

        # 3. Atualização do Arco Dinâmico FAN SPEED (HUD Esquerdo)
        fan_ratio = max(0.0, min(1.0, fan / FAN_MAX_GAUGE))
        fan_extent = -fan_ratio * 80.0  # Mapeia 0-100% para 0 a -80 graus
        self.canvas.itemconfig(self.fan_arc, extent=fan_extent)

        # 4. Atualização do Arco Dinâmico PUMP SPEED (HUD Direito)
        pump_ratio = max(0.0, min(1.0, (pump - PUMP_MIN) / (PUMP_MAX - PUMP_MIN))) if pump >= PUMP_MIN else 0.0
        pump_extent = pump_ratio * 460.0  # Mapeia 0-100% para 0 a 80 graus
        self.canvas.itemconfig(self.pump_arc, extent=pump_extent)

    def open_about_window(self):
        """Abre a segunda janela 'Sobre' com o resumo do projeto e a chave/QR Code de doação."""
        if self.about_window is not None and self.about_window.winfo_exists():
            self.about_window.lift()
            return

        self.about_window = Toplevel(self)
        self.about_window.title("Sobre o Projeto")
        self.about_window.geometry("380x600")
        self.about_window.resizable(False, False)
        self.about_window.configure(bg="#121212")

        # Torna a janela um modal em relação à principal
        self.about_window.transient(self)

        # Título da Janela
        lbl_title = Label(
            self.about_window, text="SUPER MONITOR",
            font=("Arial", 16, "bold"), fg="#00FF7F", bg="#121212"
        )
        lbl_title.pack(pady=(15, 5))

        lbl_subtitle = Label(
            self.about_window, text="Sistema de Monitoramento para Water Cooler",
            font=("Arial", 9, "italic"), fg="#AAAAAA", bg="#121212"
        )
        lbl_subtitle.pack(pady=(0, 10))

        # Texto Resumo do Projeto
        summary_text = (
            "O Super Monitor é um utilitário desenvolvido para ler em tempo real "
            "a temperatura média dos núcleos do processador e as velocidades de ventoinha (Fan Speed).\n\n"
            "Através do barramento Serial USB (controladores CH340/CH341), ele envia e sincroniza "
            "as estatísticas do sistema com o display do Water Cooler e calcula dinamicamente "
            "a rotação ideal da bomba (Pump Speed)."
        )

        lbl_summary = Label(
            self.about_window, text=summary_text,
            font=("Arial", 9), fg="#DDDDDD", bg="#121212",
            justify="left", wraplength=340
        )
        lbl_summary.pack(padx=20, pady=5)

        # Divisória
        canvas_div = tk.Canvas(self.about_window, width=340, height=2, bg="#121212", highlightthickness=0)
        canvas_div.create_line(0, 1, 340, 1, fill="#333333")
        canvas_div.pack(pady=10)

        # Seção de Apoio / Doação
        lbl_donate_title = Label(
            self.about_window, text="Apoie o Desenvolvimento",
            font=("Arial", 11, "bold"), fg="#00BFFF", bg="#121212"
        )
        lbl_donate_title.pack(pady=(0, 2))

        lbl_donate_desc = Label(
            self.about_window, text="Se este projeto foi útil para você, considere fazer uma doação voluntária via Pix!",
            font=("Arial", 8), fg="#AAAAAA", bg="#121212", wraplength=340
        )
        lbl_donate_desc.pack(pady=(0, 10))

        # Exibição da Imagem do QR Code de Doação
        img_loaded = False
        img_path = DONATION_IMAGE_FILENAME

        if os.path.exists(img_path):
            try:
                if HAS_PIL:
                    pil_img = Image.open(img_path)
                    # Redimensiona mantendo a proporção para caber na janela
                    pil_img.thumbnail((220, 260))
                    self.donate_img = ImageTk.PhotoImage(pil_img)
                else:
                    self.donate_img = tk.PhotoImage(file=img_path)

                img_label = Label(self.about_window, image=self.donate_img, bg="#121212")
                img_label.pack(pady=5)
                img_loaded = True
            except Exception as e:
                print(f"Erro ao carregar a imagem do QR Code: {e}")

        if not img_loaded:
            # Fallback caso a imagem não seja encontrada na pasta
            lbl_fallback = Label(
                self.about_window,
                text="[ Imagem QR Code Pix ]\n(Coloque a imagem 'image.png' na mesma pasta do script)",
                font=("Arial", 8, "italic"), fg="#888888", bg="#1e1e1e",
                padx=20, pady=20, relief="groove"
            )
            lbl_fallback.pack(pady=10)

        # Botão Fechar
        btn_close = Button(
            self.about_window, text="Fechar", command=self.about_window.destroy,
            bg="#2a2a2a", fg="#FFFFFF", activebackground="#3a3a3a", activeforeground="#FFFFFF",
            relief="flat", font=("Arial", 9, "bold"), padx=15, pady=3, cursor="hand2"
        )
        btn_close.pack(pady=(10, 15))

    def bg_monitor_loop(self):
        """Loop de fundo para ler sensores e sincronizar a porta serial."""
        self.wc = WaterCooler()
        try:
            self.wc.open()
        except Exception:
            pass

        last_keepalive = time.monotonic()

        while self.running:
            # 1. Lê a Temperatura da CPU
            temp = read_cpu_cores_avg()
            if temp is None:
                temp = 0.0

            # 2. Lê o Fan Speed e calcula o Pump Speed dinâmico
            fan = read_first_fan_rpm()
            if fan is None:
                fan = 0
                pump = 0
            else:
                pump = pump_from_fan(fan)

            # 3. Atualiza o Hardware do Watercooler via Serial USB
            ack = False
            if self.wc and self.wc._ser and self.wc._ser.is_open:
                ack = self.wc.set_status(temp, pump, fan)

                # Mantém a tela acesa
                if time.monotonic() - last_keepalive >= KEEPALIVE_INTERVAL:
                    self.wc.keepalive()
                    last_keepalive = time.monotonic()

            port_desc = self.wc.port if (self.wc and self.wc.port) else "Sem porta"
            status_txt = f"Serial ({port_desc}): {'ACK OK' if ack else 'Buscando dispositivo...'}"

            # 4. Atualiza a interface do PC
            self.after(0, self.update_gui, temp, fan, pump, status_txt)

            time.sleep(1.5)

    def on_close(self):
        self.running = False
        if self.wc:
            self.wc.close()
        self.destroy()


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    app = WaterCoolerApp()
    app.mainloop()
