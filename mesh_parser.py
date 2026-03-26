#!/usr/bin/env python3
"""
3D 网格文件解析器 - 基于 trimesh
支持格式：STL, OBJ, PLY, GLTF, GLB, FBX, DAE, 3DS 等
"""

import os
import trimesh


class MeshModel:
    """3D 网格模型类"""
    
    def __init__(self):
        self.mesh = None
        self.filepath = ""
        self.format = ""
    
    def load(self, filepath):
        """加载 3D 模型文件（自动检测格式）"""
        self.filepath = filepath
        ext = os.path.splitext(filepath)[1].lower()
        
        # trimesh 自动检测格式
        self.mesh = trimesh.load(filepath)
        
        # 处理多网格文件（如 GLTF 可能有多个 mesh）
        if isinstance(self.mesh, trimesh.Scene):
            # 合并所有网格
            meshes = [g for g in self.mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
            if meshes:
                self.mesh = trimesh.util.concatenate(meshes)
            else:
                raise ValueError("文件中没有找到有效的 3D 网格")
        
        self.format = ext.upper().replace('.', '')
        return self
    
    def get_bounding_box(self):
        """获取边界盒（mm）"""
        if self.mesh is None:
            return None
        
        bounds = self.mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        size = bounds[1] - bounds[0]
        
        # trimesh 默认单位可能是米，转换为 mm
        if size.max() < 1:  # 如果最大尺寸小于 1，可能是米
            size = size * 1000
        
        return size
    
    def get_volume(self):
        """获取体积（cm³）"""
        if self.mesh is None:
            return 0.0
        
        volume = abs(self.mesh.volume)
        
        # 如果体积太小，可能是米单位，转换为 mm³ 再转 cm³
        if volume < 0.001:
            volume = volume * 1e9  # m³ → mm³
        
        # mm³ → cm³
        return volume / 1000.0
    
    def get_surface_area(self):
        """获取表面积（cm²）"""
        if self.mesh is None:
            return 0.0
        
        area = self.mesh.area
        
        # 如果面积太小，可能是米单位
        if area < 0.01:
            area = area * 1e6  # m² → mm²
        
        # mm² → cm²
        return area / 100.0
    
    def get_stats(self, material_density=1.24, layer_height=0.2, infill=20):
        """获取完整统计信息"""
        bbox = self.get_bounding_box()
        volume = self.get_volume()
        area = self.get_surface_area()
        weight = volume * material_density
        
        # 打印时间估算（简化版）
        if bbox is not None and bbox.max() > 0:
            perimeter = 2 * (bbox[0] + bbox[1])
            layers = bbox[2] / layer_height
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
            'format': self.format,
            'triangles': len(self.mesh.faces) if self.mesh is not None else 0,
            'vertices': len(self.mesh.vertices) if self.mesh is not None else 0,
            'bounding_box_mm': bbox.tolist() if bbox is not None else None,
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
        if self.mesh is not None:
            return f"<MeshModel: {self.format} {len(self.mesh.faces)} faces>"
        return "<MeshModel: empty>"


def parse_mesh(filepath):
    """解析 3D 网格文件并返回模型对象"""
    model = MeshModel()
    model.load(filepath)
    return model


# 支持的格式列表
SUPPORTED_FORMATS = [
    '.stl', '.obj', '.ply', '.gltf', '.glb', 
    '.fbx', '.dae', '.3ds', '.off', '.wrl'
]


def is_supported_format(filepath):
    """检查文件格式是否支持"""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_FORMATS


def get_supported_formats_info():
    """获取支持的格式信息"""
    return {
        'STL': '3D 打印标准格式',
        'OBJ': 'Wavefront 3D 模型',
        'PLY': '多边形文件格式',
        'GLTF/GLB': 'Web 3D 格式',
        'FBX': 'Autodesk 交换格式',
        'DAE': 'Collada 交换格式',
        '3DS': '3D Studio 格式',
        '3MF': '3D 制造格式（需单独解析器）',
    }
