const resultBody     = document.getElementById('resultBody')
const resultEmpty    = document.getElementById('resultEmpty')
const logCountEl     = document.getElementById('logCount')
const scanStatus     = document.getElementById('scanStatus')
const scanStatusText = document.getElementById('scanStatusText')
const progressFill   = document.getElementById('progressFill')
const progressPct    = document.getElementById('progressPct')
const statFrames     = document.getElementById('statFrames')
const statFields     = document.getElementById('statFields')
const statConf       = document.getElementById('statConf')
const btnNext        = document.getElementById('btnNext')
const btnCapture     = document.getElementById('btnCapture')
const canvas         = document.getElementById('bboxCanvas')
const ctx            = canvas.getContext('2d')
const videoEl        = document.getElementById('video')

const KTP_FIELDS = [
  { key: 'nik',               label: 'NIK' },
  { key: 'nama',              label: 'Nama' },
  { key: 'tempat_lahir',      label: 'Tempat Lahir' },
  { key: 'tgl_lahir',         label: 'Tgl Lahir' },
  { key: 'jenis_kelamin',     label: 'Jenis Kelamin' },
  { key: 'gol_darah',         label: 'Gol. Darah' },
  { key: 'alamat',            label: 'Alamat' },
  { key: 'rt_rw',             label: 'RT/RW' },
  { key: 'kelurahan',         label: 'Kelurahan' },
  { key: 'kecamatan',         label: 'Kecamatan' },
  { key: 'agama',             label: 'Agama' },
  { key: 'status_perkawinan', label: 'Status' },
  { key: 'pekerjaan',         label: 'Pekerjaan' },
  { key: 'kewarganegaraan',   label: 'WN' },
  { key: 'berlaku_hingga',    label: 'Berlaku Hingga' },
]

const LERP_SPEED   = 0.12   // kecepatan gerak box (0.0 - 1.0)
const BOX_TIMEOUT  = 4000   // ms — hilang kalau tidak ada update

const ACCENT_COLOR = '#00ff88'
const CORNER_SIZE  = 16
const LINE_WIDTH   = 2

// Current = posisi yang sedang digambar (bergerak smooth via lerp)
// Target  = posisi tujuan dari hasil YOLO terbaru
let current = null   // { x, y, w, h, score }
let target  = null   // { x, y, w, h, score }
let boxLastSeenAt = null
let animFrameId   = null
let frameCount    = 0
let ktpDetected   = false

function syncCanvasSize() {
  const rect    = videoEl.getBoundingClientRect()
  canvas.width  = rect.width
  canvas.height = rect.height
}

window.addEventListener('resize', syncCanvasSize)
videoEl.addEventListener('loadedmetadata', syncCanvasSize)

function lerp(a, b, t) {
  return a + (b - a) * t
}

function lerpBox(cur, tgt, t) {
  return {
    x:     lerp(cur.x,     tgt.x,     t),
    y:     lerp(cur.y,     tgt.y,     t),
    w:     lerp(cur.w,     tgt.w,     t),
    h:     lerp(cur.h,     tgt.h,     t),
    score: tgt.score,
  }
}

function drawBox(box) {
  const cw = canvas.width
  const ch = canvas.height

  const x = box.x * cw
  const y = box.y * ch
  const w = box.w * cw
  const h = box.h * ch

  ctx.clearRect(0, 0, cw, ch)
  ctx.strokeStyle = ACCENT_COLOR
  ctx.lineWidth   = LINE_WIDTH
  ctx.shadowColor = ACCENT_COLOR
  ctx.shadowBlur  = 8

  // Corner kiri atas
  ctx.beginPath()
  ctx.moveTo(x, y + CORNER_SIZE)
  ctx.lineTo(x, y)
  ctx.lineTo(x + CORNER_SIZE, y)
  ctx.stroke()

  // Corner kanan atas
  ctx.beginPath()
  ctx.moveTo(x + w - CORNER_SIZE, y)
  ctx.lineTo(x + w, y)
  ctx.lineTo(x + w, y + CORNER_SIZE)
  ctx.stroke()

  // Corner kiri bawah
  ctx.beginPath()
  ctx.moveTo(x, y + h - CORNER_SIZE)
  ctx.lineTo(x, y + h)
  ctx.lineTo(x + CORNER_SIZE, y + h)
  ctx.stroke()

  // Corner kanan bawah
  ctx.beginPath()
  ctx.moveTo(x + w - CORNER_SIZE, y + h)
  ctx.lineTo(x + w, y + h)
  ctx.lineTo(x + w, y + h - CORNER_SIZE)
  ctx.stroke()

  // Label score di pojok kiri atas
  const label = `KTP ${Math.round(box.score * 100)}%`
  ctx.shadowBlur  = 0
  ctx.fillStyle   = ACCENT_COLOR
  ctx.font        = '600 11px JetBrains Mono, monospace'
  ctx.fillText(label, x + 6, y - 6)
}

