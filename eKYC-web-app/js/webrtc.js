const BE_HTTP = 'http://localhost:8080'
const BE_WS   = 'ws://localhost:8080'

let localStream = null
let pc          = null
let ws          = null

const wsPill   = document.getElementById('wsPill')
const wsStatus = document.getElementById('wsStatus')
const iceState = document.getElementById('iceState')
const video    = document.getElementById('video')
const overlay  = document.getElementById('overlay')
const flash    = document.getElementById('flash')
const btnStop  = document.getElementById('btnStop')

// ─── WebSocket ───────────────────────────────────────────────────────────────

function connectWebSocket(wsEndpoint, onMessage) {
  const url = `${BE_WS}${wsEndpoint}`
  console.log('[WS] Connecting to:', url)

  ws = new WebSocket(url)

  ws.onopen = () => {
    console.log('[WS] Connected!')
    wsPill.className     = 'status-pill connected'
    wsStatus.textContent = 'Terhubung'
  }

  ws.onmessage = (e) => {
    console.log('[WS] Message:', e.data)
    const data = JSON.parse(e.data)
    if (typeof onMessage === 'function') onMessage(data)
  }

  ws.onclose = (e) => {
    console.warn('[WS] Closed — code:', e.code, 'reason:', e.reason)
    wsPill.className     = 'status-pill'
    wsStatus.textContent = 'Terputus'
  }

  ws.onerror = (e) => {
    console.error('[WS] Error:', e)
    wsPill.className     = 'status-pill error'
    wsStatus.textContent = 'Error'
  }
}

// ─── WebRTC ──────────────────────────────────────────────────────────────────

async function startWebRTC(wsEndpoint, offerEndpoint, onMessage) {
  try {
    localStream     = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    video.srcObject = localStream
    overlay.classList.add('hidden')
    console.log('[WebRTC] Kamera aktif')
  } catch (err) {
    console.error('[WebRTC] Kamera gagal:', err)
    wsStatus.textContent = 'Kamera gagal'
    wsPill.className     = 'status-pill error'
    return
  }

  // ✅ Pass wsEndpoint ke connectWebSocket — sebelumnya tidak dipakai sama sekali
  connectWebSocket(wsEndpoint, onMessage)
  await new Promise(r => setTimeout(r, 400))

  pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
  })

  pc.oniceconnectionstatechange = () => {
    const state = pc.iceConnectionState
    console.log('[ICE] State:', state)
    if (iceState) iceState.textContent = `ICE: ${state}`
    if (state === 'failed' || state === 'disconnected') {
      wsPill.className     = 'status-pill error'
      wsStatus.textContent = 'ICE gagal'
    }
  }

  localStream.getTracks().forEach(track => {
    pc.addTrack(track, localStream)
    console.log('[WebRTC] Track added:', track.kind)
  })

  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)
  console.log('[WebRTC] Offer created, sending to:', offerEndpoint)

  try {
    const res = await fetch(`${BE_HTTP}${offerEndpoint}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sdp: offer.sdp, type: offer.type }),
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const answer = await res.json()
    console.log('[WebRTC] Answer received, setting remote description')
    await pc.setRemoteDescription(new RTCSessionDescription(answer))
  } catch (err) {
    console.error('[WebRTC] Offer failed:', err)
    wsPill.className     = 'status-pill error'
    wsStatus.textContent = 'Server error'
  }
}

// ─── Stop ────────────────────────────────────────────────────────────────────

function stopAll() {
  if (pc)          { pc.close(); pc = null }
  if (ws)          { ws.close(); ws = null }
  if (localStream) { localStream.getTracks().forEach(t => t.stop()); localStream = null }

  video.srcObject      = null
  overlay.classList.remove('hidden')
  wsPill.className     = 'status-pill'
  wsStatus.textContent = 'Terputus'
  if (iceState) iceState.textContent = 'ICE: —'
  console.log('[WebRTC] Stopped.')
}

function triggerFlash() {
  flash.classList.remove('active')
  void flash.offsetWidth
  flash.classList.add('active')
}

if (btnStop) btnStop.addEventListener('click', stopAll)
