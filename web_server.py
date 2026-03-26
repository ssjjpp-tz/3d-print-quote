#!/usr/bin/env python3
"""
3D Print Quote - Web 上传服务
访问 http://localhost:5000 上传文件并获取报价
"""

import os
import sys
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename

# 添加技能目录到路径
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from stl_parser import STLModel
from threemf_parser import ThreeMFModel
from quote_engine import calculate_quote, format_quote_report, load_config, get_materials_list

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 最大 50MB

# CORS 支持
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 上传目录
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='3d_quote_')
ALLOWED_EXTENSIONS = {'stl', '3mf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_file(filepath):
    """分析模型文件"""
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
        raise ValueError(f"不支持的格式：{ext}")


# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🖨️ 3D 打印自动报价</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8ebff;
        }
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .upload-text {
            color: #666;
            font-size: 16px;
        }
        .upload-hint {
            color: #999;
            font-size: 14px;
            margin-top: 10px;
        }
        #fileInput { display: none; }
        
        .form-group {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        select, input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .result {
            margin-top: 30px;
            padding: 25px;
            background: #f8f9ff;
            border-radius: 15px;
            display: none;
        }
        .result.show {
            display: block;
            animation: slideIn 0.5s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .result h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #667eea;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .info-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .info-card .label {
            color: #999;
            font-size: 12px;
            margin-bottom: 5px;
        }
        .info-card .value {
            color: #333;
            font-size: 18px;
            font-weight: 600;
        }
        
        .price-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin-top: 20px;
        }
        .price-label {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .price-value {
            font-size: 48px;
            font-weight: bold;
        }
        .price-currency {
            font-size: 24px;
            vertical-align: super;
        }
        
        .cost-breakdown {
            margin-top: 20px;
            background: white;
            padding: 20px;
            border-radius: 10px;
        }
        .cost-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .cost-item:last-child {
            border-bottom: none;
            font-weight: 600;
            padding-top: 15px;
            margin-top: 10px;
            border-top: 2px solid #667eea;
        }
        
        .error {
            background: #fff0f0;
            color: #d63031;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        .error.show {
            display: block;
        }
        
        .loading {
            text-align: center;
            padding: 30px;
            display: none;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .materials-info {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #eee;
        }
        .materials-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .materials-table th, .materials-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        .materials-table th {
            background: #f8f9ff;
            color: #667eea;
        }
        
        .file-info {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .file-info.show {
            display: block;
        }
        .file-name {
            font-weight: 600;
            color: #333;
            word-break: break-all;
        }
        .file-size {
            color: #999;
            font-size: 14px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖨️ 3D 打印自动报价</h1>
        <p class="subtitle">上传 STL 或 3MF 文件，立即获取报价</p>
        
        <form id="uploadForm">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📦</div>
                <div class="upload-text">点击选择文件或拖拽到此处</div>
                <div class="upload-hint">支持格式：STL, 3MF | 最大 50MB</div>
                <input type="file" id="fileInput" name="file" accept=".stl,.3mf">
            </div>
            
            <div class="file-info" id="fileInfo">
                <div class="file-name" id="fileName"></div>
                <div class="file-size" id="fileSize"></div>
            </div>
            
            <div class="form-group">
                <label for="material">选择材料</label>
                <select id="material" name="material">
                    <option value="PLA">PLA - 常用环保材料 (¥0.08/g)</option>
                    <option value="ABS">ABS - 高强度 (¥0.10/g)</option>
                    <option value="PETG">PETG - 耐候性好 (¥0.12/g)</option>
                    <option value="Nylon">尼龙 - 耐磨 (¥0.25/g)</option>
                    <option value="TPU">TPU - 柔性材料 (¥0.18/g)</option>
                    <option value="Resin">树脂 - 光固化 (¥0.15/g)</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="profit">利润率倍数</label>
                <input type="number" id="profit" name="profit" value="2.0" step="0.1" min="1.0">
                <div style="color: #999; font-size: 14px; margin-top: 5px;">
                    2.0 = 100% 利润 | 1.5 = 50% 利润 | 3.0 = 200% 利润
                </div>
            </div>
            
            <button type="submit" class="btn" id="submitBtn">🚀 开始计算报价</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div>正在分析模型，请稍候...</div>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="result" id="result">
            <h2>📊 分析结果</h2>
            
            <div class="info-grid">
                <div class="info-card">
                    <div class="label">文件格式</div>
                    <div class="value" id="resFormat">-</div>
                </div>
                <div class="info-card">
                    <div class="label">三角形</div>
                    <div class="value" id="resTriangles">-</div>
                </div>
                <div class="info-card">
                    <div class="label">尺寸</div>
                    <div class="value" id="resSize">-</div>
                </div>
                <div class="info-card">
                    <div class="label">体积</div>
                    <div class="value" id="resVolume">-</div>
                </div>
                <div class="info-card">
                    <div class="label">重量</div>
                    <div class="value" id="resWeight">-</div>
                </div>
                <div class="info-card">
                    <div class="label">打印时间</div>
                    <div class="value" id="resTime">-</div>
                </div>
            </div>
            
            <div class="price-box">
                <div class="price-label">建议售价</div>
                <div class="price-value">
                    <span class="price-currency">¥</span><span id="resPrice">0.00</span>
                </div>
            </div>
            
            <div class="cost-breakdown">
                <h3 style="margin-bottom: 15px; color: #333;">💰 成本明细</h3>
                <div class="cost-item">
                    <span>材料费</span>
                    <span id="costMaterial">¥0.00</span>
                </div>
                <div class="cost-item">
                    <span>机器费</span>
                    <span id="costMachine">¥0.00</span>
                </div>
                <div class="cost-item">
                    <span>人工费</span>
                    <span id="costLabor">¥0.00</span>
                </div>
                <div class="cost-item">
                    <span>总成本</span>
                    <span id="costTotal">¥0.00</span>
                </div>
            </div>
        </div>
        
        <div class="materials-info">
            <h3 style="color: #333; margin-bottom: 10px;">📋 材料说明</h3>
            <table class="materials-table">
                <thead>
                    <tr>
                        <th>材料</th>
                        <th>密度</th>
                        <th>单价</th>
                        <th>特点</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>PLA</strong></td>
                        <td>1.24 g/cm³</td>
                        <td>¥0.08/g</td>
                        <td>常用环保，易打印</td>
                    </tr>
                    <tr>
                        <td><strong>ABS</strong></td>
                        <td>1.04 g/cm³</td>
                        <td>¥0.10/g</td>
                        <td>高强度，耐高温</td>
                    </tr>
                    <tr>
                        <td><strong>PETG</strong></td>
                        <td>1.27 g/cm³</td>
                        <td>¥0.12/g</td>
                        <td>耐候性好，韧性佳</td>
                    </tr>
                    <tr>
                        <td><strong>尼龙</strong></td>
                        <td>1.14 g/cm³</td>
                        <td>¥0.25/g</td>
                        <td>耐磨，机械性能好</td>
                    </tr>
                    <tr>
                        <td><strong>TPU</strong></td>
                        <td>1.21 g/cm³</td>
                        <td>¥0.18/g</td>
                        <td>柔性，可弯曲</td>
                    </tr>
                    <tr>
                        <td><strong>树脂</strong></td>
                        <td>1.10 g/cm³</td>
                        <td>¥0.15/g</td>
                        <td>光固化，高精度</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        
        // 点击上传
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // 文件选择
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                showFileInfo(e.target.files[0]);
            }
        });
        
        // 拖拽
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                showFileInfo(e.dataTransfer.files[0]);
            }
        });
        
        function showFileInfo(file) {
            fileName.textContent = '📄 ' + file.name;
            fileSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
            fileInfo.classList.add('show');
        }
        
        // 提交
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const file = fileInput.files[0];
            if (!file) {
                showError('请选择文件');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('material', document.getElementById('material').value);
            formData.append('profit', document.getElementById('profit').value);
            
            // 显示加载
            loading.classList.add('show');
            result.classList.remove('show');
            error.classList.remove('show');
            
            try {
                const response = await fetch('/api/quote', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || '分析失败');
                }
                
                showResult(data);
            } catch (err) {
                showError(err.message);
            } finally {
                loading.classList.remove('show');
            }
        });
        
        function showResult(data) {
            // 几何信息
            document.getElementById('resFormat').textContent = data.stats.format;
            document.getElementById('resTriangles').textContent = data.stats.triangles.toLocaleString();
            
            if (data.stats.bounding_box_mm) {
                const [x, y, z] = data.stats.bounding_box_mm;
                document.getElementById('resSize').textContent = `${x.toFixed(1)} × ${y.toFixed(1)} × ${z.toFixed(1)} mm`;
            } else {
                document.getElementById('resSize').textContent = '-';
            }
            
            document.getElementById('resVolume').textContent = data.stats.volume_cm3.toFixed(2) + ' cm³';
            document.getElementById('resWeight').textContent = data.quote.weight_g.toFixed(2) + ' g';
            document.getElementById('resTime').textContent = data.quote.print_time_hours.toFixed(1) + ' 小时';
            
            // 价格
            document.getElementById('resPrice').textContent = data.quote.price.toFixed(2);
            
            // 成本明细
            document.getElementById('costMaterial').textContent = '¥' + data.quote.material_cost.toFixed(2);
            document.getElementById('costMachine').textContent = '¥' + data.quote.machine_cost.toFixed(2);
            document.getElementById('costLabor').textContent = '¥' + data.quote.labor_cost.toFixed(2);
            document.getElementById('costTotal').textContent = '¥' + data.quote.total_cost.toFixed(2);
            
            result.classList.add('show');
        }
        
        function showError(msg) {
            error.textContent = '❌ ' + msg;
            error.classList.add('show');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'service': '3d-print-quote'})

