const dgram = require('dgram');

// Porta padrão do protocolo XM / NetSDK
const PORT = 34567;
const BROADCAST_ADDR = '255.255.255.255';

const socket = dgram.createSocket('udp4');

console.log('📡 XMeye/NetSDK Discovery Tool (Imitando NVR)');
console.log('---------------------------------------------');

socket.on('error', (err) => {
    console.error(`❌ Erro no socket: ${err.stack}`);
    socket.close();
});

socket.on('message', (msg, rinfo) => {
    console.log(`\n📬 Resposta recebida de ${rinfo.address}:${rinfo.port}`);

    // O protocolo XM tem um header binário de 20 bytes antes do JSON
    // Vamos tentar extrair o JSON ignorando o header
    try {
        // Geralmente o JSON começa com '{'
        const str = msg.toString();
        const jsonStartIndex = str.indexOf('{');

        if (jsonStartIndex !== -1) {
            const jsonStr = str.substring(jsonStartIndex);
            const data = JSON.parse(jsonStr);

            console.log("✅ CÂMERA DETECTADA (Dados Nativos):");
            console.log(JSON.stringify(data, null, 2));

            // Extrair dados cruciais
            if (data.NetWork && data.NetWork.IP) {
                console.log(`\n🎯 ALVO CONFIRMADO:`);
                console.log(`   IP: ${data.NetWork.IP}`);
                console.log(`   MAC: ${data.NetWork.Mac}`);
                console.log(`   Serial (Cloud ID): ${data.NetWork.Sn || "N/A"}`);
                console.log(`   Versão: ${data.NetWork.Ver || "N/A"}`);

                // Dica baseada no protocolo
                console.log(`\n💡 DICA PARA CONEXÃO:`);
                console.log(`   Se funciona no NVR, tente usar este Serial Number.`);
            }
        } else {
            console.log("⚠️ Resposta recebida, mas não achei JSON válido (Pode ser binário puro).");
            console.log("Hex Dump:", msg.toString('hex').substring(0, 100) + "...");
        }
    } catch (e) {
        console.log("❌ Erro ao parsear resposta:", e.message);
    }
});

socket.on('listening', () => {
    const address = socket.address();
    console.log(`🔭 Escutando respostas em ${address.address}:${address.port}...`);

    // ENVIAR O PACOTE MÁGICO DO NVR
    // Estrutura simplificada do comando OP_SEARCH (imitação do python-dvr)
    // Header + Payload JSON

    const payload = JSON.stringify({
        "Name": "OPSearch",
        "OPMonitor": {
            "Action": "Search"
        }
    });

    // Construção do Header NetSDK (20 bytes)
    // 0-3: Head (0xff000000)
    // 4-7: Version
    // 8-11: Session
    // 12-15: MsgId (0x05f2 = 1522 para Search)
    // 16-19: Length (Tamanho do JSON)

    const head = Buffer.from([0xff, 0x00, 0x00, 0x00]);
    const version = Buffer.alloc(4);
    const session = Buffer.alloc(4);
    const msgId = Buffer.from([0xf2, 0x05, 0x00, 0x00]); // 1522 Little Endian
    const length = Buffer.alloc(4);
    length.writeUInt32LE(payload.length);
    const reserved = Buffer.alloc(4); // Às vezes tem mais 4 bytes

    const packet = Buffer.concat([head, version, session, msgId, length, reserved, Buffer.from(payload)]);

    socket.setBroadcast(true);

    console.log("🚀 Enviando Broadcast na porta 34567...");
    socket.send(packet, 0, packet.length, PORT, BROADCAST_ADDR, (err) => {
        if (err) console.error("Erro no envio:", err);
        else console.log("   Pacote enviado! Aguardando câmeras...");
    });
});

socket.bind(); // Porta aleatória local
