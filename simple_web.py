#!/usr/bin/env python3
"""
3D Print Quote - 简易 Web 服务（无需 Flask，纯 Python）
使用 http.server + CGI
"""

import os
import sys
import json
import tempfile
import cgi
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# 添加技能目录到路径
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SKILL_DIR)

from stl_parser import STLModel
from threemf_parser import ThreeMFModel
from quote_engine import calculate_quote, load_config, get_materials_list

# 上传目录
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='3d_quote_')

# HTML 页面
HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🖨️ 3D 打印自动报价</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}
.container{max-width:700px;margin:0 auto;background:#fff;border-radius:20px;padding:30px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
h1{text-align:center;color:#333;margin-bottom:10px}
.subtitle{text-align:center;color:#666;margin-bottom:25px}
.upload-area{border:3px dashed #667eea;border-radius:15px;padding:30px;text-align:center;background:#f8f9ff;cursor:pointer;margin-bottom:20px}
.upload-area:hover{background:#f0f2ff}
.upload-icon{font-size:40px;margin-bottom:10px}
#fileInput{display:none}
.form-group{margin:15px 0}
label{display:block;margin-bottom:5px;color:#333;font-weight:600}
select,input{width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:15px}
.btn{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:600;cursor:pointer}
.btn:hover{opacity:0.9}
.result{margin-top:25px;padding:20px;background:#f8f9ff;border-radius:12px;display:none}
.result h2{color:#667eea;margin-bottom:15px;border-bottom:2px solid #667eea;padding-bottom:10px}
.info-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:20px}
.info-card{background:#fff;padding:12px;border-radius:8px}
.info-card .label{color:#999;font-size:11px}
.info-card .value{color:#333;font-size:16px;font-weight:600}
.price-box{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:20px;border-radius:12px;text-align:center;margin-top:15px}
.price-value{font-size:36px;font-weight:bold}
.cost-breakdown{margin-top:15px;background:#fff;padding:15px;border-radius:8px}
.cost-item{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee}
.cost-item:last-child{border-bottom:none;font-weight:600}
.error{background:#fff0f0;color:#d63031;padding:12px;border-radius:8px;margin-top:15px;display:none}
.loading{text-align:center;padding:20px;display:none}
.spinner{border:3px solid #f3f3f3;border-top:3px solid #667eea;border-radius:50%;width:30px;height:30px;animation:spin 1s linear infinite;margin:0 auto 10px}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.file-info{background:#fff;padding:10px;border-radius:8px;margin-bottom:15px;display:none}
</style>
</head>
<body>
<div class="container">
<h1>🖨️ 3D 打印自动报价</h1>
<p class="subtitle">上传 STL/3MF 文件，立即获取报价</p>

<form id="uploadForm" enctype="multipart/form-data">
<div class="upload-area" onclick="document.getElementById('fileInput').click()">
<div class="upload-icon">📦</div>
<div>点击选择文件或拖拽到此处</div>
<div style="color:#999;font-size:13px;margin-top:8px">支持：STL, 3MF | 最大 50MB</div>
<input type="file" id="fileInput" name="file" accept=".stl,.3mf">
</div>

<div class="file-info" id="fileInfo"></div>

<div class="form-group">
<label>材料</label>
<select id="material" name="material">
<optgroup label="🧪 非金属材料">
<option value="PLA">PLA - 常用环保 (¥0.08/g)</option>
<option value="ABS">ABS - 高强度 (¥0.10/g)</option>
<option value="PETG">PETG - 耐候性好 (¥0.12/g)</option>
<option value="Nylon">尼龙 - 耐磨 (¥0.25/g)</option>
<option value="TPU">TPU - 柔性 (¥0.18/g)</option>
<option value="Resin">树脂 - 光固化 (¥0.15/g)</option>
<option value="PC">PC - 高透明 (¥0.20/g)</option>
<option value="ASA">ASA - 抗 UV(¥0.22/g)</option>
<option value="PEEK">PEEK - 耐高温特种 (¥2.80/g)</option>
</optgroup>
<optgroup label="🔩 金属材料">
<option value="Aluminum">铝合金 - 轻质 (¥0.35/g)</option>
<option value="StainlessSteel">不锈钢 - 耐腐蚀 (¥0.80/g)</option>
<option value="Steel">碳钢 - 高强度 (¥0.45/g)</option>
<option value="Titanium">钛合金 - 高强轻质 (¥3.50/g)</option>
<option value="Copper">紫铜 - 导电好 (¥0.90/g)</option>
<option value="Brass">黄铜 - 易加工 (¥0.65/g)</option>
</optgroup>
</select>
</div>

<div class="form-group">
<label>利润率倍数</label>
<input type="number" id="profit" name="profit" value="2.0" step="0.1" min="1.0">
<div style="color:#999;font-size:12px;margin-top:3px">2.0=100% 利润</div>
</div>

<button type="submit" class="btn">🚀 计算报价</button>
</form>

<div class="loading" id="loading"><div class="spinner"></div>分析中...</div>
<div class="error" id="error"></div>

<div class="result" id="result">
<h2>📊 分析结果</h2>
<div class="info-grid">
<div class="info-card"><div class="label">格式</div><div class="value" id="rFormat">-</div></div>
<div class="info-card"><div class="label">三角形</div><div class="value" id="rTriangles">-</div></div>
<div class="info-card"><div class="label">尺寸</div><div class="value" id="rSize">-</div></div>
<div class="info-card"><div class="label">体积</div><div class="value" id="rVolume">-</div></div>
<div class="info-card"><div class="label">重量</div><div class="value" id="rWeight">-</div></div>
<div class="info-card"><div class="label">时间</div><div class="value" id="rTime">-</div></div>
</div>
<div class="price-box"><div style="font-size:13px;opacity:0.9">建议售价</div><div class="price-value">¥<span id="rPrice">0.00</span></div></div>
<div class="cost-breakdown">
<div class="cost-item"><span>材料费</span><span id="cMaterial">¥0.00</span></div>
<div class="cost-item"><span>机器费</span><span id="cMachine">¥0.00</span></div>
<div class="cost-item"><span>人工费</span><span id="cLabor">¥0.00</span></div>
<div class="cost-item"><span>总成本</span><span id="cTotal">¥0.00</span></div>
</div>
</div>
</div>

<script>
const fileInput=document.getElementById('fileInput');
const fileInfo=document.getElementById('fileInfo');
fileInput.addEventListener('change',e=>{
if(e.target.files[0]){
const f=e.target.files[0];
fileInfo.innerHTML='<b>📄 '+f.name+'</b><br>'+(f.size/1024).toFixed(1)+' KB';
fileInfo.style.display='block';
}
});

document.getElementById('uploadForm').addEventListener('submit',async e=>{
e.preventDefault();
const file=fileInput.files[0];
if(!file){showError('请选择文件');return;}

const fd=new FormData();
fd.append('file',file);
fd.append('material',document.getElementById('material').value);
fd.append('profit',document.getElementById('profit').value);

document.getElementById('loading').style.display='block';
document.getElementById('result').style.display='none';
document.getElementById('error').style.display='none';

try{
const res=await fetch('/api/quote',{method:'POST',body:fd});
const data=await res.json();
if(!res.ok)throw new Error(data.error);
showResult(data);
}catch(err){showError(err.message);}
finally{document.getElementById('loading').style.display='none';}
});

function showResult(d){
document.getElementById('rFormat').textContent=d.stats.format;
document.getElementById('rTriangles').textContent=d.stats.triangles.toLocaleString();
if(d.stats.bounding_box_mm){
const[x,y,z]=d.stats.bounding_box_mm;
document.getElementById('rSize').textContent=x.toFixed(1)+' × '+y.toFixed(1)+' × '+z.toFixed(1)+' mm';
}else document.getElementById('rSize').textContent='-';
document.getElementById('rVolume').textContent=d.stats.volume_cm3.toFixed(2)+' cm³';
document.getElementById('rWeight').textContent=d.quote.weight_g.toFixed(2)+' g';
document.getElementById('rTime').textContent=d.quote.print_time_hours.toFixed(1)+' h';
document.getElementById('rPrice').textContent=d.quote.price.toFixed(2);
document.getElementById('cMaterial').textContent='¥'+d.quote.material_cost.toFixed(2);
document.getElementById('cMachine').textContent='¥'+d.quote.machine_cost.toFixed(2);
document.getElementById('cLabor').textContent='¥'+d.quote.labor_cost.toFixed(2);
document.getElementById('cTotal').textContent='¥'+d.quote.total_cost.toFixed(2);
document.getElementById('result').style.display='block';
}
function showError(m){
document.getElementById('error').textContent='❌ '+m;
document.getElementById('error').style.display='block';
}
</script>
</body>
</html>'''

class QuoteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/materials':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            materials = get_materials_list(load_config())
            self.wfile.write(json.dumps(materials, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/quote':
            try:
                # 解析 multipart 表单
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    self.send_error(400, 'Invalid content type')
                    return
                
                # 获取 boundary
                boundary = content_type.split('boundary=')[1] if 'boundary=' in content_type else None
                if not boundary:
                    self.send_error(400, 'No boundary')
                    return
                
                # 读取数据
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # 保存到临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.upload')
                temp_file.write(post_data)
                temp_file.close()
                
                # 解析表单
                form = cgi.FieldStorage(
                    fp=open(temp_file.name, 'rb'),
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
                )
                
                # 获取文件
                if 'file' not in form:
                    self.send_json({'error': '没有上传文件'}, 400)
                    return
                
                file_item = form['file']
                if not file_item.filename:
                    self.send_json({'error': '文件名为空'}, 400)
                    return
                
                filename = file_item.filename.lower()
                if not (filename.endswith('.stl') or filename.endswith('.3mf')):
                    self.send_json({'error': '只支持 STL 和 3MF 文件'}, 400)
                    return
                
                # 保存上传的文件
                ext = '.stl' if filename.endswith('.stl') else '.3mf'
                save_path = os.path.join(UPLOAD_FOLDER, 'upload' + ext)
                with open(save_path, 'wb') as f:
                    f.write(file_item.file.read())
                
                # 获取参数
                material = form.getfirst('material', 'PLA')
                profit = float(form.getfirst('profit', '2.0'))
                
                # 分析模型
                if ext == '.stl':
                    model = STLModel()
                    model.load(save_path)
                else:
                    model = ThreeMFModel()
                    model.load(save_path)
                
                stats = model.get_stats()
                
                # 计算报价
                config = load_config()
                quote = calculate_quote(stats, material, profit, config)
                
                # 清理
                os.unlink(temp_file.name)
                
                self.send_json({'success': True, 'stats': stats, 'quote': quote})
                
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

def run_server(port=5000):
    server = HTTPServer(('0.0.0.0', port), QuoteHandler)
    print("=" * 60)
    print("🖨️  3D 打印自动报价服务（纯 Python 版）")
    print("=" * 60)
    print(f"📁 上传目录：{UPLOAD_FOLDER}")
    print(f"🌐 访问地址：http://localhost:{port}")
    print(f"📎 支持格式：STL, 3MF")
    print("=" * 60)
    print("按 Ctrl+C 停止服务")
    server.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server(port)
