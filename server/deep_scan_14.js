const net = require('net');

const TARGET_IP = '192.168.3.14';
const PORTS_TO_CHECK = [
    80,    // Web HTTP
    554,   // RTSP (Vídeo Padrão)
    8899,  // ONVIF
    34567, // XMeye / NETIP (Configuração + Vídeo Proprietário)
    8000,  // Porta Alternativa comum
    8080,  // Web Alternativa
    5000,  // UPnP ou Stream
    37777, // Dahua Alternativa
    1935   // RTMP
];

console.log(`\n🏥 DIAGNÓSTICO PROFUNDO EM ${TARGET_IP}\n`);

async function scan() {
    for (const port of PORTS_TO_CHECK) {
        process.stdout.write(`Checando porta ${port}... `);
        const isOpen = await checkPort(port, TARGET_IP);
        if (isOpen) {
            console.log(`✅ ABERTA!`);
        } else {
            console.log(`❌ Fechada`);
        }
    }
    console.log("\nCONCLUSÃO:");
}

function checkPort(port, host) {
    return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(2000);

        socket.on('connect', () => {
            socket.destroy();
            resolve(true);
        });

        socket.on('timeout', () => {
            socket.destroy();
            resolve(false);
        });

        socket.on('error', (err) => {
            resolve(false);
        });

        socket.connect(port, host);
    });
}

scan();
