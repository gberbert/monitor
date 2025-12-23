# Estudo de Viabilidade: Acesso Remoto via Web App (Estilo TeamViewer)

## 1. Resumo Executivo
**STATUS: PROVA DE CONCEITO BEM SUCEDIDA (22/12/2025)**

Conseguimos estabelecer o acesso remoto de vídeo em tempo real (sub-segundo) para dispositivos móveis via 4G, contornando as limitações de codec (H.265) e rede (Portas fechadas).

## 2. Solução Técnica Validada

### A. Core de Vídeo (Go2RTC + FFmpeg)
*   **Desafio**: As câmeras Dahua/XMeye usam codec **H.265** (HEVC). Navegadores (Chrome/Edge/Safari) não reproduzem isso nativamente via WebRTC.
*   **Solução**: Implementamos **Transcodificação em Tempo Real**.
    *   O `ffmpeg.exe` roda no servidor local.
    *   Converte o fluxo H.265 para **H.264** instantaneamente.
    *   Entrega para o navegador via WebRTC.
*   **Resultado**: Vídeo fluido, alta qualidade, funciona em qualquer celular ou PC.

### B. Acesso Externo (Tunneling)
*   **Ferramenta**: Cloudflare Tunnel (`cloudflared`).
*   **Resultado**: Criou um link HTTPS público (`https://....trycloudflare.com`) que aponta direto para o nosso servidor local (Porta 1984).
*   **Segurança**: Sem portas abertas no roteador. Tráfego criptografado.

## 3. Próximos Passos (Roteiro de Produto)

Agora que a tecnologia base está validada, podemos construir o produto final:

### Fase 1: Infraestrutura (Atual)
- [x] Rodar Go2RTC com FFmpeg.
- [x] Testar Transcodificação H.264.
- [x] Acesso Externo via Link Temporário.

### Fase 2: Interface "Web VMS" (Próxima)
- [ ] Criar um **Servidor Web Python** (Flask/FastAPI) dedicado.
- [ ] Implementar **Tela de Login** (Segurança para não deixar suas câmeras abertas).
- [ ] Criar **Dashboard (Grid)** que lê automaticamente o `cameras.db`.
- [ ] Permitir clicar na câmera para abrir em tela cheia (usando o player H.264 que criamos).

### Fase 3: Produção
- [ ] Configurar tunnel fixo (para o link não mudar toda hora).
- [ ] Colocar tudo para iniciar com o Windows (Serviço).

---
**Conclusão**: O projeto é 100% viável e a parte mais difícil (transmissão de vídeo compatível na web) está resolvida.
