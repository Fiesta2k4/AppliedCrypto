const crypto = require('crypto');
const argon2 = require('argon2');

async function deriveKey(masterPassword, salt) {
  return await argon2.hash(masterPassword + salt, { type: argon2.argon2id });
}

function encryptAES(secret, key) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-cbc', key.slice(0, 32), iv);
  const encrypted = Buffer.concat([cipher.update(secret, 'utf8'), cipher.final()]);
  return { iv: iv.toString('hex'), data: encrypted.toString('hex') };
}

module.exports = { deriveKey, encryptAES };