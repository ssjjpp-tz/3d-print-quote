#!/usr/bin/env python3
"""
3MF 文件解析器 - 纯 Python 实现
3MF = ZIP 压缩包 + XML 模型数据
"""

import zipfile
import xml.etree.ElementTree as ET
import math
import os


class ThreeMFModel:
    """3MF 模型类"""
    
    def __init__(self):
        self.vertices = []
        self.triangles = []  # 索引三元组 (v1, v2, v3)
        self.metadata = {}
        self.base_unit = 'millimeter'
        self.filepath = ""
        self.file_structure = []
    
    def load(self, filepath):
        """加载 3MF 文件"""
        self.filepath = filepath
        
        if not zipfile.is_zipfile(filepath):
            raise ValueError("不是有效的 3MF 文件（不是 ZIP 格式）")
        
        with zipfile.ZipFile(filepath, 'r') as zf:
            self.file_structure = zf.namelist()
            
            # 读取 3D 模型数据
            if '3D/3dmodel.model' in zf.namelist():
                model_xml = zf.read('3D/3dmodel.model')
                self._parse_model_xml(model_xml)
            
            # 读取元数据
            for name in zf.namelist():
                if name.startswith('Metadata/'):
                    try:
                        content = zf.read(name).decode('utf-8')
                        self.metadata[name] = content
                    except:
                        pass
        
        return self
    
    def _parse_model_xml(self, xml_data):
        """解析 3D 模型 XML"""
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            raise ValueError(f"XML 解析失败：{e}")
        
        # 尝试多种命名空间
        namespaces = [
            {'3mf': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'},
            {'': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'},
            {}  # 无命名空间
        ]
        
        for ns in namespaces:
            prefix = list(ns.keys())[0] if ns else ''
            
            # 查找 resources
            if prefix:
                resources = root.find(f'.//{prefix}:resources', ns)
            else:
                resources = root.find('.//resources')
            
            if resources is not None:
                self._parse_resources(resources, prefix)
                break
        
        # 获取单位
        root_elem = root
        for attr in ['unit', '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}unit']:
            if root.get(attr):
                self.base_unit = root.get(attr)
                break
    
    def _parse_resources(self, resources, prefix):
        """解析 resources 元素"""
        # 查找所有 mesh 元素
        if prefix:
            xpath = f'.//{prefix}:mesh'
        else:
            xpath = './/mesh'
        
        for mesh in resources.iter():
            if mesh.tag.endswith('mesh') or mesh.tag == 'mesh':
                # 解析顶点
                if prefix:
                    vertices_elem = mesh.find(f'.//{prefix}:vertices', {prefix: 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'})
                else:
                    vertices_elem = mesh.find('.//vertices')
                
                if vertices_elem is not None:
                    for v in vertices_elem.findall('.//vertex'):
                        try:
                            x = float(v.get('x', 0))
                            y = float(v.get('y', 0))
                            z = float(v.get('z', 0))
                            self.vertices.append((x, y, z))
                        except:
                            pass
                
                # 解析三角形
                if prefix:
                    triangles_elem = mesh.find(f'.//{prefix}:triangles', {prefix: 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'})
                else:
                    triangles_elem = mesh.find('.//triangles')
                
                if triangles_elem is not None:
                    for t in triangles_elem.findall('.//triangle'):
                        try:
                            v1 = int(t.get('v1', 0))
                            v2 = int(t.get('v2', 0))
                            v3 = int(t.get('v3', 0))
                            self.triangles.append((v1, v2, v3))
                        except:
                            pass
    
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
    
    def get_volume_estimate(self):
        """估算体积（3MF 需要重建三角形顶点）"""
        if not self.vertices or not self.triangles:
            return 0.0
        
        volume = 0.0
        for v1_idx, v2_idx, v3_idx in self.triangles:
            if v1_idx < len(self.vertices) and v2_idx < len(self.vertices) and v3_idx < len(self.vertices):
                v1 = self.vertices[v1_idx]
                v2 = self.vertices[v2_idx]
                v3 = self.vertices[v3_idx]
                
                vol = (v1[0] * (v2[1] * v3[2] - v3[1] * v2[2]) -
                       v1[1] * (v2[0] * v3[2] - v3[0] * v2[2]) +
                       v1[2] * (v2[0] * v3[1] - v3[0] * v2[1])) / 6.0
                volume += vol
        
        return abs(volume) / 1000.0  # mm³ → cm³
    
    def get_surface_area_estimate(self):
        """估算表面积"""
        if not self.vertices or not self.triangles:
            return 0.0
        
        area = 0.0
        for v1_idx, v2_idx, v3_idx in self.triangles:
            if v1_idx < len(self.vertices) and v2_idx < len(self.vertices) and v3_idx < len(self.vertices):
                v1 = self.vertices[v1_idx]
                v2 = self.vertices[v2_idx]
                v3 = self.vertices[v3_idx]
                
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
        volume = self.get_volume_estimate()
        area = self.get_surface_area_estimate()
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
            'format': '3MF',
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
            'infill_percent': infill,
            'unit': self.base_unit,
            'metadata_count': len(self.metadata),
            'file_count': len(self.file_structure)
        }
    
    def __repr__(self):
        return f"<ThreeMFModel: {len(self.vertices)} vertices, {len(self.triangles)} triangles>"


def parse_3mf(filepath):
    """解析 3MF 文件并返回模型对象"""
    model = ThreeMFModel()
    model.load(filepath)
    return model
