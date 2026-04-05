// Creates a valid .ico file from the PNG using raw ICO format
const fs = require('fs');
const path = require('path');

const pngData = fs.readFileSync(path.join(__dirname, 'ollama-icon.png'));

// ICO format: header (6 bytes) + 1 directory entry (16 bytes) + PNG data
// Using PNG-in-ICO format which Windows Vista+ supports natively

const HEADER_SIZE = 6;
const DIR_ENTRY_SIZE = 16;
const dataOffset = HEADER_SIZE + DIR_ENTRY_SIZE;

const buf = Buffer.alloc(dataOffset + pngData.length);

// ICO Header
buf.writeUInt16LE(0, 0);          // reserved
buf.writeUInt16LE(1, 2);          // type: 1 = icon
buf.writeUInt16LE(1, 4);          // image count: 1

// Directory entry for 192x192 image
buf.writeUInt8(0, 6);             // width: 0 = 256 (or large)
buf.writeUInt8(0, 7);             // height: 0 = 256 (or large)
buf.writeUInt8(0, 8);             // color count
buf.writeUInt8(0, 9);             // reserved
buf.writeUInt16LE(1, 10);         // planes
buf.writeUInt16LE(32, 12);        // bit count
buf.writeUInt32LE(pngData.length, 14); // size of image data
buf.writeUInt32LE(dataOffset, 18);     // offset to image data

// Copy PNG data
pngData.copy(buf, dataOffset);

const outPath = path.join(__dirname, 'ollama-icon.ico');
fs.writeFileSync(outPath, buf);
console.log(`Created ${outPath} (${buf.length} bytes)`);
