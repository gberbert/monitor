import json

# Config
IP = "192.168.3.27"
USER = "admin" # Tentar admin primeiro, ou berbert
PASS = "viguera2001" # Tentar a senha fornecida

# Se import falhar, tenta via mocks (nao, vamos assumir que não funciona o import direto e usar submodulos se precisar)
# Mas o usuario conseguiu instalar dvrip.
# O erro anterior foi "ImportError: cannot import name 'DVRIPCam'".
# Vamos tentar consertar o import baseado na estrutura que vimos.
# Vimos que dvrip tem submodulos. Mas nao vimos a classe Cam.
# Talvez tenhamos que implementar a classe Cam "na unha" usando login.ClientLogin e monitor.DoMonitor...
# Isso é complexo.

# Vamos tentar uma abordagem Socket Puro NETIP (SOFIA) Baseado em exemplos open source.
# O protocolo é simples o suficiente para um script "hardcoded" de troca de codec.
#
# Estrutura do Pacote SOFIA:
# HEAD (0xFF000000) + SESSION_ID + SEQ + TOTAL_LEN + CUR_LEN + MSG_ID + 0x00 + RESERVED
# Login ID: 1000
# Config ID: 1042 (AVEnc)

import socket
import struct
import time

def make_packet(msg_id, session_id, seq, data_json):
    head_magic = 0xff
    ver = 1 # ? 
    # Packet struct:
    # head(1), ver(1), res(2), session(4), seq(4), total_len(4), cur_len(4), msg_id(2), res(1), enc(1)
    # Total 24 bytes? 
    # Documentação varia. Vamos usar o padrão "Sofia" comum.
    # 0xFF + 0x01 + 0x0000 + Session(4) + Seq(4) + Len(4) + Len(4) + MsgID(2) + ...
    
    # Simplificação: Vamos usar a string connection do dvrip se funcionar.
    pass

print("--- DIAGNOSTICO NETIP / DVRIP ---")
# Como dvrip falhou no import, vamos usar a ferramenta de linha de comando 'dvr.exe' via subprocess
# para tentar pegar info. É o jeito mais seguro sem reinventar a roda.

import subprocess
import sys

# O executavel dvr fica em .../Scripts/dvr.exe.
# Como nao sabemos o path exato (User Install), vamos tentar 'python -m dvrip'

def run_dvr_cmd(cmd_list):
    full_cmd = [sys.executable, "-m", "dvrip", "-u", "berbert", "-p", "viguera2001", "-h", "192.168.3.27"] + cmd_list
    print(f"Executando: {' '.join(full_cmd)}")
    try:
        res = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        return res.stdout
    except Exception as e:
        print(f"ERRO: {e}")
        return ""

print("1. Tentando INFO...")
info = run_dvr_cmd(["info"])

if "H.265" in info or "HEVC" in info:
    print("ALERTA: Câmera confirmada como H.265!")

print("\n2. Tentando listar encoders (se suportado)...")
# O CLI do dvrip é limitado (cat, find, info...). Não tem 'get_config'.
# Então não podemos mudar o codec via CLI.

print("--- TESTE RTSP NATIVO (OPENCV) DE NOVO ---")
# Vamos tentar só confirmar se o channel 1 stream 1 abre com TCP forçado no codigo
import cv2
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
url = "rtsp://berbert:viguera2001@192.168.3.27:34567/user=berbert&password=viguera2001&channel=1&stream=1.sdp"
print(f"Abrindo: {url}")
cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
if cap.isOpened():
    print("Sucesso! Frame lido?")
    ret, frame = cap.read()
    print(f"Ret: {ret}")
else:
    print("Falha ao abrir.")
cap.release()
