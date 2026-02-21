const BE_HTTP = 'http://localhost:8000'
const BE_WS   = 'ws://localhost:8000'

let localStream = null
let pc          = null
let ws          = null

const wsPill  = document.getElementById('wsPill')
const wsStatus = document.getElementById('wsStatus')
const iceState = document.getElementById('iceState')
const video    = document.getElementById('video')
const overlay  = document.getElementById('overlay')
const flash    = document.getElementById('flash')
const btnStop  = document.getElementById('btnStop')

// ─── WebSocket ───────────────────────────────────────────────────────────────

function connectWebSocket(onMessage) {
  ws = new WebSocket(`${BE_WS}/webrtc/ws/notify`)

  ws.onopen = () => {
    wsPill.className     = 'status-pill connected'
    wsStatus.textContent = 'Terhubung'
  }

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (typeof onMessage === 'function') onMessage(data)
  }

  ws.onclose = () => {
    wsPill.className     = 'status-pill'
    wsStatus.textContent = 'Terputus'
  }

  ws.onerror = () => {
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
  } catch (err) {
    wsStatus.textContent = 'Kamera gagal'
    wsPill.className     = 'status-pill error'
    return
  }

  connectWebSocket(onMessage)
  await new Promise(r => setTimeout(r, 400))

  pc = new RTCPeerConnection({
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
  })

  pc.oniceconnectionstatechange = () => {
    const state = pc.iceConnectionState
    if (iceState) iceState.textContent = `ICE: ${state}`
    if (state === 'failed' || state === 'disconnected') {
      wsPill.className     = 'status-pill error'
      wsStatus.textContent = 'ICE gagal'
    }
  }

  localStream.getTracks().forEach(track => pc.addTrack(track, localStream))

  const offer = await pc.createOffer()
  await pc.setLocalDescription(offer)

  try {
    const res = await fetch(`${BE_HTTP}${offerEndpoint}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ sdp: offer.sdp, type: offer.type }),
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const answer = await res.json()
    await pc.setRemoteDescription(new RTCSessionDescription(answer))
  } catch (err) {
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
}

function triggerFlash() {
  flash.classList.remove('active')
  void flash.offsetWidth
  flash.classList.add('active')
}

if (btnStop) btnStop.addEventListener('click', stopAll)