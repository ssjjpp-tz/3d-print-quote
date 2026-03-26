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
        profit_margin: 利润率（倍数，如 1.5 表示 50% 利润）
        config: 配置字典
    
    返回:
        报价字典
    """
    if config is None:
        config = load_config()
    
    if profit_margin is None:
        profit_margin = config.get('default_profit_margin', 1.5)
    
    # 获取材料参数
    mat_info = config['materials'].get(material, config['materials']['PLA'])
    density = mat_info['density']
    price_per_g = mat_info['price_per_g']
    
    # 判断是否为金属材料
    is_metal = material in ['Aluminum', 'StainlessSteel', 'Steel', 'Titanium', 'Copper', 'Brass']
    
    # 更新重量（根据实际材料密度）
    weight = stats['volume_cm3'] * density
    
    if is_metal:
        # 金属 CNC 加工报价
        material_cost = weight * price_per_g
        
        # CNC 加工时间估算（根据体积和复杂度）
        volume_mm3 = stats.get('volume_cm3', 0) * 1000
        cnc_time_hours = max(0.5, volume_mm3 / 5000)  # 简单估算
        
        # CNC 机器成本
        cnc_hourly_rate = config.get('metal_processing', {}).get('cnc_hourly_rate', 80.0)
        machine_cost = cnc_time_hours * cnc_hourly_rate
        
        # CNC setup 费用
        cnc_setup_fee = config.get('metal_processing', {}).get('cnc_setup_fee', 50.0)
        
        # 人工成本
        labor_cost = config['labor_cost_base']
        if stats.get('surface_area_cm2', 0) > 200:
            labor_cost *= 1.5
        
        # 总成本
        total_cost = material_cost + machine_cost + labor_cost + cnc_setup_fee
        
        # 建议售价
        price = total_cost * profit_margin
        
        return {
            'material': material,
            'material_name': mat_info['name'],
            'material_name_zh': mat_info.get('name_zh', mat_info['name']),
            'material_desc': mat_info.get('desc', ''),
            'density': density,
            'weight_g': round(weight, 2),
            'material_cost': round(material_cost, 2),
            'machine_cost': round(machine_cost, 2),
            'labor_cost': round(labor_cost, 2),
            'cnc_setup_fee': cnc_setup_fee,
            'cnc_time_hours': round(cnc_time_hours, 2),
            'total_cost': round(total_cost, 2),
            'profit_margin': profit_margin,
            'price': round(price, 2),
            'is_metal': True
        }
    else:
        # 3D 打印报价（塑料）
        material_cost = weight * price_per_g
        machine_cost = stats['print_time_hours'] * config['machine_cost_per_hour']
        labor_cost = config['labor_cost_base']
        if stats.get('surface_area_cm2', 0) > 200:
            labor_cost *= 1.5
        
        total_cost = material_cost + machine_cost + labor_cost
        price = total_cost * profit_margin
        
        if price < config.get('min_price', 15.0):
            price = config['min_price']
        
        return {
            'material': material,
            'material_name': mat_info['name'],
            'material_name_zh': mat_info.get('name_zh', mat_info['name']),
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
            'print_time_min': stats['print_time_min'],
            'is_metal': False
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
    material_display = quote.get('material_name_zh') or quote['material_name']
    lines.append(f"   材料：{material_display} ({quote['material_desc']})")
    
    lines.append("")
    if quote.get('is_metal'):
        lines.append("⚙️ 加工估算 (CNC):")
        lines.append(f"   CNC 加工时间：{quote.get('cnc_time_hours', 0):.2f} 小时")
    else:
        lines.append("⏱️ 打印估算:")
        lines.append(f"   层高：{stats.get('layer_height_mm', 0.2)} mm")
        lines.append(f"   填充：{stats.get('infill_percent', 20)}%")
        lines.append(f"   时间：{quote['print_time_min']:.0f} 分钟 ({quote['print_time_hours']:.1f} 小时)")
    
    lines.append("")
    lines.append("💰 费用明细:")
    lines.append(f"   材料费    ¥{quote['material_cost']:.2f}")
    lines.append(f"   机器费    ¥{quote['machine_cost']:.2f}")
    lines.append(f"   人工费    ¥{quote['labor_cost']:.2f}")
    lines.append("   ─────────────────────")
    lines.append(f"   总成本    ¥{quote['total_cost']:.2f}")
    lines.append("   ─────────────────────")
    lines.append(f"   建议售价  ¥{quote['price']:.2f}")
    
    if quote.get('cnc_setup_fee'):
        lines.append(f"   （含 CNC  setup 费 ¥{quote['cnc_setup_fee']:.2f}）")
    
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
