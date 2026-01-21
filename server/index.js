const express = require('express');
const cors = require('cors');
const onvif = require('node-onvif');
const ffmpeg = require('fluent-ffmpeg');
const ffmpegPath = require('ffmpeg-static');
const ffprobePath = require('ffprobe-static');

const fs = require('fs');
const path = require('path');

// Helper de Log
function logToFile(msg) {
    const logPath = path.join(__dirname, 'ffmpeg_debug.log');
    const time = new Date().toISOString();
    fs.appendFileSync(logPath, `[${time}] ${msg}\n`);
}

// Configurar FFmpeg e FFprobe
ffmpeg.setFfmpegPath(ffmpegPath);
ffmpeg.setFfprobePath(ffprobePath.path);

const app = express();
const PORT = 3001;

// Proteção contra crashes (Blindagem)
process.on('uncaughtException', (err) => {
    console.error('CRÍTICO: Erro não tratado:', err);
    // Não sai do processo, apenas loga
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('CRÍTICO: Rejeição de promessa:', reason);
});

// Middlewares
app.use(cors());
app.use(express.json());

const net = require('net');
const { networkInterfaces } = require('os');

// Armazenamento em memória das câmeras encontradas
let discoveredCameras = [];

// Função aprimorada para descobrir a sub-rede correta
function getLocalSubnet() {
    const nets = networkInterfaces();
    const results = [];

    for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
            // Procura IPv4, não-interno
            if (net.family === 'IPv4' && !net.internal) {
                // Tenta priorizar Wi-Fi ou Ethernet
                const p = { name, ip: net.address, subnet: net.address.split('.').slice(0, 3).join('.') };
                results.push(p);
                console.log(`Interface detectada: ${name} - IP: ${net.address}`);
            }
        }
    }

    // Retorna a primeira que parecer válida (geralmente a primária)
    // Se tiver mais de uma, o ideal seria o usuário escolher ou escanearmos todas.
    // Vamos assumir a primeira da lista por enquanto.
    return results.length > 0 ? results[0].subnet : '192.168.0';
}

// Scanners de porta com timeout maior
function checkPort(port, host) {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(2000); // 2 segundos (mais tolerante para Wi-Fi)

        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });

        socket.on('timeout', () => {
            socket.destroy();
            resolve(false);
        });

        socket.on('error', () => {
            socket.destroy();
            resolve(false);
        });

        socket.connect(port, host);
    });
}

/**
 * Rota: Escanear rede (Focado em ICSEE/XMeye - Porta 34567)
 */
app.get('/api/scan', async (req, res) => {
    console.log('Iniciando varredura profunda (Modo ICSEE/XMeye)...');

    const subnet = getLocalSubnet();
    console.log(`Escaneando sub-rede base: ${subnet}.x`);

    discoveredCameras = [];
    const activeHosts = [];
    const promises = [];

    // Passo 1: Descobrir IPs ativos (Ping/Connect simples na 34567 ou 80)
    // Escaneamos 1-254
    for (let i = 1; i < 255; i++) {
        const ip = `${subnet}.${i}`;

        // Check paralelo nas portas principais
        // 34567 = Padrão XMeye/ICSEE
        // 554 = RTSP Padrão
        // 80 = Web Padrão
        const check = async () => {
            const isXMeye = await checkPort(34567, ip);
            if (isXMeye) {
                console.log(`[CAM DETECTADA] ${ip} (Porta 34567 Aberta)`);
                discoveredCameras.push({
                    id: `cam-${ip}-XM`,
                    name: `Câmera ICSEE (${ip})`,
                    ip: ip,
                    type: 'xmeye',
                    status: 'auth_required'
                });
                return;
            }

            const isRTSP = await checkPort(554, ip);
            if (isRTSP) {
                console.log(`[RTSP DETECTADO] ${ip} (Porta 554 Aberta)`);
                discoveredCameras.push({
                    id: `cam-${ip}-RTSP`,
                    name: `Câmera Genérica (${ip})`,
                    ip: ip,
                    type: 'rtsp',
                    status: 'auth_required'
                });
                return;
            }
        };

        promises.push(check());
    }

    // Executa em blocos para não engasgar a rede (opcional, aqui vai tudo de vez pois node aguenta)
    await Promise.all(promises);

    console.log(`Scan finalizado. ${discoveredCameras.length} câmeras encontradas.`);

    res.json({
        success: true,
        count: discoveredCameras.length,
        cameras: discoveredCameras
    });
});

