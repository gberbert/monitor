const onvif = require('node-onvif');

const CONFIG = {
    ip: '192.168.3.14', // O IP que achamos
    port: 8899,         // Porta ONVIF detectada
    user: 'admin'
};

const PASSWORDS = ['', '123456', 'admin', '888888'];

console.log(`\n📡 SONDAGEM ONVIF - Descobrindo URL Real da Câmera...`);
console.log(`   Alvo: http://${CONFIG.ip}:${CONFIG.port}/onvif/device_service\n`);

async function probe() {
    for (const pass of PASSWORDS) {
        console.log(`🔑 Testando senha: "${pass}"...`);

        try {
            const device = new onvif.OnvifDevice({
                xaddr: `http://${CONFIG.ip}:${CONFIG.port}/onvif/device_service`,
                user: CONFIG.user,
                pass: pass
            });

            // Tenta inicializar (Autenticação acontece aqui)
            const info = await device.init();

            console.log(`\n✅ SUCESSO! Conectado via ONVIF!`);
            console.log(`   Fabricante: ${info.Manufacturer}`);
            console.log(`   Modelo: ${info.Model}`);
            console.log(`   Firmware: ${info.FirmwareVersion}\n`);

            // Obter URL de Vídeo
            const url = device.getUdpStreamUrl();
            console.log(`📹 URL DESCOBERTA: ${url}`);
            console.log(`---------------------------------------------------`);
            console.log(`👉 Tente adicionar manualmente no site com essa URL SE tiver o formato rtsp://`);
            console.log(`   Caso contrário, a câmera confirmou que o IP e Senha estão certos.`);
            return;

        } catch (error) {
            if (error.message.includes('401') || error.message.includes('Authorized')) {
                console.log(`   ❌ Senha incorreta.`);
            } else {
                console.log(`   ❌ Erro de conexão: ${error.message}`);
                // Se der erro de conexão (não auth), provavel que porta 8899 não seja a certa ou device offline
                // Mas como vimos 8899 aberta, deve ser auth.
            }
        }
    }

    console.log(`\n❌ FIM. Nenhuma senha padrão funcionou.`);
    console.log(`⚠️  Se você definiu uma senha diferente, edite este arquivo e adicione ela na lista PASSWORDS.`);
}

probe();
