#!/usr/bin/env python3
"""
3D Print Quote - 微信集成模块
用户发送 STL/3MF 文件到微信，自动回复报价
"""

import os
import sys
import tempfile

# 添加技能目录到路径
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from stl_parser import STLModel
from threemf_parser import ThreeMFModel
from quote_engine import calculate_quote, format_quote_report, load_config


def analyze_and_quote(filepath, material='PLA'):
    """
    分析模型并生成报价
    
    参数:
        filepath: 模型文件路径
        material: 材料类型
    
    返回:
        (stats, quote, report_text)
    """
    config = load_config()
    ext = os.path.splitext(filepath)[1].lower()
    
    # 分析模型
    if ext == '.stl':
        model = STLModel()
        model.load(filepath)
        stats = model.get_stats()
    elif ext == '.3mf':
        model = ThreeMFModel()
        model.load(filepath)
        stats = model.get_stats()
    else:
        raise ValueError(f"不支持的格式：{ext}")
    
    # 计算报价
    quote = calculate_quote(stats, material, config=config)
    
    # 生成报告
    report = format_quote_report(stats, quote, filepath)
    
    return stats, quote, report


def weixin_quote_handler(file_path, user_message=""):
    """
    微信消息处理器
    当用户发送 STL/3MF 文件时调用
    
    参数:
        file_path: 微信保存的文件路径
        user_message: 用户附带的消息（可指定材料）
    
    返回:
        回复文本
    """
    # 解析用户指定的材料
    material = 'PLA'
    material_keywords = {
        'pla': 'PLA',
        'abs': 'ABS',
        'petg': 'PETG',
        '尼龙': 'Nylon',
        'nylon': 'Nylon',
        'tpu': 'TPU',
        '树脂': 'Resin',
        'resin': 'Resin'
    }
    
    msg_lower = user_message.lower() if user_message else ''
    for key, mat in material_keywords.items():
        if key in msg_lower:
            material = mat
            break
    
    try:
        stats, quote, report = analyze_and_quote(file_path, material)
        
        # 生成简短版回复（适合微信）
        short_reply = f"""📦 3D 打印报价
━━━━━━━━━━━━━━━━
模型：{os.path.basename(file_path)}
尺寸：{stats['bounding_box_mm'][0]:.1f} × {stats['bounding_box_mm'][1]:.1f} × {stats['bounding_box_mm'][2]:.1f} mm
体积：{stats['volume_cm3']:.2f} cm³
重量：{quote['weight_g']:.2f} g ({quote['material_name']})
打印：{quote['print_time_hours']:.1f} 小时
━━━━━━━━━━━━━━━━
💰 建议售价：¥{quote['price']:.2f}
━━━━━━━━━━━━━━━━
材料：{quote['material_name']} ({quote['material_desc']})
"""
        return short_reply
    
    except Exception as e:
        return f"❌ 分析失败：{e}\n请确认文件是有效的 STL 或 3MF 格式"


if __name__ == '__main__':
    # 测试
    if len(sys.argv) > 1:
        reply = weixin_quote_handler(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '')
        print(reply)
