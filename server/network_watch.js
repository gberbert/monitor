const { exec } = require('child_process');
const { networkInterfaces } = require('os');

// Configuração
const CHECK_INTERVAL = 3000; // Verificar a cada 3 segundos

// Estado
let knownDevices = new Map(); // IP -> Status (true=online, false=offline)
let isFirstRun = true;

// Descobrir sub-rede automaticamente
function getSubnet() {
    const nets = networkInterfaces();
    for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
            if (net.family === 'IPv4' && !net.internal) {
                const parts = net.address.split('.');
                parts.pop();
                return parts.join('.');
            }
        }
    }
    return '192.168.3'; // Fallback baseado no seu histórico
}

// Função Ping (Promise wrapper)
function ping(ip) {
    return new Promise((resolve) => {
        // Ping Windows: -n 1 (uma vez), -w 500 (timeout 500ms)
        exec(`ping -n 1 -w 500 ${ip}`, (err, stdout) => {
            // Se encontrar "TTL=" na resposta, está vivo
            const isAlive = stdout.includes('TTL=') || stdout.includes('ttl=');
            resolve(isAlive);
        });
    });
}

async function scan() {
    const subnet = getSubnet();
    if (isFirstRun) {
        console.log(`\n📡 Monitor de Rede Iniciado na sub-rede ${subnet}.x`);
        console.log(`------------------------------------------------`);
        console.log(`1. Mantenha as câmeras LIGADAS e aguarde a lista inicial.`);
        console.log(`2. Depois que estabilizar, DESLIGUE uma câmera.`);
        console.log(`3. O script vai avisar qual IP caiu.`);
        console.log(`------------------------------------------------\n`);
    }

    // Varredura de IPs (focada nos que já responderam ou faixa comum)
    // Para ser rápido, vamos focar nos IPs que você já viu no ARP e arredores
    // Mas para garantir, vamos varrer 1..254 paralelamente em blocos

    // Lista de Promises
    const checks = [];
    for (let i = 1; i < 255; i++) {
        checks.push((async () => {
            const ip = `${subnet}.${i}`;
            const isOnline = await ping(ip);
            return { ip, isOnline };
        })());
    }

    const results = await Promise.all(checks);

    // Processar resultados
    let changes = false;
    results.forEach(({ ip, isOnline }) => {
        const wasOnline = knownDevices.get(ip) || false;

        if (isOnline && !wasOnline) {
            // Entrou (ou primeira execução)
            if (!isFirstRun) console.log(`🟢 NOVO DISPOSITIVO ONLINE: ${ip}`);
            knownDevices.set(ip, true);
            changes = true;
        } else if (!isOnline && wasOnline) {
            // Saiu!
            console.log(`🔴 DISPOSITIVO FICOU OFFLINE: ${ip} (Pode ser a câmera!)`);
            knownDevices.set(ip, false);
            changes = true;
        }
    });

    if (isFirstRun) {
        console.log("Dispositivos atualmente online:");
        let count = 0;
        knownDevices.forEach((status, ip) => {
            if (status) {
                console.log(` - ${ip}`);
                count++;
            }
        });
        console.log(`Total: ${count} dispositivos.\n`);
        console.log("👀 Monitorando alterações... (desligue a câmera agora)");
        isFirstRun = false;
    }

    // Agenda próximo loop
    setTimeout(scan, CHECK_INTERVAL);
}

// Iniciar
scan();
