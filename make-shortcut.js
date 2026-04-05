const { execFileSync } = require('child_process');
const os = require('os');
const path = require('path');
const fs = require('fs');

const icoPath = path.join(__dirname, 'ollama-icon.ico').replace(/\\/g, '\\\\');
const chromePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    process.env.LOCALAPPDATA + '\\Google\\Chrome\\Application\\chrome.exe'
];
const chrome = chromePaths.find(p => fs.existsSync(p)) || chromePaths[0];

const ps = `
$s = New-Object -ComObject WScript.Shell
$desktop = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$lnk = $s.CreateShortcut("$desktop\\Ollama Chat.lnk")
$lnk.TargetPath = "${chrome.replace(/\\/g, '\\\\')}"
$lnk.Arguments = "--app=http://localhost:8080"
$lnk.IconLocation = "${icoPath},0"
$lnk.Description = "Ollama Chat"
$lnk.Save()
Write-Host "Saved to: $desktop\\Ollama Chat.lnk"
`;

const result = execFileSync('powershell', ['-NoProfile', '-Command', ps], { encoding: 'utf8' });
console.log(result);
console.log('Chrome path:', chrome);
