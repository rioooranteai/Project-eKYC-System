const logBody     = document.getElementById('logBody')
const logEmpty    = document.getElementById('logEmpty')
const logCountEl  = document.getElementById('logCount')
const faceStatus  = document.getElementById('faceStatus')
const faceStatusText = document.getElementById('faceStatusText')
const progressFill   = document.getElementById('progressFill')
const progressPct    = document.getElementById('progressPct')
const statFrames     = document.getElementById('statFrames')
const statScore      = document.getElementById('statScore')
const statResult     = document.getElementById('statResult')
const faceOval       = document.getElementById('faceOval')

let frameCount = 0
let logCount   = 0

function addLog(type, msg, data = null) {
  logCount++
  if (logEmpty) logEmpty.remove()

  const time  = new Date().toTimeString().slice(0, 8)
  const entry = document.createElement('div')
  entry.className = `log-entry ${type}`
  entry.innerHTML = `
    <span class="log-time">${time}</span>
    <span class="log-msg">${msg}</span>
    ${data ? `<div class="log-data">${JSON.stringify(data)}</div>` : ''}
  `
  logBody.appendChild(entry)
  logBody.scrollTop = logBody.scrollHeight
  logCountEl.textContent = `${logCount} events`
}

function onMessage(data) {
  if (data.event === 'connected') {
    addLog('info', 'Terhubung ke server.')
    return
  }

  if (data.event === 'frame_received') {
    frameCount++
    statFrames.textContent = frameCount
    triggerFlash()
    return
  }

  if (data.event === 'face_detected') {
    faceOval.classList.add('detected')
    faceStatus.className     = 'status-badge scanning'
    faceStatusText.textContent = '⟳ Wajah terdeteksi, menganalisa...'
    addLog('info', 'Wajah terdeteksi.')
    return
  }

  if (data.event === 'liveness_result') {
    const score = data.score ?? 0
    const live  = data.is_live ?? false
    const pct   = Math.round(score * 100)

    progressFill.style.width = `${pct}%`
    progressPct.textContent  = `${pct}%`
    statScore.textContent    = `${pct}%`

    if (live) {
      faceStatus.className      = 'status-badge success'
      faceStatusText.textContent = '✓ Wajah asli terverifikasi'
      statResult.textContent     = 'LIVE'
      statResult.style.color     = 'var(--accent)'
      addLog('success', `Liveness terverifikasi — score ${pct}%`, { score, is_live: live })
    } else {
      faceStatus.className      = 'status-badge failed'
      faceStatusText.textContent = '✗ Wajah tidak terverifikasi'
      statResult.textContent     = 'FAKE'
      statResult.style.color     = 'var(--warn)'
      addLog('error', `Liveness gagal — score ${pct}%`, { score, is_live: live })
    }
  }
}

// Tampilkan data KTP dari session jika ada
const storedKTP = sessionStorage.getItem('ktpData')
if (storedKTP) {
  const ktp = JSON.parse(storedKTP)
  addLog('info', `Data KTP dimuat: ${ktp.nama || '—'} (NIK: ${ktp.nik || '—'})`)
}

faceStatus.className      = 'status-badge scanning'
faceStatusText.textContent = '⟳ Menginisialisasi kamera...'

startWebRTC('/webrtc/ws/notify', '/webrtc/offer/face', onMessage)