@app.route('/api/version')
def version():
    """版本信息"""
    return jsonify({
        'version': '1.1.0',
        'name': '3D Print Quote',
        'author': '小龙女二代'
    })

@app.route('/api/quote', methods=['POST'])
def api_quote():
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式，请上传 STL 或 3MF 文件'}), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 获取参数
        material = request.form.get('material', 'PLA')
        profit = float(request.form.get('profit', 2.0))
        
        # 分析模型
        stats = analyze_file(filepath)
        
        # 计算报价
        config = load_config()
        quote = calculate_quote(stats, material, profit, config)
        
        # 返回结果
        return jsonify({
            'success': True,
            'stats': stats,
            'quote': quote
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/materials')
def api_materials():
    """获取材料列表"""
    config = load_config()
    return jsonify(get_materials_list(config))

if __name__ == '__main__':
    import os
    
    # 从环境变量获取端口（Railway/Render 等平台使用）
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("🖨️  3D 打印自动报价服务")
    print("=" * 60)
    print(f"📁 上传目录：{UPLOAD_FOLDER}")
    print(f"🌐 访问地址：http://0.0.0.0:{port}")
    print(f"📎 支持格式：STL, 3MF")
    print(f"📏 最大文件：50 MB")
    print("=" * 60)
    
    # 启动服务
    app.run(host='0.0.0.0', port=port, debug=False)
