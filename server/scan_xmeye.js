const dgram = require('dgram');
const socket = dgram.createSocket('udp4');

console.log("📡 Escutando broadcasts XMeye/ICSEE...");

socket.on('message', (msg, rinfo) => {
    try {
        const message = msg.toString();
        // Mensagens de broadcast da XMeye geralmente contêm JSON
        if (message.includes('{') && message.includes('Ret')) {
            console.log(`\n🎯 DETECTADO!`);
            console.log(`IP: ${rinfo.address}`);
            console.log(`Dados: ${message.substring(0, 100)}...`); // Mostra o começo para confirmar
        }
    } catch (e) {
        // ignorar lixo
    }
});

socket.on('listening', () => {
    const address = socket.address();
    console.log(`Escutando na porta ${address.port} ou Enviando probe...`);

    // Além de ouvir, vamos enviar uma provocação (Discovery Probe)
    // Esse é o "Hey!" mágico que faz as câmeras XMeye responderem
    const probe = Buffer.from(JSON.stringify({
        "Cmd": "DeviceFind",
        "Action": "Find"
    }));

    socket.setBroadcast(true);

    // Envia para a rede toda na porta 34569 (Padrão XMeye Discovery)
    setInterval(() => {
        console.log('Enviando ping de descoberta...');
        socket.send(probe, 0, probe.length, 34569, '255.255.255.255');
    }, 2000); // Tenta a cada 2 segundos
});

socket.bind(0); // Bind em porta aleatória para enviar
