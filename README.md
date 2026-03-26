# 🖨️ 3D Print Quote - 3D 打印自动报价系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey.svg)](https://flask.palletsprojects.com/)

**纯 Python 实现的 3D 打印自动报价系统** - 上传 STL/3MF 模型文件，自动分析几何信息、计算材料成本、估算打印时间，立即获取精准报价。

---

## ✨ 功能特性

### 🎯 核心功能
- ✅ **STL 解析** - Binary 和 ASCII 格式自动检测
- ✅ **3MF 解析** - ZIP+XML 结构完整支持
- ✅ **体积计算** - 散度定理精确计算
- ✅ **表面积** - 三角形面积累加
- ✅ **边界盒** - 长宽高尺寸分析
- ✅ **重量估算** - 根据材料密度自动计算
- ✅ **打印时间** - 层高、填充率可配置
- ✅ **成本计算** - 材料 + 机器 + 人工
- ✅ **利润率** - 可配置倍数
- ✅ **最低起印价** - 保护小单成本

### 🌐 Web 界面
- ✅ 响应式设计 - 支持 PC 和移动端
- ✅ 拖拽上传 - 支持文件拖放
- ✅ 实时计算 - 秒级响应
- ✅ 成本明细 - 透明展示
- ✅ 材料对比 - 6 种常用材料

### 🔌 API 接口
- ✅ RESTful API
- ✅ CORS 支持
- ✅ 健康检查
- ✅ JSON 响应

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd 3d-print-quote
pip3 install -r requirements.txt
```

### 2. 启动服务

```bash
python3 web_server.py
```

### 3. 访问界面

打开浏览器访问：**http://localhost:5000**

---

## 📋 支持材料

| 材料 | 密度 | 单价 | 特点 |
|------|------|------|------|
| **PLA** | 1.24 g/cm³ | ¥0.08/g | 常用环保，易打印 |
| **ABS** | 1.04 g/cm³ | ¥0.10/g | 高强度，耐高温 |
| **PETG** | 1.27 g/cm³ | ¥0.12/g | 耐候性好，韧性佳 |
| **尼龙** | 1.14 g/cm³ | ¥0.25/g | 耐磨，机械性能好 |
| **TPU** | 1.21 g/cm³ | ¥0.18/g | 柔性，可弯曲 |
| **树脂** | 1.10 g/cm³ | ¥0.15/g | 光固化，高精度 |

---

## 🔧 配置说明

编辑 `config.json` 自定义参数：

```json
{
  "machine_cost_per_hour": 5.0,    // 机器成本 元/小时
  "labor_cost_base": 10.0,         // 基础人工费
  "default_profit_margin": 2.0,    // 默认利润率（倍数）
  "min_price": 15.0,               // 最低起印价
  "default_layer_height": 0.2,     // 默认层高 (mm)
  "default_infill": 20             // 默认填充率 (%)
}
```

---

## 📡 API 使用

### 上传文件获取报价

```bash
curl -X POST http://localhost:5000/api/quote \
  -F "file=@model.stl" \
  -F "material=PLA" \
  -F "profit=2.0"
```

**响应示例：**
```json
{
  "success": true,
  "stats": {
    "format": "Binary STL",
    "triangles": 12458,
    "bounding_box_mm": [85.2, 42.5, 120.0],
    "volume_cm3": 45.82
  },
  "quote": {
    "weight_g": 56.82,
    "print_time_hours": 3.1,
    "material_cost": 4.55,
    "machine_cost": 15.50,
    "labor_cost": 10.00,
    "total_cost": 30.05,
    "price": 60.10
  }
}
```

### 获取材料列表

```bash
curl http://localhost:5000/api/materials
```

### 健康检查

```bash
curl http://localhost:5000/health
```

---

## 💻 Python 代码集成

```python
from stl_parser import STLModel
from quote_engine import calculate_quote, load_config

# 分析 STL 模型
model = STLModel()
model.load('model.stl')
stats = model.get_stats()

# 计算报价
config = load_config()
quote = calculate_quote(stats, material='PLA', profit_margin=2.0, config=config)

print(f"文件：model.stl")
print(f"重量：{quote['weight_g']:.2f} g")
print(f"打印时间：{quote['print_time_hours']:.1f} 小时")
print(f"建议售价：¥{quote['price']:.2f}")
```

---

## 📁 项目结构

```
3d-print-quote/
├── web_server.py           # Web 服务器 (Flask)
├── simple_web.py           # 简化版 Web 服务
├── admin_server.py         # 管理后台
├── main.py                 # 命令行入口
├── stl_parser.py           # STL 解析器
├── threemf_parser.py       # 3MF 解析器
├── quote_engine.py         # 报价引擎
├── weixin_integration.py   # 微信集成
├── config.json             # 配置文件
├── requirements.txt        # Python 依赖
├── service.sh              # 系统服务脚本
├── 3d-quote.service        # systemd 服务配置
└── README.md               # 本文档
```

---

## 🔐 部署建议

### 生产环境部署

1. **使用 Gunicorn**
```bash
pip3 install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_server:app
```

2. **Systemd 服务**
```bash
sudo cp 3d-quote.service /etc/systemd/system/
sudo systemctl enable 3d-quote
sudo systemctl start 3d-quote
```

3. **Nginx 反向代理**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🧪 测试

### 命令行测试

```bash
# 分析单个文件
python3 main.py model.stl

# 指定材料
python3 main.py model.stl ABS

# 批量处理
python3 main.py *.stl

# 查看材料列表
python3 main.py --materials
```

---

## 📊 输出示例

```
============================================================
📦 3D 打印报价分析
============================================================
文件：model.stl
大小：256.3 KB
格式：Binary STL

📐 几何信息:
   三角形：12,458
   尺寸：85.2 × 42.5 × 120.0 mm

⚖️ 物理属性 (PLA):
   体积：45.82 cm³
   重量：56.82 g

⏱️ 打印估算:
   时间：185 分钟 (3.1 小时)

💰 成本估算:
   材料费：¥4.55
   机器费：¥15.50
   人工费：¥10.00
   总成本：¥30.05
   建议售价：¥60.10
============================================================
```

---

## 🛠️ 技术细节

### STL 解析
- 80 字节文件头 + 4 字节计数 + 50 字节/三角形
- ASCII 检测：以 `solid` 开头
- 体积计算：散度定理（signed volume）

### 3MF 解析
- ZIP 压缩包格式
- 解析 `3D/3dmodel.model` XML
- 支持顶点索引三角形

### 打印时间估算
```python
# 外壳时间
shell_time = perimeter × layers / print_speed

# 填充时间
infill_time = infill_volume / (speed × nozzle_diameter × layer_height)

# 总时间
total_time = shell_time + infill_time + setup_time
```

---

##  更新日志

### v1.1.0 (2026-03-27)
- ✨ 添加 CORS 支持
- ✨ 新增健康检查接口 `/health`
- ✨ 新增版本信息接口 `/api/version`
- 🎨 优化 Web 界面响应速度
- 🐛 修复 3MF 文件解析 bug

### v1.0.0 (2026-03-25)
- 🎉 首次发布
- ✅ 完整 STL/3MF 解析
- ✅ Web 界面
- ✅ 微信集成

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👤 作者

**小龙女二代** 🐉

- GitHub: [@ssjjpp-tz](https://github.com/ssjjpp-tz)
- 项目地址：https://github.com/ssjjpp-tz/3d-print-quote

---

## 🙏 致谢

感谢使用 3D Print Quote！如果这个项目对你有帮助，请给一个 ⭐️ Star！
