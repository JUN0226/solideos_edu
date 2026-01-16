/**
 * 시스템 리소스 모니터링 대시보드 JavaScript
 * 실시간 데이터 업데이트 및 차트 관리
 */

// 차트 객체 저장
const charts = {
    cpuHistory: null,
    networkHistory: null,
    diskIO: null
};

// 히스토리 데이터 (최대 60개 샘플)
const historyData = {
    cpu: [],
    memory: [],
    gpuLoad: [],
    gpuTemp: [],
    networkSent: [],
    networkRecv: [],
    diskRead: [],
    diskWrite: [],
    labels: []
};

const MAX_HISTORY = 60;
let updateInterval = null;
let lastReportFilename = null;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    startUpdating();
});

/**
 * 차트 초기화
 */
function initCharts() {
    // Chart.js 기본 설정
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
    Chart.defaults.font.family = "'Segoe UI', 'Malgun Gothic', sans-serif";

    // CPU/메모리 히스토리 차트
    const cpuCtx = document.getElementById('cpuHistoryChart')?.getContext('2d');
    if (cpuCtx) {
        charts.cpuHistory = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: '메모리',
                        data: [],
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { usePointStyle: true, padding: 15 }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        display: false
                    }
                },
                animation: { duration: 0 }
            }
        });
    }

    // 네트워크 히스토리 차트
    const networkCtx = document.getElementById('networkHistoryChart')?.getContext('2d');
    if (networkCtx) {
        charts.networkHistory = new Chart(networkCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '송신 (KB/s)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    },
                    {
                        label: '수신 (KB/s)',
                        data: [],
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { usePointStyle: true, padding: 15 }
                    }
                },
                scales: {
                    y: {
                        min: 0,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        display: false
                    }
                },
                animation: { duration: 0 }
            }
        });
    }
}

/**
 * 실시간 업데이트 시작
 */
function startUpdating() {
    updateData();
    updateInterval = setInterval(updateData, 1000);
}

/**
 * 데이터 업데이트
 */
async function updateData() {
    try {
        const response = await fetch('/api/resources');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        updateDashboard(data);
        updateHistory(data);
        updateCharts();
        updateRecordingStatus(data);

    } catch (error) {
        console.error('Fetch error:', error);
    }
}

/**
 * 대시보드 UI 업데이트
 */
function updateDashboard(data) {
    // CPU
    updateGauge('cpu-gauge', data.cpu.percent, '#3b82f6');
    document.getElementById('cpu-percent').textContent = `${data.cpu.percent.toFixed(1)}%`;
    document.getElementById('cpu-cores').textContent = `${data.cpu.cores_physical}C/${data.cpu.cores_logical}T`;
    document.getElementById('cpu-freq').textContent = `${data.cpu.frequency_current.toFixed(0)} MHz`;

    const cpuTemp = data.cpu.temperature;
    const cpuTempEl = document.getElementById('cpu-temp');
    if (cpuTemp !== null && cpuTemp > 0) {
        cpuTempEl.textContent = `${cpuTemp.toFixed(1)}°C`;
        cpuTempEl.className = getTemperatureClass(cpuTemp);
    } else {
        cpuTempEl.textContent = 'N/A';
        cpuTempEl.className = '';
    }

    // 메모리
    updateGauge('memory-gauge', data.memory.percent, '#22c55e');
    document.getElementById('memory-percent').textContent = `${data.memory.percent.toFixed(1)}%`;
    document.getElementById('memory-used').textContent = `${data.memory.used_gb} GB`;
    document.getElementById('memory-total').textContent = `${data.memory.total_gb} GB`;
    document.getElementById('memory-available').textContent = `${data.memory.available_gb} GB`;

    // GPU
    const gpuCard = document.getElementById('gpu-card');
    if (data.gpu.available && data.gpu.gpus.length > 0) {
        gpuCard.style.display = 'block';
        const gpu = data.gpu.gpus[0];

        document.getElementById('gpu-name').textContent = gpu.name;
        document.getElementById('gpu-load').textContent = `${gpu.load.toFixed(1)}%`;
        document.getElementById('gpu-memory').textContent = `${gpu.memory_percent.toFixed(1)}%`;

        const gpuTempEl = document.getElementById('gpu-temp');
        if (gpu.temperature !== null) {
            gpuTempEl.textContent = `${gpu.temperature}°C`;
            gpuTempEl.className = 'gpu-stat-value ' + getTemperatureClass(gpu.temperature);
        } else {
            gpuTempEl.textContent = 'N/A';
        }

        updateGauge('gpu-gauge', gpu.load, '#8b5cf6');
    } else {
        gpuCard.style.display = 'none';
    }

    // 네트워크
    document.getElementById('network-upload').textContent = `${data.network.bytes_sent_speed.toFixed(1)} KB/s`;
    document.getElementById('network-download').textContent = `${data.network.bytes_recv_speed.toFixed(1)} KB/s`;

    // 디스크 I/O
    document.getElementById('disk-read').textContent = `${data.disk.io.read_speed.toFixed(2)} MB/s`;
    document.getElementById('disk-write').textContent = `${data.disk.io.write_speed.toFixed(2)} MB/s`;

    // 디스크 파티션
    updatePartitions(data.disk.partitions);

    // 시스템 정보
    document.getElementById('hostname').textContent = data.system.hostname;
    document.getElementById('uptime').textContent = data.system.uptime_formatted;
}

