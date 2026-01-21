const ffmpeg = require('fluent-ffmpeg');
const ffmpegPath = require('ffmpeg-static');
const ffprobePath = require('ffprobe-static');

ffmpeg.setFfmpegPath(ffmpegPath);
ffmpeg.setFfprobePath(ffprobePath.path);

// A URL Mágica
const url = 'rtsp://192.168.3.14:554/user=admin_password=tlJwpbo6_channel=0_stream=0&onvif=0.sdp?real_stream';

console.log(`🕵️ Analisando Codec da URL Mágica...\nURI: ${url}`);

ffmpeg(url)
    .inputOptions(['-rtsp_transport tcp', '-stimeout 5000000'])
    .ffprobe((err, data) => {
        if (err) {
            console.error("❌ Falha ao sondar:", err.message);
        } else {
            console.log("✅ Conexão Bem Sucedida! Metadados Recebidos:");
            data.streams.forEach((stream, i) => {
                if (stream.codec_type === 'video') {
                    console.log(`\n📺 STREAM DE VÍDEO ${i}:`);
                    console.log(`   Codec: ${stream.codec_name.toUpperCase()}`); // HEVC = H.265
                    console.log(`   Resolução: ${stream.width}x${stream.height}`);
                    console.log(`   Bitrate: ${stream.bitrate || 'N/A'}`);

                    if (stream.codec_name === 'hevc') {
                        console.log("\n⚠️  ALERTA: Codec HEVC (H.265) detectado!");
                        console.log("   Isso exige MUITA CPU para converter para navegador.");
                        console.log("   É a causa nº 1 de 'Tela Preta' ou travamentos.");
                    }
                }
            });
        }
    });