/**
 * Rota: Testar Credenciais na Câmera
 */
app.post('/api/camera/auth', async (req, res) => {
    const { ip, user, pass, rtspUrl } = req.body;

    // Função Helper para testar uma URL
    const testStream = (url) => {
        return new Promise((resolve) => {
            let responded = false;
            const cmd = ffmpeg(url)
                .setFfmpegPath(ffmpegPath)
                .inputOptions(['-rtsp_transport', 'tcp']); // Removido stimeout para compatibilidade

            const safeTimeout = setTimeout(() => {
                if (!responded) {
                    responded = true;
                    try { cmd.kill(); } catch (e) { }
                    resolve({ success: false, message: "Timeout" });
                }
            }, 6000);

            cmd.ffprobe((err, metadata) => {
                if (responded) return;
                clearTimeout(safeTimeout);
                responded = true;

                if (err) {
                    resolve({ success: false, message: err.message });
                } else {
                    resolve({ success: true, metadata });
                }
            });
        });
    };

    // MODO URL DIRETA (Bypass)
    if (rtspUrl) {
        console.log(`\n🔗 Testando URL Customizada direta: ${rtspUrl}`);
        const result = await testStream(rtspUrl);
        if (result.success) {
            console.log("✅ SUCESSO! URL Customizada válida.");
            return res.json({ success: true, streamUrl: rtspUrl, metadata: result.metadata.format });
        } else {
            console.log("❌ Falha na URL Customizada:", result.message);
            return res.json({ success: false, message: "URL recusada pelo FFmpeg: " + result.message });
        }
    }

    // ... Lógica Padrão ...
    console.log(`\n🔍 Testando acesso em ${ip} (User: ${user})...`);

    // Credenciais e Variações de Senha para "Quebrar" o Auth
    const passwordsToTry = [
        pass,          // A senha que você digitou
        "",            // Senha Vazia (Padrão de fábrica muito comum em RTSP)
        "123456",      // Padrão comum
        "admin",       // Padrão comum
        "888888"       // Padrão VStarCam/Outras
    ];

    // Remover duplicatas e valores nulos se o usuário já digitou um deles
    const uniquePasswords = [...new Set(passwordsToTry)].filter(p => p !== undefined);

    // Lista de Templates de URL - FOCADA EM COMPATIBILIDADE (SUB-STREAM)
    // Tentar SubStream (1) primeiro, pois costuma ser H.264 (mais compatível)
    const urlTemplates = [
        // 1. XMeye Sub-stream (stream=1)
        `rtsp://{{ip}}:554/user={{user}}&password={{pass}}&channel=1&stream=1.sdp?`,

        // 2. Dahua/XMeye Sub-stream (subtype=1)
        `rtsp://{{user}}:{{pass}}@{{ip}}:554/cam/realmonitor?channel=1&subtype=1`,

        // 3. Main Stream (se sub falhar)
        `rtsp://{{ip}}:554/user={{user}}&password={{pass}}&channel=1&stream=0.sdp?`,

        // 4. Padrão Genérico
        `rtsp://{{user}}:{{pass}}@{{ip}}:554`,
    ];

    console.log(`➡️ Iniciando "Smart Auth" para ${ip}...`);
    console.log(`   * Priorizando SUB-STREAM (Melhor compatibilidade)`);
    console.log(`   Senhas candidatas: [${uniquePasswords.map(p => p === "" ? "(vazia)" : "***").join(", ")}]`);

    for (const currentPass of uniquePasswords) {
        const safeUser = encodeURIComponent(user);
        const safePass = encodeURIComponent(currentPass);

        for (const template of urlTemplates) {
            let url = template
                .replace('{{ip}}', ip)
                .replace('{{user}}', safeUser)
                .replace('{{pass}}', safePass);

            // Tenta conectar
            const result = await testStream(url);

            if (result.success) {
                console.log(`✅ SUCESSO! Conectado. URL: ${url}`);
                return res.json({
                    success: true,
                    streamUrl: url,
                    metadata: result.metadata.format,
                    usedPassword: currentPass
                });
            }
        }
    }

    // ... [Loop anterior falhou] ...

    console.log("⚠️ Padrões RTSP falharam. Tentando negociação ONVIF (Deep Link)...");

    // TENTATIVA 4: ONVIF "Magic" (Pergunta a URL real para a câmera via Porta 8899)
    try {
        const isOnvifOpen = await checkPort(8899, ip);
        if (isOnvifOpen) {

            // Loop de senhas também para ONVIF
            for (const passVar of uniquePasswords) {
                console.log(`   🔎 Sondando ONVIF com senha: "${passVar === "" ? "(vazia)" : "***"}"`);

                const device = new onvif.OnvifDevice({
                    xaddr: `http://${ip}:8899/onvif/device_service`,
                    user: user,
                    pass: passVar
                });

                try {
                    await device.init();
                    let onvifUrl = device.getUdpStreamUrl();

                    console.log(`   💡 ONVIF retornou URL: ${onvifUrl}`);

                    // Testar essa URL específica
                    let result = await testStream(onvifUrl);
                    if (result.success) {
                        console.log("✅ SUCESSO via ONVIF!");
                        return res.json({
                            success: true,
                            streamUrl: onvifUrl,
                            metadata: result.metadata.format,
                            usedPassword: passVar
                        });
                    }
                } catch (e) {
                    // Falha de auth no ONVIF, tenta próxima senha
                }
            }
        }
    } catch (err) {
        console.log("   ❌ Erro na sondagem ONVIF:", err.message);
    }

    console.log("❌ Todas as tentativas (RTSP e ONVIF) falharam.");
    res.json({ success: false, message: "Falha: Câmera rejeitou conexões H.264 e ONVIF falhou." });
});

