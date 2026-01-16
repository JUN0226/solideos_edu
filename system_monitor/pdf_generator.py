"""
PDF 리포트 생성 모듈
수집된 시스템 리소스 데이터를 PDF 리포트로 생성합니다.
"""

import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import numpy as np


class PDFReportGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._create_custom_styles()
        
    def _register_fonts(self):
        """한글 폰트 등록"""
        # Windows 맑은 고딕 폰트
        font_paths = [
            'C:/Windows/Fonts/malgun.ttf',
            'C:/Windows/Fonts/malgunbd.ttf',
            'C:/Windows/Fonts/NanumGothic.ttf',
        ]
        
        self.font_name = 'Helvetica'
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if 'malgun' in font_path:
                        pdfmetrics.registerFont(TTFont('MalgunGothic', font_path))
                        self.font_name = 'MalgunGothic'
                    elif 'Nanum' in font_path:
                        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                        self.font_name = 'NanumGothic'
                    break
                except Exception:
                    continue
        
        # matplotlib 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False
        
    def _create_custom_styles(self):
        """커스텀 스타일 생성"""
        self.styles.add(ParagraphStyle(
            name='KoreanTitle',
            fontName=self.font_name,
            fontSize=24,
            leading=30,
            alignment=1,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='KoreanHeading',
            fontName=self.font_name,
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2563eb')
        ))
        
        self.styles.add(ParagraphStyle(
            name='KoreanBody',
            fontName=self.font_name,
            fontSize=10,
            leading=14
        ))
        
    def _create_line_chart(self, timestamps, data_series, title, ylabel, labels, colors_list=None):
        """라인 차트 생성"""
        fig, ax = plt.subplots(figsize=(8, 3))
        
        if colors_list is None:
            colors_list = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6']
        
        for i, (data, label) in enumerate(zip(data_series, labels)):
            color = colors_list[i % len(colors_list)]
            ax.plot(range(len(data)), data, label=label, color=color, linewidth=1.5)
        
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel('시간 (초)', fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#f8fafc')
        fig.patch.set_facecolor('white')
        
        # 이미지로 저장
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return buf
    
    def _create_bar_chart(self, labels, values, title, ylabel, color='#3b82f6'):
        """바 차트 생성"""
        fig, ax = plt.subplots(figsize=(8, 3))
        
        bars = ax.bar(labels, values, color=color, alpha=0.8)
        
        # 값 표시
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}%',
                   ha='center', va='bottom', fontsize=8)
        
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_ylim(0, 100)
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_facecolor('#f8fafc')
        fig.patch.set_facecolor('white')
        
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return buf
    
    def _calculate_statistics(self, data_list):
        """통계 계산"""
        if not data_list:
            return {'avg': 0, 'min': 0, 'max': 0}
        
        return {
            'avg': round(sum(data_list) / len(data_list), 2),
            'min': round(min(data_list), 2),
            'max': round(max(data_list), 2)
        }
    
    def generate_report(self, recorded_data, start_time, end_time):
        """PDF 리포트 생성"""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        story = []
        
        # 제목
        story.append(Paragraph("시스템 리소스 모니터링 리포트", self.styles['KoreanTitle']))
        story.append(Spacer(1, 10))
        
        # 기본 정보
        info_data = [
            ['항목', '내용'],
            ['측정 시작', start_time],
            ['측정 종료', end_time],
            ['총 샘플 수', f'{len(recorded_data)}개'],
            ['샘플링 간격', '1초'],
        ]
        
        if recorded_data and 'system' in recorded_data[0]:
            sys_info = recorded_data[0]['system']
            info_data.extend([
                ['운영체제', f"{sys_info.get('platform', 'N/A')} {sys_info.get('platform_release', '')}"],
                ['호스트명', sys_info.get('hostname', 'N/A')],
                ['프로세서', sys_info.get('processor', 'N/A')[:50]],
            ])
        
        info_table = Table(info_data, colWidths=[100, 350])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # 데이터 추출
        cpu_data = [d['cpu']['percent'] for d in recorded_data if 'cpu' in d]
        memory_data = [d['memory']['percent'] for d in recorded_data if 'memory' in d]
        
        network_sent = [d['network']['bytes_sent_speed'] for d in recorded_data if 'network' in d]
        network_recv = [d['network']['bytes_recv_speed'] for d in recorded_data if 'network' in d]
        
        disk_read = [d['disk']['io']['read_speed'] for d in recorded_data if 'disk' in d]
        disk_write = [d['disk']['io']['write_speed'] for d in recorded_data if 'disk' in d]
        
        gpu_load = []
        gpu_temp = []
        gpu_memory = []
        if recorded_data and recorded_data[0].get('gpu', {}).get('available'):
            for d in recorded_data:
                if d.get('gpu', {}).get('gpus'):
                    gpu = d['gpu']['gpus'][0]
                    gpu_load.append(gpu.get('load', 0))
                    gpu_temp.append(gpu.get('temperature', 0) or 0)
                    gpu_memory.append(gpu.get('memory_percent', 0))
        
        cpu_temp_data = [d['cpu'].get('temperature', 0) or 0 for d in recorded_data if 'cpu' in d]
        
        # === CPU & 메모리 ===
        story.append(Paragraph("CPU & 메모리 사용량", self.styles['KoreanHeading']))
        
        chart_buf = self._create_line_chart(
            range(len(cpu_data)),
            [cpu_data, memory_data],
            'CPU & 메모리 사용률 추이',
            '사용률 (%)',
            ['CPU', '메모리'],
            ['#3b82f6', '#22c55e']
        )
        story.append(Image(chart_buf, width=450, height=170))
        story.append(Spacer(1, 10))
        
        # CPU & 메모리 통계 테이블
        cpu_stats = self._calculate_statistics(cpu_data)
        mem_stats = self._calculate_statistics(memory_data)
        
        stats_data = [
            ['항목', '평균', '최소', '최대'],
            ['CPU 사용률 (%)', f"{cpu_stats['avg']}", f"{cpu_stats['min']}", f"{cpu_stats['max']}"],
            ['메모리 사용률 (%)', f"{mem_stats['avg']}", f"{mem_stats['min']}", f"{mem_stats['max']}"],
        ]
        
        stats_table = Table(stats_data, colWidths=[150, 100, 100, 100])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#eff6ff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bfdbfe')),
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # === GPU (있는 경우) ===
        if gpu_load:
            story.append(Paragraph("GPU 사용량", self.styles['KoreanHeading']))
            
            chart_buf = self._create_line_chart(
                range(len(gpu_load)),
                [gpu_load, gpu_memory, gpu_temp],
                'GPU 사용률, 메모리 & 온도 추이',
                '값',
                ['사용률 (%)', '메모리 (%)', '온도 (°C)'],
                ['#8b5cf6', '#f59e0b', '#ef4444']
            )
            story.append(Image(chart_buf, width=450, height=170))
            story.append(Spacer(1, 10))
            
            gpu_load_stats = self._calculate_statistics(gpu_load)
            gpu_temp_stats = self._calculate_statistics(gpu_temp)
            gpu_mem_stats = self._calculate_statistics(gpu_memory)
            
            gpu_stats_data = [
                ['항목', '평균', '최소', '최대'],
                ['GPU 사용률 (%)', f"{gpu_load_stats['avg']}", f"{gpu_load_stats['min']}", f"{gpu_load_stats['max']}"],
                ['GPU 메모리 (%)', f"{gpu_mem_stats['avg']}", f"{gpu_mem_stats['min']}", f"{gpu_mem_stats['max']}"],
                ['GPU 온도 (°C)', f"{gpu_temp_stats['avg']}", f"{gpu_temp_stats['min']}", f"{gpu_temp_stats['max']}"],
            ]
            
            gpu_table = Table(gpu_stats_data, colWidths=[150, 100, 100, 100])
            gpu_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f3ff')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c4b5fd')),
            ]))
            story.append(gpu_table)
            story.append(Spacer(1, 20))
        
        # === 네트워크 ===
        story.append(Paragraph("네트워크 트래픽", self.styles['KoreanHeading']))
        
        chart_buf = self._create_line_chart(
            range(len(network_sent)),
            [network_sent, network_recv],
            '네트워크 송수신 속도 추이',
            '속도 (KB/s)',
            ['송신 (Upload)', '수신 (Download)'],
            ['#f59e0b', '#06b6d4']
        )
        story.append(Image(chart_buf, width=450, height=170))
        story.append(Spacer(1, 10))
        
        net_sent_stats = self._calculate_statistics(network_sent)
        net_recv_stats = self._calculate_statistics(network_recv)
        
        net_stats_data = [
            ['항목', '평균', '최소', '최대'],
            ['송신 속도 (KB/s)', f"{net_sent_stats['avg']}", f"{net_sent_stats['min']}", f"{net_sent_stats['max']}"],
            ['수신 속도 (KB/s)', f"{net_recv_stats['avg']}", f"{net_recv_stats['min']}", f"{net_recv_stats['max']}"],
        ]
        
        net_table = Table(net_stats_data, colWidths=[150, 100, 100, 100])
        net_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891b2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecfeff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a5f3fc')),
        ]))
        story.append(net_table)
        story.append(Spacer(1, 20))
        
        # === 디스크 I/O ===
        story.append(Paragraph("디스크 I/O", self.styles['KoreanHeading']))
        
        chart_buf = self._create_line_chart(
            range(len(disk_read)),
            [disk_read, disk_write],
            '디스크 읽기/쓰기 속도 추이',
            '속도 (MB/s)',
            ['읽기', '쓰기'],
            ['#22c55e', '#ef4444']
        )
        story.append(Image(chart_buf, width=450, height=170))
        story.append(Spacer(1, 10))
        
        disk_read_stats = self._calculate_statistics(disk_read)
        disk_write_stats = self._calculate_statistics(disk_write)
        
        disk_stats_data = [
            ['항목', '평균', '최소', '최대'],
            ['읽기 속도 (MB/s)', f"{disk_read_stats['avg']}", f"{disk_read_stats['min']}", f"{disk_read_stats['max']}"],
            ['쓰기 속도 (MB/s)', f"{disk_write_stats['avg']}", f"{disk_write_stats['min']}", f"{disk_write_stats['max']}"],
        ]
        
        disk_table = Table(disk_stats_data, colWidths=[150, 100, 100, 100])
        disk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a34a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0fdf4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#86efac')),
        ]))
        story.append(disk_table)
        story.append(Spacer(1, 20))
        
        # === 디스크 사용량 ===
        if recorded_data and 'disk' in recorded_data[-1]:
            story.append(Paragraph("디스크 파티션 사용량", self.styles['KoreanHeading']))
            
            partitions = recorded_data[-1]['disk']['partitions']
            if partitions:
                partition_labels = [p['mountpoint'][:10] for p in partitions]
                partition_values = [p['percent'] for p in partitions]
                
                chart_buf = self._create_bar_chart(
                    partition_labels,
                    partition_values,
                    '디스크 파티션별 사용률',
                    '사용률 (%)',
                    '#3b82f6'
                )
                story.append(Image(chart_buf, width=450, height=170))
                story.append(Spacer(1, 10))
                
                partition_data = [['파티션', '전체 (GB)', '사용 (GB)', '여유 (GB)', '사용률 (%)']]
                for p in partitions:
                    partition_data.append([
                        p['mountpoint'],
                        f"{p['total_gb']}",
                        f"{p['used_gb']}",
                        f"{p['free_gb']}",
                        f"{p['percent']}"
                    ])
                
                partition_table = Table(partition_data, colWidths=[90, 90, 90, 90, 90])
                partition_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#475569')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ]))
                story.append(partition_table)
        
        # 리포트 생성
        doc.build(story)
        return self.output_path


# 테스트용
if __name__ == '__main__':
    # 테스트 데이터 생성
    import random
    from monitor import SystemMonitor
    
    monitor = SystemMonitor()
    test_data = []
    
    for i in range(60):
        data = monitor.get_all_resources()
        test_data.append(data)
    
    generator = PDFReportGenerator('test_report.pdf')
    generator.generate_report(
        test_data,
        '2024-01-01 10:00:00',
        '2024-01-01 10:01:00'
    )
    print('PDF generated: test_report.pdf')