/**
 * 게이지 업데이트
 */
function updateGauge(id, value, color) {
    const gauge = document.getElementById(id);
    if (!gauge) return;

    const circle = gauge.querySelector('.gauge-fill');
    if (!circle) return;

    const circumference = 2 * Math.PI * 54;
    const offset = circumference - (value / 100) * circumference;

    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = color;
}

/**
 * 온도 클래스 결정
 */
function getTemperatureClass(temp) {
    if (temp < 60) return 'temp-value normal';
    if (temp < 80) return 'temp-value warm';
    return 'temp-value hot';
}

/**
 * 파티션 업데이트
 */
function updatePartitions(partitions) {
    const container = document.getElementById('partition-list');
    if (!container) return;

    container.innerHTML = partitions.map(p => {
        const color = p.percent < 70 ? '#22c55e' : p.percent < 90 ? '#f59e0b' : '#ef4444';
        return `
            <div class="partition-item">
                <span class="partition-name">${p.mountpoint}</span>
                <div class="partition-bar">
                    <div class="partition-bar-fill" style="width: ${p.percent}%; background: ${color};"></div>
                </div>
                <span class="partition-info">${p.used_gb} / ${p.total_gb} GB (${p.percent}%)</span>
            </div>
        `;
    }).join('');
}

/**
 * 히스토리 데이터 업데이트
 */
function updateHistory(data) {
    const now = new Date().toLocaleTimeString();

    historyData.labels.push(now);
    historyData.cpu.push(data.cpu.percent);
    historyData.memory.push(data.memory.percent);
    historyData.networkSent.push(data.network.bytes_sent_speed);
    historyData.networkRecv.push(data.network.bytes_recv_speed);
    historyData.diskRead.push(data.disk.io.read_speed);
    historyData.diskWrite.push(data.disk.io.write_speed);

    if (data.gpu.available && data.gpu.gpus.length > 0) {
        historyData.gpuLoad.push(data.gpu.gpus[0].load);
        historyData.gpuTemp.push(data.gpu.gpus[0].temperature || 0);
    }

    // 히스토리 크기 제한
    if (historyData.labels.length > MAX_HISTORY) {
        historyData.labels.shift();
        historyData.cpu.shift();
        historyData.memory.shift();
        historyData.networkSent.shift();
        historyData.networkRecv.shift();
        historyData.diskRead.shift();
        historyData.diskWrite.shift();
        historyData.gpuLoad.shift();
        historyData.gpuTemp.shift();
    }
}