function animLoop() {
  animFrameId = requestAnimationFrame(animLoop)

  // Cek timeout — hilangkan box kalau tidak ada update
  if (boxLastSeenAt && Date.now() - boxLastSeenAt > BOX_TIMEOUT) {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    current        = null
    target         = null
    boxLastSeenAt  = null
    setKTPDetected(false)
    return
  }

  if (!target) return

  // Inisialisasi current di posisi target pertama kali (langsung muncul)
  if (!current) {
    current = { ...target }
  }

  // Lerp current mendekati target
  current = lerpBox(current, target, LERP_SPEED)

  drawBox(current)
}

function setKTPDetected(detected) {
  ktpDetected = detected

  if (detected) {
    btnCapture.disabled  = false
    btnCapture.className = 'btn-capture active'
    scanStatus.className     = 'status-badge scanning'
    scanStatusText.textContent = '✦ KTP terdeteksi — siap capture'
  } else {
    btnCapture.disabled  = true
    btnCapture.className = 'btn-capture'
    if (scanStatusText.textContent.includes('terdeteksi')) {
      scanStatus.className     = 'status-badge idle'
      scanStatusText.textContent = '⏳ Menunggu KTP...'
    }
  }
}

function renderKTPResult(data) {
  if (resultEmpty) resultEmpty.remove()

  resultBody.innerHTML = ''
  let filled = 0

  KTP_FIELDS.forEach(({ key, label }) => {
    const val = data[key]
    if (val) filled++

    const row = document.createElement('div')
    row.className = 'result-row'
    row.innerHTML = `
      <span class="result-key">${label}</span>
      <span class="result-val ${val ? '' : 'empty'}">${val || '—'}</span>
    `
    resultBody.appendChild(row)
  })

  const pct = Math.round((filled / KTP_FIELDS.length) * 100)
  progressFill.style.width = `${pct}%`
  progressPct.textContent  = `${pct}%`
  logCountEl.textContent   = `${filled} field`
  statFields.textContent   = filled

  if (data.confidence_avg && data.confidence_avg > 0) {
    statConf.textContent = `${Math.round(data.confidence_avg * 100)}%`
  }

  if (pct >= 60) {
    scanStatus.className       = 'status-badge success'
    scanStatusText.textContent = '✓ Data KTP berhasil dibaca'
    btnNext.style.pointerEvents = 'auto'
    btnNext.style.opacity       = '1'
  }

  sessionStorage.setItem('ktpData', JSON.stringify(data))
}

function onMessage(data) {
  if (data.event === 'connected') return

  if (data.event === 'frame_received') {
    frameCount++
    statFrames.textContent = frameCount
    triggerFlash()
    return
  }

  // YOLO detect KTP
  if (data.event === 'yolo_result' && data.boxes?.length > 0) {
    const box      = data.boxes[0]
    target         = { x: box.x, y: box.y, w: box.w, h: box.h, score: box.score }
    boxLastSeenAt  = Date.now()
    syncCanvasSize()
    setKTPDetected(true)
    return
  }

  // YOLO tidak detect
  if (data.event === 'no_ktp') {
    target = null
    setKTPDetected(false)
    return
  }

  // Capture sedang diproses
  if (data.event === 'capture_processing') {
    btnCapture.className       = 'btn-capture processing'
    btnCapture.disabled        = true
    scanStatus.className       = 'status-badge scanning'
    scanStatusText.textContent = '⟳ Memproses OCR...'
    return
  }

  // Hasil OCR berhasil
  if (data.event === 'ktp_result') {
    renderKTPResult(data.data)
    btnCapture.className = 'btn-capture active'
    btnCapture.disabled  = false
    triggerFlash()
    return
  }

  // Capture gagal
  if (data.event === 'capture_failed') {
    scanStatus.className       = 'status-badge failed'
    scanStatusText.textContent = `✗ ${data.reason}`
    btnCapture.className       = ktpDetected ? 'btn-capture active' : 'btn-capture'
    btnCapture.disabled        = !ktpDetected
    return
  }
}

btnCapture.addEventListener('click', () => {
  if (!ktpDetected || !ws) return
  ws.send(JSON.stringify({ event: 'capture' }))
})

scanStatus.className       = 'status-badge scanning'
scanStatusText.textContent = '⟳ Menginisialisasi kamera...'

animLoop()
syncCanvasSize()

startWebRTC('/webrtc/ws/notify', '/webrtc/offer', onMessage)