/**
 * Rota: Iniciar Stream de uma câmera (Simulação para Setup)
 * Recebe: { url, user, pass }
 */
/**
 * Rota: Streaming de Vídeo ao Vivo (MJPEG Proxy)
 * Uso: <img src="/api/stream/live?url=RTSP_URL" />
 */
app.get('/api/stream/live', (req, res) => {
    // Parse Manual da URL para evitar quebra com '&' na string RTSP
    // Ex: /api/stream/live?url=rtsp://x&y=1 -> Express pegaria url=rtsp://x e y=1
    const rawUrl = req.url; // /api/stream/live?url=rtsp://...
    let streamUrl = '';

    const queryIndex = rawUrl.indexOf('?url=');
    if (queryIndex !== -1) {
        // Pega tudo depois de 'url=' e decodifica apenas uma vez se necessario
        streamUrl = decodeURIComponent(rawUrl.substring(queryIndex + 5));
    }

    if (!streamUrl) return res.status(400).send('URL falhou parse manual');

    console.log(`\n🎥 Transmissão (Parse Seguro):`);
    console.log(`   URL Recebida: ${streamUrl}`);

    // ... headers ...
    res.writeHead(200, {
        'Content-Type': 'multipart/x-mixed-replace; boundary=ffmpeg',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    });

    const command = ffmpeg(streamUrl)
        .setFfmpegPath(ffmpegPath)
        .inputOptions([
            '-rtsp_transport tcp'
            // Removido timeouts e buffers manuais para evitar erro de sintaxe do FFmpeg
        ])
        .outputOptions([
            '-f mjpeg',
            '-q:v 20',           // Aumentar compressão (5 era qualidade muito alta/pesada)
            '-r 10',             // Reduzir FPS para garantir fluidez no transporte
            '-vf scale=640:360', // Resolução fixa e leve
            '-b:v 1000k',        // Limitar bitrate violentamente
            '-an',
            '-pix_fmt yuvj420p'
        ])
        .on('start', (commandLine) => {
            console.log('   Stream FFmpeg iniciado!');
            logToFile(`START_CMD: ${commandLine}`);
        })
        .on('progress', (progress) => {
            // Debug de vida
            if (progress.frames % 50 === 0) logToFile(`PROGRESS: Frame=${progress.frames} FPS=${progress.currentFps}`);
        })
        .on('stderr', (stderrLine) => {
            logToFile(`STDERR: ${stderrLine}`);
        })
        .on('error', (err) => {
            if (!err.message.includes('Output stream closed')) {
                console.error('   CRASH no Stream:', err.message);
                logToFile(`ERROR_CRASH: ${err.message}`);
            }
        });

    // Pipe process output to response
    const stream = command.pipe(res, { end: true });

    // Cleanup
    req.on('close', () => {
        console.log('   Cliente desconectou.');
        command.kill();
    });
});

