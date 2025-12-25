const appVersion = "1.0.6"; 
document.addEventListener("DOMContentLoaded", () => {
    const versionEl = document.getElementById('app-version-display');
    if (versionEl) {
        versionEl.innerText = 'v' + appVersion;
    }
});