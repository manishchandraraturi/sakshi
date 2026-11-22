/**
 * frontend/src/utils/verify.ts
 *
 * In-browser Ed25519 signature verification using TweetNaCl.
 * Produces byte-for-byte identical canonical JSON matching the Python backend.
 */
import nacl from 'tweetnacl'
import { decodeUTF8, decodeBase64 } from 'tweetnacl-util'

/**
 * Deterministically serializes a JS object/array into sorted, compact JSON without whitespace.
 * Matches Python: json.dumps(payload, sort_keys=True, separators=(',', ':'))
 */
export function canonicalJsonStringify(obj: any): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj)
  }

  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalJsonStringify).join(',') + ']'
  }

  const keys = Object.keys(obj).sort()
  const pairs = keys.map(
    (key) => `${JSON.stringify(key)}:${canonicalJsonStringify(obj[key])}`
  )
  return '{' + pairs.join(',') + '}'
}

/**
 * Verifies an Ed25519 detached signature in the browser.
 * Returns true if the signature is valid for the canonical payload, false if tampered or invalid.
 */
export function verifyCredential(
  payload: Record<string, any>,
  signatureB64: string,
  pubkeyB64: string
): boolean {
  try {
    if (!payload || !signatureB64 || !pubkeyB64) {
      return false
    }

    const canonicalString = canonicalJsonStringify(payload)
    const messageBytes = decodeUTF8(canonicalString)
    const signatureBytes = decodeBase64(signatureB64)
    const pubkeyBytes = decodeBase64(pubkeyB64)

    return nacl.sign.detached.verify(messageBytes, signatureBytes, pubkeyBytes)
  } catch (err) {
    console.error('Signature verification error:', err)
    return false
  }
}
