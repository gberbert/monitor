const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const packageJsonPath = path.join(__dirname, 'package.json');
// Adjusted path to point to client/src/version.ts
const versionFilePath = path.join(__dirname, 'client', 'src', 'version.ts');

// 1. Ler o package.json atual
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const currentVersion = packageJson.version;

// 2. Incrementar a versão (Lógica: Patch 0.0.X)
let versionParts = currentVersion.split('.').map(Number);
versionParts[2] += 1; // Incrementa o último número
const newVersion = versionParts.join('.');

// 3. Atualizar o package.json
packageJson.version = newVersion;
fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 4)); // Using 4 spaces or 2? Original was 2, but 4 is fine. adhering to 4 is safe but I'll stick to 4.

// 4. Criar/Atualizar o arquivo client/src/version.ts para o App ler
// Ensure directory exists just in case
const versionDir = path.dirname(versionFilePath);
if (!fs.existsSync(versionDir)) {
    fs.mkdirSync(versionDir, { recursive: true });
}

const versionFileContent = `export const appVersion = "${newVersion}";\n`;
fs.writeFileSync(versionFilePath, versionFileContent);

console.log(`✅ Versão atualizada: ${currentVersion} -> ${newVersion}`);

// 5. Executar comandos GIT
try {
    console.log('📦 Adicionando arquivos ao Git...');
    execSync('git add .');

    console.log('🔖 Criando commit...');
    execSync(`git commit -m "versão ${newVersion}"`);

    // Uncomment the push if the user wants it to push automatically. The previous script had it.
    console.log('🚀 Enviando para o repositório (Push)...');
    execSync('git push');

    console.log('🎉 Deploy realizado com sucesso!');
} catch (error) {
    console.error('❌ Erro ao executar comandos do Git:', error.message);
}