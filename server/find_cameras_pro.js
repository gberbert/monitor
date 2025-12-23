const { exec } = require('child_process');
const net = require('net');

console.log("\n🕵️  INICIANDO CAÇADA PRO (Busca por Portas XMeye 34567)...\n");

// 1. Obter lista de IPs via ARP
exec('arp -a', async (err, stdout, stderr) => {
    if (err) {
        console.error("Erro ao rodar ARP:", err);
        return;
    }

    const ips = [];
    const lines = stdout.split('\n');
    lines.forEach(line => {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 2) {
            const ip = parts[0];
            // Filtra IPs locais
            if (ip.match(/192\.168\.\d+\.\d+/) && !ip.endsWith('.1') && !ip.endsWith('.255')) {
                ips.push(ip);
            }
        }
    });

    console.log(`📡 Analisando ${ips.length} dispositivos da rede...\n`);

    const cameras = [];

    // 2. Verificar porta 34567 (Assinatura XMeye) em cada IP
    for (const ip of ips) {
        const isCamera = await checkPort(34567, ip);
        const isRTSP = await checkPort(554, ip);
        const isOnvif = await checkPort(8899, ip);
        const isWeb = await checkPort(80, ip);

        process.stdout.write(`Scanning ${ip}... `);

        if (isCamera) {
            console.log(`🚨  BINGO! Porta 34567 ABERTA! (É Câmera XMeye)`);
            cameras.push({ ip, type: 'XMeye (ICSEE)', port: 34567 });
        } else if (isRTSP) {
            console.log(`✅  Porta 554 Aberta (Possível Câmera Genérica)`);
            cameras.push({ ip, type: 'Genérica RTSP', port: 554 });
        } else if (isOnvif) {
            console.log(`✅  Porta 8899 Aberta (Possível Câmera ONVIF)`);
            cameras.push({ ip, type: 'ONVIF', port: 8899 });
        } else {
            // Ignora silenciosamente
        }
    }

    console.log("\n------------------------------------------------");
    console.log(`🎉  RESULTADO FINAL: ${cameras.length} Câmeras Encontradas`);
    console.log("------------------------------------------------");
    cameras.forEach(cam => {
        console.log(`📹  IP: ${cam.ip}  |  Tipo: ${cam.type}`);
    });
    console.log("------------------------------------------------\n");
    console.log("👉 Use APENAS estes IPs para tentar conectar.");
});

function checkPort(port, host) {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(1000); // 1 segundo timeout (rápido)

        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });

        socket.on('timeout', () => {
            socket.destroy();
            resolve(false);
        });

        socket.on('error', () => {
            // Ignora erros
            resolve(false);
        });

        socket.connect(port, host);
    });
}