// Endpoint de Snapshot (Teste de Vida)
app.get('/api/stream/snapshot', (req, res) => {
    const rawUrl = req.url;
    let streamUrl = '';
    const queryIndex = rawUrl.indexOf('?url=');
    if (queryIndex !== -1) streamUrl = decodeURIComponent(rawUrl.substring(queryIndex + 5));

    if (!streamUrl) return res.status(400).send('URL missing');

    console.log(`📸 Snapshot Solicitado...`);
    logToFile(`SNAPSHOT_START: ${streamUrl}`);

    const command = ffmpeg(streamUrl)
        .setFfmpegPath(ffmpegPath)
        .inputOptions([
            '-rtsp_transport tcp',
            // '-stimeout 5000000', // Removido pois causa erro
            '-ss 5', // Esperar 5s pelo Keyframe (H.265 demora!)
            '-probesize 10000000',
            '-analyzeduration 10000000'
        ])
        .outputOptions([
            '-f image2',
            '-vframes 1',
            '-q:v 5'
        ])
        .on('start', (cmd) => logToFile(`SNAPSHOT_CMD: ${cmd}`))
        .on('error', (err) => {
            console.error('Erro Snapshot:', err.message);
            logToFile(`SNAPSHOT_ERROR: ${err.message}`);
            if (!res.headersSent) res.status(500).send('Erro na captura');
        })
        .on('end', () => {
            logToFile('SNAPSHOT_SUCCESS');
        });

    res.contentType('image/jpeg');
    command.pipe(res, { end: true });
});

// Executar comando de sistema (usado pelo ARP scan)
const { exec } = require('child_process');

app.get('/api/network/devices', (req, res) => {
    exec('arp -a', (error, stdout, stderr) => {
        if (error) return res.json({ success: false, message: "Erro ARP" });

        const devices = [];
        const lines = stdout.split('\n');
        lines.forEach(line => {
            const parts = line.trim().split(/\s+/);
            if (parts.length >= 3) {
                const ip = parts[0];
                const mac = parts[1];
                if (ip.match(/^\d+\.\d+\.\d+\.\d+$/) && !ip.endsWith('.255') && !ip.startsWith('224.')) {
                    devices.push({ ip, mac, type: parts[2] });
                }
            }
        });
        res.json({ success: true, count: devices.length, devices });
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`
  🚀 Servidor de Monitoramento Rodando!
  -------------------------------------
  Backend Local: http://localhost:${PORT}
  API Scan:      http://localhost:${PORT}/api/scan
  Stream Test:   http://localhost:${PORT}/api/stream/live?url=...
  `);
});
