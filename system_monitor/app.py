"""
시스템 리소스 모니터링 웹 애플리케이션
Flask 기반의 실시간 모니터링 대시보드
"""

import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS

from monitor import SystemMonitor
from pdf_generator import PDFReportGenerator

app = Flask(__name__)
CORS(app)

# 전역 변수
monitor = SystemMonitor()
recording = False
recorded_data = []
recording_start_time = None
recording_thread = None
RECORDING_DURATION = 300  # 5분 (300초)


def recording_worker():
    """백그라운드 기록 워커"""
    global recording, recorded_data, recording_start_time
    
    start = time.time()
    while recording and (time.time() - start) < RECORDING_DURATION:
        try:
            data = monitor.get_all_resources()
            recorded_data.append(data)
        except Exception as e:
            print(f"Recording error: {e}")
        time.sleep(1)
    
    recording = False


@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('index.html')


@app.route('/api/resources')
def get_resources():
    """실시간 리소스 데이터 API"""
    try:
        data = monitor.get_all_resources()
        data['recording'] = recording
        data['recorded_count'] = len(recorded_data)
        data['recording_duration'] = RECORDING_DURATION
        
        if recording and recording_start_time:
            elapsed = (datetime.now() - recording_start_time).total_seconds()
            data['recording_elapsed'] = int(elapsed)
            data['recording_remaining'] = max(0, RECORDING_DURATION - int(elapsed))
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/start-recording', methods=['POST'])
def start_recording():
    """기록 시작"""
    global recording, recorded_data, recording_start_time, recording_thread
    
    if recording:
        return jsonify({'status': 'already_recording'})
    
    recording = True
    recorded_data = []
    recording_start_time = datetime.now()
    
    recording_thread = threading.Thread(target=recording_worker, daemon=True)
    recording_thread.start()
    
    return jsonify({
        'status': 'started',
        'start_time': recording_start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration': RECORDING_DURATION
    })


@app.route('/api/stop-recording', methods=['POST'])
def stop_recording():
    """기록 중지"""
    global recording
    
    if not recording:
        return jsonify({'status': 'not_recording'})
    
    recording = False
    
    return jsonify({
        'status': 'stopped',
        'samples': len(recorded_data)
    })


@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """PDF 리포트 생성"""
    global recorded_data, recording_start_time
    
    if len(recorded_data) < 2:
        return jsonify({'error': 'Not enough data to generate report'}), 400
    
    try:
        # 리포트 파일 경로
        report_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(report_dir, f'system_report_{timestamp}.pdf')
        
        # 시작/종료 시간
        start_time = recorded_data[0]['timestamp']
        end_time = recorded_data[-1]['timestamp']
        
        # PDF 생성
        generator = PDFReportGenerator(report_path)
        generator.generate_report(recorded_data, start_time, end_time)
        
        return jsonify({
            'status': 'success',
            'filename': os.path.basename(report_path),
            'path': report_path,
            'samples': len(recorded_data)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-report/<filename>')
def download_report(filename):
    """PDF 리포트 다운로드"""
    try:
        report_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(report_dir, filename)
        
        if os.path.exists(report_path):
            return send_file(
                report_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recording-status')
def recording_status():
    """현재 기록 상태"""
    return jsonify({
        'recording': recording,
        'samples': len(recorded_data),
        'start_time': recording_start_time.strftime('%Y-%m-%d %H:%M:%S') if recording_start_time else None
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  시스템 리소스 모니터링 대시보드")
    print("=" * 60)
    print(f"  서버 시작: http://localhost:5000")
    print("  브라우저에서 위 주소로 접속하세요.")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
