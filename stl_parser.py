#!/usr/bin/env python3
"""
STL 文件解析器 - 纯 Python 实现
支持 Binary STL 和 ASCII STL
"""

import struct
import math
import os


class STLModel:
    """STL 模型类"""
    
    def __init__(self):
        self.triangles = []  # [(normal, v1, v2, v3), ...]
        self.vertices = []
        self.header = ""
        self.is_binary = None
        self.filepath = ""
    
    def load(self, filepath):
        """加载 STL 文件"""
        self.filepath = filepath
        file_size = os.path.getsize(filepath)
        
        with open(filepath, 'rb') as f:
            header = f.read(80)
            # ASCII STL 以 'solid' 开头
            if header.strip().lower().startswith(b'solid'):
                self.is_binary = False
                self._load_ascii(filepath)
            else:
                self.is_binary = True
                self._load_binary(filepath, file_size)
        
        return self
    
    def _load_binary(self, filepath, file_size):
        """解析 Binary STL"""
        with open(filepath, 'rb') as f:
            self.header = f.read(80).decode('utf-8', errors='ignore').strip()
            num_triangles = struct.unpack('<I', f.read(4))[0]
            
            # 验证文件大小
            expected_size = 84 + num_triangles * 50
            if file_size != expected_size:
                # 尝试继续解析（有些文件有额外数据）
                pass
            
            for _ in range(num_triangles):
                data = f.read(50)
                if len(data) < 50:
                    break
                
                normal = struct.unpack('<3f', data[0:12])
                v1 = struct.unpack('<3f', data[12:24])
                v2 = struct.unpack('<3f', data[24:36])
                v3 = struct.unpack('<3f', data[36:48])
                
                self.triangles.append((normal, v1, v2, v3))
                self.vertices.extend([v1, v2, v3])
    
    def _load_ascii(self, filepath):
        """解析 ASCII STL"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        self.header = lines[0].strip() if lines else ""
        
        i = 0
        while i < len(lines):
            line = lines[i].strip().lower()
            if line.startswith('facet'):
                # 解析法向量
                parts = line.split()
                normal = (0, 0, 1)  # 默认法向量
                if len(parts) >= 5:
                    try:
                        normal = tuple(float(x) for x in parts[2:5])
                    except:
                        pass
                
                i += 1
                # 跳过 outer loop
                while i < len(lines) and 'outer loop' not in lines[i].lower():
                    i += 1
                i += 1
                
                vertices = []
                while i < len(lines) and 'vertex' in lines[i].lower():
                    vparts = lines[i].strip().split()
                    if len(vparts) >= 4:
                        try:
                            v = tuple(float(x) for x in vparts[1:4])
                            vertices.append(v)
                        except:
                            pass
                    i += 1
                
                if len(vertices) == 3:
                    self.triangles.append((normal, vertices[0], vertices[1], vertices[2]))
                    self.vertices.extend(vertices)
                
                # 跳过 endloop endfacet
                while i < len(lines) and 'endfacet' not in lines[i].lower():
                    i += 1
            i += 1
    
    def get_bounding_box(self):
        """计算边界盒"""
        if not self.vertices:
            return None
        
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        zs = [v[2] for v in self.vertices]
        
        return {
            'min': (min(xs), min(ys), min(zs)),
            'max': (max(xs), max(ys), max(zs)),
            'size': (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
        }
    
    def get_volume(self):
        """
        计算体积（散度定理）
        返回：立方厘米
        """
        volume = 0.0
        for _, v1, v2, v3 in self.triangles:
            vol = (v1[0] * (v2[1] * v3[2] - v3[1] * v2[2]) -
                   v1[1] * (v2[0] * v3[2] - v3[0] * v2[2]) +
                   v1[2] * (v2[0] * v3[1] - v3[0] * v2[1])) / 6.0
            volume += vol
        
        return abs(volume) / 1000.0  # mm³ → cm³
    
    def get_surface_area(self):
        """
        计算表面积
        返回：平方厘米
        """
        area = 0.0
        for _, v1, v2, v3 in self.triangles:
            ax = v2[0] - v1[0]
            ay = v2[1] - v1[1]
            az = v2[2] - v1[2]
            bx = v3[0] - v1[0]
            by = v3[1] - v1[1]
            bz = v3[2] - v1[2]
            
            cx = ay * bz - az * by
            cy = az * bx - ax * bz
            cz = ax * by - ay * bx
            
            tri_area = math.sqrt(cx*cx + cy*cy + cz*cz) / 2.0
            area += tri_area
        
        return area / 100.0  # mm² → cm²
    
    def get_stats(self, material_density=1.24, layer_height=0.2, infill=20):
        """获取完整统计信息"""
        bbox = self.get_bounding_box()
        volume = self.get_volume()
        area = self.get_surface_area()
        weight = volume * material_density
        
        # 打印时间估算
        if bbox:
            perimeter = 2 * (bbox['size'][0] + bbox['size'][1])
            layers = bbox['size'][2] / layer_height
            infill_volume = volume * (infill / 100)
            
            print_speed = 50  # mm/s
            nozzle_diameter = 0.4  # mm
            
            shell_time = (perimeter * layers) / print_speed / 60
            infill_time = (infill_volume * 1000) / (print_speed * nozzle_diameter * layer_height) / 60
            total_time = shell_time + infill_time
        else:
            total_time = 0
        
        return {
            'filepath': self.filepath,
            'filename': os.path.basename(self.filepath),
            'format': 'Binary STL' if self.is_binary else 'ASCII STL',
            'triangles': len(self.triangles),
            'vertices': len(self.vertices),
            'bounding_box_mm': bbox['size'] if bbox else None,
            'volume_cm3': round(volume, 3),
            'surface_area_cm2': round(area, 3),
            'weight_g': round(weight, 2),
            'print_time_min': round(total_time, 1),
            'print_time_hours': round(total_time / 60, 2),
            'material_density': material_density,
            'layer_height_mm': layer_height,
            'infill_percent': infill
        }
    
    def __repr__(self):
        return f"<STLModel: {len(self.triangles)} triangles>"


def parse_stl(filepath):
    """解析 STL 文件并返回模型对象"""
    model = STLModel()
    model.load(filepath)
    return model
