const http = require('http');
const https = require('https');
const url = require('url');
const fs = require('fs');
const path = require('path');

const OLLAMA_SERVER = 'https://andrews-macbook-pro.taile4ced3.ts.net';
const PORT = 8080;

// Load icon bytes for serving
const iconPath = path.join(__dirname, 'ollama-icon.png');

// PWA manifest — uses URL so Chrome can validate it
const manifest = JSON.stringify({
    name: 'Ollama Chat',
    short_name: 'Ollama',
    start_url: '/',
    display: 'standalone',
    background_color: '#1a1a1a',
    theme_color: '#252525',
    icons: [
        { src: '/icon.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
        { src: '/icon.png', sizes: '512x512', type: 'image/png', purpose: 'any' }
    ]
});

const server = http.createServer((req, res) => {
    // Add CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // Handle preflight requests
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Serve the chat app
    if (req.url === '/' || req.url === '/index.html') {
        const htmlPath = path.join(__dirname, 'ollama-chat.html');
        fs.readFile(htmlPath, 'utf8', (err, data) => {
            if (err) { res.writeHead(500); res.end('Error loading app'); return; }
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(data);
        });
        return;
    }

    // Serve PWA manifest
    if (req.url === '/manifest.json') {
        res.writeHead(200, { 'Content-Type': 'application/manifest+json' });
        res.end(manifest);
        return;
    }

    // Serve icon from local file
    if (req.url === '/icon.png' || req.url === '/favicon.ico') {
        fs.readFile(iconPath, (err, data) => {
            if (err) { res.writeHead(404); res.end(); return; }
            res.writeHead(200, { 'Content-Type': 'image/png', 'Cache-Control': 'no-cache' });
            res.end(data);
        });
        return;
    }

    console.log(`${req.method} ${req.url}`);

    // Buffer request body first
    let requestBody = [];
    req.on('data', chunk => requestBody.push(chunk));
    req.on('end', () => {
        const bodyBuffer = Buffer.concat(requestBody);

        if (bodyBuffer.length > 0 && req.method === 'POST') {
            console.log('Request body:', bodyBuffer.toString().substring(0, 200));
        }

        // Parse the target URL
        const targetUrl = OLLAMA_SERVER + req.url;
        const parsedUrl = url.parse(targetUrl);

        // Build headers — include content-length so remote server knows body size
        const forwardHeaders = {
            'user-agent': 'Ollama-Proxy/1.0',
        };
        if (req.headers['content-type']) forwardHeaders['content-type'] = req.headers['content-type'];
        if (req.headers['accept']) forwardHeaders['accept'] = req.headers['accept'];
        if (bodyBuffer.length > 0) forwardHeaders['content-length'] = bodyBuffer.length;

        const proxyOptions = {
            hostname: parsedUrl.hostname,
            port: parsedUrl.port || 443,
            path: parsedUrl.path,
            method: req.method,
            headers: forwardHeaders,
            rejectUnauthorized: false
        };

        // Forward the request
        const proxyReq = https.request(proxyOptions, (proxyRes) => {
            console.log(`← ${proxyRes.statusCode} ${req.url}`);

            // Copy status code and headers
            res.writeHead(proxyRes.statusCode, proxyRes.headers);

            // Stream the response
            proxyRes.pipe(res);
        });

        proxyReq.on('error', (error) => {
            console.error('Proxy error:', error);
            res.writeHead(500);
            res.end('Proxy error: ' + error.message);
        });

        if (bodyBuffer.length > 0) {
            proxyReq.write(bodyBuffer);
        }
        proxyReq.end();
    });
});

server.listen(PORT, () => {
    console.log(`\n🦙 Ollama Chat running at http://localhost:${PORT}`);
    console.log(`   Forwarding API to: ${OLLAMA_SERVER}`);
    console.log(`\n   Open http://localhost:${PORT} in Chrome to install as a desktop app\n`);
});
