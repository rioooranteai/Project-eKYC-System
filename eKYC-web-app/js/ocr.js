const resultBody  = document.getElementById('resultBody')
const resultEmpty = document.getElementById('resultEmpty')
const logCountEl  = document.getElementById('logCount')
const scanStatus  = document.getElementById('scanStatus')
const scanStatusText = document.getElementById('scanStatusText')
const progressFill   = document.getElementById('progressFill')
const progressPct    = document.getElementById('progressPct')
const statFrames     = document.getElementById('statFrames')
const statFields     = document.getElementById('statFields')
const statConf       = document.getElementById('statConf')
const btnNext        = document.getElementById('btnNext')

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

let frameCount = 0
let ktpData    = {}

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
    scanStatus.className     = 'status-badge success'
    scanStatusText.textContent = '✓ Data KTP berhasil dibaca'
    btnNext.style.pointerEvents = 'auto'
    btnNext.style.opacity       = '1'
  } else if (pct > 0) {
    scanStatus.className     = 'status-badge scanning'
    scanStatusText.textContent = `⟳ Membaca... ${pct}% selesai`
  }
}

function onMessage(data) {
  if (data.event === 'frame_received') {
    frameCount++
    statFrames.textContent = frameCount
    triggerFlash()
  }

  if (data.event === 'ktp_result' && data.data) {
    ktpData = data.data
    renderKTPResult(ktpData)
    sessionStorage.setItem('ktpData', JSON.stringify(ktpData))
  }
}

scanStatus.className     = 'status-badge scanning'
scanStatusText.textContent = '⟳ Menginisialisasi kamera...'

startWebRTC('/webrtc/ws/notify', '/webrtc/offer', onMessage)