/**
 * 차트 업데이트
 */
function updateCharts() {
    if (charts.cpuHistory) {
        charts.cpuHistory.data.labels = historyData.labels;
        charts.cpuHistory.data.datasets[0].data = historyData.cpu;
        charts.cpuHistory.data.datasets[1].data = historyData.memory;
        charts.cpuHistory.update('none');
    }

    if (charts.networkHistory) {
        charts.networkHistory.data.labels = historyData.labels;
        charts.networkHistory.data.datasets[0].data = historyData.networkSent;
        charts.networkHistory.data.datasets[1].data = historyData.networkRecv;
        charts.networkHistory.update('none');
    }
}

/**
 * 기록 상태 업데이트
 */
function updateRecordingStatus(data) {
    const statusEl = document.getElementById('recording-status');
    const progressEl = document.getElementById('recording-progress');
    const startBtn = document.getElementById('btn-start-recording');
    const stopBtn = document.getElementById('btn-stop-recording');
    const generateBtn = document.getElementById('btn-generate-report');

    if (data.recording) {
        statusEl.classList.remove('hidden');
        progressEl.classList.remove('hidden');
        startBtn.disabled = true;
        stopBtn.disabled = false;

        const elapsed = data.recording_elapsed || 0;
        const total = data.recording_duration || 300;
        const percent = (elapsed / total) * 100;

        document.getElementById('progress-fill').style.width = `${percent}%`;
        document.getElementById('recording-time').textContent =
            `${formatTime(elapsed)} / ${formatTime(total)} (${data.recorded_count}개 샘플)`;

        // 자동 완료 체크
        if (elapsed >= total) {
            generateBtn.disabled = false;
        }
    } else {
        statusEl.classList.add('hidden');
        progressEl.classList.add('hidden');
        startBtn.disabled = false;
        stopBtn.disabled = true;

        // 데이터가 있으면 리포트 생성 활성화
        if (data.recorded_count > 0) {
            generateBtn.disabled = false;
        }
    }
}

/**
 * 시간 포맷
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 기록 시작
 */
async function startRecording() {
    try {
        const response = await fetch('/api/start-recording', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'started') {
            showNotification('기록을 시작했습니다. 5분간 데이터를 수집합니다.', 'success');
        } else {
            showNotification('이미 기록 중입니다.', 'error');
        }
    } catch (error) {
        showNotification('기록 시작에 실패했습니다.', 'error');
    }
}

/**
 * 기록 중지
 */
async function stopRecording() {
    try {
        const response = await fetch('/api/stop-recording', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'stopped') {
            showNotification(`기록을 중지했습니다. ${data.samples}개 샘플이 수집되었습니다.`, 'success');
            document.getElementById('btn-generate-report').disabled = false;
        }
    } catch (error) {
        showNotification('기록 중지에 실패했습니다.', 'error');
    }
}

/**
 * PDF 리포트 생성
 */
async function generateReport() {
    const btn = document.getElementById('btn-generate-report');
    btn.disabled = true;
    btn.textContent = '생성 중...';

    try {
        const response = await fetch('/api/generate-report', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            lastReportFilename = data.filename;
            showNotification(`PDF 리포트가 생성되었습니다: ${data.filename}`, 'success');
            document.getElementById('btn-download-report').disabled = false;

            // 자동 다운로드
            downloadReport();
        } else {
            showNotification(`리포트 생성 실패: ${data.error}`, 'error');
        }
    } catch (error) {
        showNotification('리포트 생성에 실패했습니다.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '📄 PDF 리포트 생성';
    }
}

/**
 * PDF 다운로드
 */
function downloadReport() {
    if (!lastReportFilename) {
        showNotification('다운로드할 리포트가 없습니다.', 'error');
        return;
    }

    window.location.href = `/api/download-report/${lastReportFilename}`;
}

/**
 * 알림 표시
 */
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');

    setTimeout(() => {
        notification.classList.add('hidden');
    }, 5000);
}
