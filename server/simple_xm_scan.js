const dgram = require('dgram');

// Configurações do Protocolo XM
const PORT = 34567;
const BROADCAST_ADDR = '255.255.255.255';
const MSG = Buffer.from(JSON.stringify({
    "Name": "Search",
    "Config": "All"
}));

const socket = dgram.createSocket('udp4');

console.log('📡 XMeye Radar (Simulando NVR)...');

socket.on('error', (err) => {
    console.log(`❌ Erro: ${err.stack}`);
    socket.close();
});

socket.on('message', (msg, rinfo) => {
    console.log(`\n📬 RESPOSTA RECEBIDA DE ${rinfo.address}:`);
    console.log('------------------------------------------------');
    try {
        const data = JSON.parse(msg.toString());
        console.log(JSON.stringify(data, null, 2));

        // Analisar resposta para ajudar o usuário
        if (data.NetWork && data.NetWork.IP) {
            const ip = data.NetWork.IP;
            const sn = data.NetWork.Sn; // Serial Number é a chave de tudo!

            console.log(`\n✅ ALVO IDENTIFICADO!`);
            console.log(`   IP: ${ip}`);
            console.log(`   Serial: ${sn}`);
            console.log(`   MAC: ${data.NetWork.Mac}`);

            // Sugestão de URL baseada na pesquisa do Gemini
            console.log(`\n🔗 Tente esta URL RTSP (Padrão XM):`);
            console.log(`   rtsp://${ip}:554/user=admin&password=&channel=1&stream=0.sdp`);
            console.log(`   (Nota: Se tiver senha, coloque depois de password=)`);
        }
    } catch (e) {
        console.log(`⚠️ Resposta não-JSON: ${msg.toString()}`);
    }
});

socket.on('listening', () => {
    const address = socket.address();
    socket.setBroadcast(true);
    console.log(`🚀 Enviando Broadcast para ${BROADCAST_ADDR}:${PORT}...`);

    // Envia 3 vezes para garantir (UDP pode perder pacotes)
    socket.send(MSG, PORT, BROADCAST_ADDR);
    setTimeout(() => socket.send(MSG, PORT, BROADCAST_ADDR), 500);
    setTimeout(() => socket.send(MSG, PORT, BROADCAST_ADDR), 1000);
});

socket.bind(); // Porta aleatória para escutar a resposta
