const appVersion = "1.0.11"; 
document.addEventListener("DOMContentLoaded", () => {
    const versionEl = document.getElementById('app-version-display');
    if (versionEl) {
        versionEl.innerText = 'v' + appVersion;
    }
});