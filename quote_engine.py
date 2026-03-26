#!/usr/bin/env python3
"""
3D 打印报价计算引擎
"""

import os
import json

# 默认配置
DEFAULT_CONFIG = {
    "materials": {
        "PLA": {"density": 1.24, "price_per_g": 0.08, "name": "PLA", "desc": "常用环保材料"},
        "ABS": {"density": 1.04, "price_per_g": 0.10, "name": "ABS", "desc": "高强度"},
        "PETG": {"density": 1.27, "price_per_g": 0.12, "name": "PETG", "desc": "耐候性好"},
        "Nylon": {"density": 1.14, "price_per_g": 0.25, "name": "尼龙", "desc": "耐磨"},
        "TPU": {"density": 1.21, "price_per_g": 0.18, "name": "TPU", "desc": "柔性材料"},
        "Resin": {"density": 1.10, "price_per_g": 0.15, "name": "树脂", "desc": "光固化"}
    },
    "machine_cost_per_hour": 5.0,
    "labor_cost_base": 10.0,
    "default_profit_margin": 2.0,
    "default_layer_height": 0.2,
    "default_infill": 20,
    "min_price": 15.0  # 最低起印价
}


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            custom_config = json.load(f)
            # 合并配置
            config = DEFAULT_CONFIG.copy()
            config.update(custom_config)
            return config
    return DEFAULT_CONFIG


def calculate_quote(stats, material='PLA', profit_margin=None, config=None):
    """
    计算报价
    
    参数:
        stats: 模型统计信息（来自 parser 的 get_stats）
        material: 材料类型
        profit_margin: 利润率（倍数，如 2.0 表示 100% 利润）
        config: 配置字典
    
    返回:
        报价字典
    """
    if config is None:
        config = load_config()
    
    if profit_margin is None:
        profit_margin = config.get('default_profit_margin', 2.0)
    
    # 获取材料参数
    mat_info = config['materials'].get(material, config['materials']['PLA'])
    density = mat_info['density']
    price_per_g = mat_info['price_per_g']
    
    # 更新重量（根据实际材料密度）
    weight = stats['volume_cm3'] * density
    
    # 材料成本
    material_cost = weight * price_per_g
    
    # 机器成本
    machine_cost = stats['print_time_hours'] * config['machine_cost_per_hour']
    
    # 人工成本（可根据表面积调整）
    labor_cost = config['labor_cost_base']
    if stats.get('surface_area_cm2', 0) > 200:
        labor_cost *= 1.5  # 大表面积增加后处理时间
    
    # 总成本
    total_cost = material_cost + machine_cost + labor_cost
    
    # 建议售价
    price = total_cost * profit_margin
    
    # 最低价格限制
    if price < config.get('min_price', 15.0):
        price = config['min_price']
    
    return {
        'material': material,
        'material_name': mat_info['name'],
        'material_desc': mat_info.get('desc', ''),
        'density': density,
        'weight_g': round(weight, 2),
        'material_cost': round(material_cost, 2),
        'machine_cost': round(machine_cost, 2),
        'labor_cost': round(labor_cost, 2),
        'total_cost': round(total_cost, 2),
        'profit_margin': profit_margin,
        'price': round(price, 2),
        'print_time_hours': stats['print_time_hours'],
        'print_time_min': stats['print_time_min']
    }


def format_quote_report(stats, quote, filename=None):
    """格式化报价报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("📦 3D 打印报价分析")
    lines.append("=" * 60)
    
    if filename:
        lines.append(f"文件：{filename}")
        if os.path.exists(filename):
            lines.append(f"大小：{os.path.getsize(filename) / 1024:.1f} KB")
    
    lines.append(f"格式：{stats.get('format', 'Unknown')}")
    lines.append("")
    
    lines.append("📐 几何信息:")
    lines.append(f"   三角形：{stats.get('triangles', 0):,}")
    lines.append(f"   顶点数：{stats.get('vertices', 0):,}")
    
    if stats.get('bounding_box_mm'):
        x, y, z = stats['bounding_box_mm']
        lines.append(f"   尺寸：{x:.1f} × {y:.1f} × {z:.1f} mm")
    
    lines.append("")
    lines.append(f"⚖️ 物理属性 ({quote['material']}):")
    lines.append(f"   体积：{stats.get('volume_cm3', 0):.2f} cm³")
    lines.append(f"   表面积：{stats.get('surface_area_cm2', 0):.2f} cm²")
    lines.append(f"   重量：{quote['weight_g']:.2f} g")
    lines.append(f"   材料：{quote['material_name']} ({quote['material_desc']})")
    
    lines.append("")
    lines.append("⏱️ 打印估算:")
    lines.append(f"   层高：{stats.get('layer_height_mm', 0.2)} mm")
    lines.append(f"   填充：{stats.get('infill_percent', 20)}%")
    lines.append(f"   时间：{quote['print_time_min']:.0f} 分钟 ({quote['print_time_hours']:.1f} 小时)")
    
    lines.append("")
    lines.append("💰 成本估算:")
    lines.append(f"   材料费：¥{quote['material_cost']:.2f}")
    lines.append(f"   机器费：¥{quote['machine_cost']:.2f}")
    lines.append(f"   人工费：¥{quote['labor_cost']:.2f}")
    lines.append(f"   总成本：¥{quote['total_cost']:.2f}")
    lines.append(f"   建议售价：¥{quote['price']:.2f} ({(quote['profit_margin']-1)*100:.0f}% 利润)")
    
    if quote['price'] < 15.0:
        lines.append(f"   ⚠️ 低于起印价，按 ¥15.00 计费")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def get_materials_list(config=None):
    """获取材料列表"""
    if config is None:
        config = load_config()
    
    return [
        {
            'id': key,
            'name': info['name'],
            'density': info['density'],
            'price_per_g': info['price_per_g'],
            'desc': info.get('desc', '')
        }
        for key, info in config['materials'].items()
    ]
