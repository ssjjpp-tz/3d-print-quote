#!/usr/bin/env python3
"""
3D Print Quote - 3D 打印自动报价
主入口文件

用法:
    python main.py model.stl [材料]
    python main.py model.3mf PLA --pdf quote.pdf
"""

import sys
import os
import argparse

# 添加技能目录到路径
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from stl_parser import STLModel
from threemf_parser import ThreeMFModel
from quote_engine import calculate_quote, format_quote_report, get_materials_list, load_config


def analyze_model(filepath):
    """分析模型文件（自动检测格式）"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.stl':
        model = STLModel()
        model.load(filepath)
        return model.get_stats()
    
    elif ext == '.3mf':
        model = ThreeMFModel()
        model.load(filepath)
        return model.get_stats()
    
    else:
        raise ValueError(f"不支持的文件格式：{ext}")


def main():
    parser = argparse.ArgumentParser(
        description='3D 打印自动报价',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py model.stl
  python main.py model.stl ABS
  python main.py model.3mf PLA
  python main.py *.stl --batch
  python main.py --materials  # 列出所有材料
        '''
    )
    
    parser.add_argument('file', nargs='?', help='STL 或 3MF 文件路径')
    parser.add_argument('material', nargs='?', default='PLA',
                       help='材料类型 (默认：PLA)')
    parser.add_argument('--materials', action='store_true',
                       help='列出所有可用材料')
    parser.add_argument('--batch', action='store_true',
                       help='批量处理多个文件')
    parser.add_argument('--profit', type=float, default=None,
                       help='利润率倍数 (默认：2.0)')
    parser.add_argument('--json', action='store_true',
                       help='输出 JSON 格式')
    parser.add_argument('--config', help='配置文件路径')
    
    args = parser.parse_args()
    
    config = load_config()
    
    # 列出材料
    if args.materials:
        print("\n可用材料:")
        print("-" * 60)
        for mat in get_materials_list(config):
            print(f"  {mat['id']:8} | {mat['name']:6} | "
                  f"密度：{mat['density']:.2f} g/cm³ | "
                  f"¥{mat['price_per_g']:.2f}/g | {mat['desc']}")
        print("-" * 60)
        return
    
    # 检查文件
    if not args.file:
        parser.print_help()
        print("\n❌ 请指定 STL 或 3MF 文件")
        sys.exit(1)
    
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在：{args.file}")
        sys.exit(1)
    
    # 验证材料
    material = args.material.upper()
    if material not in config['materials']:
        print(f"❌ 未知材料：{material}")
        print(f"可用材料：{', '.join(config['materials'].keys())}")
        sys.exit(1)
    
    # 分析模型
    try:
        print(f"\n正在分析：{args.file}")
        stats = analyze_model(args.file)
    except Exception as e:
        print(f"❌ 分析失败：{e}")
        sys.exit(1)
    
    # 计算报价
    quote = calculate_quote(stats, material, args.profit, config)
    
    # 输出
    if args.json:
        import json
        result = {
            'file': args.file,
            'stats': stats,
            'quote': quote
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        report = format_quote_report(stats, quote, args.file)
        print(report)


if __name__ == '__main__':
    main()
