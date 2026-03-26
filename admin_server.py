#!/usr/bin/env python3
"""
3D Print Quote - 管理后台
配置价格参数、利润倍数、材料价格等
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import html

# 技能目录
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SKILL_DIR, 'config.json')

def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# 管理后台 HTML
ADMIN_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚙️ 3D 打印报价 - 管理后台</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f6fa;padding:20px}
.container{max-width:900px;margin:0 auto}
h1{color:#2c3e50;margin-bottom:10px}
.subtitle{color:#7f8c8d;margin-bottom:30px}
.card{background:#fff;border-radius:12px;padding:25px;margin-bottom:20px;box-shadow:0 2px 10px rgba(0,0,0,0.05)}
.card h2{color:#34495e;margin-bottom:20px;padding-bottom:10px;border-bottom:2px solid #3498db}
.form-group{margin:15px 0}
label{display:block;margin-bottom:8px;color:#2c3e50;font-weight:600}
input,select{width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:15px}
input:focus,select:focus{outline:none;border-color:#3498db}
.hint{color:#95a5a6;font-size:13px;margin-top:5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px}
.material-card{background:#f8f9fa;border:2px solid #e0e0e0;border-radius:10px;padding:15px}
.material-card h3{color:#2c3e50;margin-bottom:10px;font-size:16px}
.btn{background:#3498db;color:#fff;border:none;padding:12px 25px;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
.btn:hover{background:#2980b9}
.btn-success{background:#27ae60}
.btn-success:hover{background:#219a52}
.price-preview{background:#ecf0f1;padding:20px;border-radius:10px;margin-top:20px}
.price-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #bdc3c7}
.price-row:last-child{border-bottom:none;font-weight:600;font-size:18px;color:#2c3e50}
.alert{padding:15px;border-radius:8px;margin-bottom:20px}
.alert-success{background:#d4edda;color:#155724;border:1px solid #c3e6cb}
.alert-error{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}
.hidden{display:none}
</style>
</head>
<body>
<div class="container">
<h1>⚙️ 3D 打印报价 - 管理后台</h1>
<p class="subtitle">配置价格参数和利润倍数</p>

<div id="msg"></div>

<form id="configForm">
<!-- 基础价格 -->
<div class="card">
<h2>💰 基础价格构成</h2>
<div class="grid">
<div class="form-group">
<label>机器成本 (元/小时)</label>
<input type="number" id="machine_cost" step="0.1" min="0">
<div class="hint">3D 打印机运行成本，含电费、折旧</div>
</div>
<div class="form-group">
<label>基础人工费 (元)</label>
<input type="number" id="labor_cost" step="0.1" min="0">
<div class="hint">每个订单的基础人工处理成本</div>
</div>
<div class="form-group">
<label>最低起印价 (元)</label>
<input type="number" id="min_price" step="1" min="0">
<div class="hint">低于此价格按此价格收费</div>
</div>
<div class="form-group">
<label>默认利润率倍数</label>
<input type="number" id="default_profit" step="0.1" min="1.0">
<div class="hint">2.0 = 100% 利润，1.5 = 50% 利润</div>
</div>
</div>
</div>

<!-- 打印参数 -->
<div class="card">
<h2>🖨️ 打印参数</h2>
<div class="grid">
<div class="form-group">
<label>默认层高 (mm)</label>
<input type="number" id="layer_height" step="0.05" min="0.05">
<div class="hint">影响打印时间和表面质量</div>
</div>
<div class="form-group">
<label>默认填充率 (%)</label>
<input type="number" id="infill" step="5" min="0" max="100">
<div class="hint">影响材料用量和强度</div>
</div>
</div>
</div>

<!-- 材料价格 -->
<div class="card">
<h2>🧪 非金属材料</h2>
<div id="nonmetalMaterials" class="grid"></div>
</div>

<div class="card">
<h2>🔩 金属材料</h2>
<div id="metalMaterials" class="grid"></div>
</div>

<div class="card">
<h2>⚙️ 金属加工费用</h2>
<div class="grid">
<div class="form-group">
<label>CNC 开机费 (元)</label>
<input type="number" id="cnc_setup" step="1" min="0">
<div class="hint">金属加工固定成本</div>
</div>
<div class="form-group">
<label>CNC 加工费 (元/小时)</label>
<input type="number" id="cnc_hourly" step="1" min="0">
<div class="hint">数控机床运行成本</div>
</div>
<div class="form-group">
<label>阳极氧化 (元/cm²)</label>
<input type="number" id="anodizing" step="0.1" min="0">
<div class="hint">铝合金表面处理</div>
</div>
<div class="form-group">
<label>电镀 (元/cm²)</label>
<input type="number" id="plating" step="0.1" min="0">
<div class="hint">金属表面电镀</div>
</div>
<div class="form-group">
<label>喷漆 (元/cm²)</label>
<input type="number" id="painting" step="0.1" min="0">
<div class="hint">表面喷漆处理</div>
</div>
<div class="form-group">
<label>抛光 (元/cm²)</label>
<input type="number" id="polishing" step="0.1" min="0">
<div class="hint">表面抛光处理</div>
</div>
</div>
</div>

<div class="card">
<h2>📊 价格预览</h2>
<div class="price-preview">
<div class="price-row"><span>示例：10g PLA, 40 分钟</span><span></span></div>
<div class="price-row"><span>材料费</span><span id="preview_material">¥0.00</span></div>
<div class="price-row"><span>机器费</span><span id="preview_machine">¥0.00</span></div>
<div class="price-row"><span>人工费</span><span id="preview_labor">¥0.00</span></div>
<div class="price-row"><span>总成本</span><span id="preview_total">¥0.00</span></div>
<div class="price-row" style="background:#3498db;color:#fff;margin:10px -20px -20px;padding:15px 20px;border-radius:0 0 10px 10px">
<span>建议售价</span><span id="preview_price">¥0.00</span>
</div>
</div>
</div>

<button type="submit" class="btn btn-success" style="width:100%;padding:15px;font-size:18px">💾 保存配置</button>
</form>

<div class="card" style="margin-top:20px">
<h2>🔗 快速链接</h2>
<div style="display:flex;gap:15px;flex-wrap:wrap">
<a href="/" class="btn">🏠 报价前台</a>
<a href="/api/materials" class="btn" target="_blank">📋 材料 API</a>
</div>
</div>
</div>

<script>
let config = {};

// 加载配置
async function loadConfig(){
const res=await fetch('/admin/api/config');
config=await res.json();

document.getElementById('machine_cost').value=config.machine_cost_per_hour;
document.getElementById('labor_cost').value=config.labor_cost_base;
document.getElementById('min_price').value=config.min_price;
document.getElementById('default_profit').value=config.default_profit_margin;
document.getElementById('layer_height').value=config.default_layer_height;
document.getElementById('infill').value=config.default_infill;

// 材料分类
const categories={
nonmetal:['PLA','ABS','PETG','Nylon','TPU','Resin','PC','ASA','PEEK'],
metal:['Aluminum','StainlessSteel','Steel','Titanium','Copper','Brass']
};

// 渲染材料
function renderMaterials(category,elementId){
const container=document.getElementById(elementId);
let html='<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:15px">';
for(const key of category){
const val=config.materials[key];
if(!val)continue;
html+=`
<div class="material-card">
<h3>${val.name}</h3>
<div style="color:#95a5a6;font-size:12px;margin-bottom:10px">${key}</div>
<div class="form-group">
<label>密度 (g/cm³)</label>
<input type="number" step="0.01" name="mat_density_${key}" value="${val.density}">
</div>
<div class="form-group">
<label>单价 (元/g)</label>
<input type="number" step="${key==='Gold'?10:0.01}" name="mat_price_${key}" value="${val.price_per_g}">
</div>
<div class="form-group">
<label>描述</label>
<input type="text" name="mat_desc_${key}" value="${val.desc||''}">
</div>
</div>
`;
}
html+='</div>';
container.innerHTML=html;
}

renderMaterials(categories.nonmetal,'nonmetalMaterials');
renderMaterials(categories.metal,'metalMaterials');

// 金属加工费用
if(config.metal_processing){
document.getElementById('cnc_setup').value=config.metal_processing.cnc_setup_fee||50;
document.getElementById('cnc_hourly').value=config.metal_processing.cnc_hourly_rate||80;
document.getElementById('anodizing').value=config.metal_processing.surface_treatment?.anodizing||0.5;
document.getElementById('plating').value=config.metal_processing.surface_treatment?.plating||1.0;
document.getElementById('painting').value=config.metal_processing.surface_treatment?.painting||0.3;
document.getElementById('polishing').value=config.metal_processing.surface_treatment?.polishing||0.8;
}

updatePreview();
}

// 更新预览
function updatePreview(){
const machineCost=parseFloat(document.getElementById('machine_cost').value)||0;
const laborCost=parseFloat(document.getElementById('labor_cost').value)||0;
const profit=parseFloat(document.getElementById('default_profit').value)||2;

// 示例：10g PLA, 40 分钟
const weightG=10;
const printHours=40/60;
const plaPrice=parseFloat(config.materials?.PLA?.price_per_g)||0.08;

const materialCost=weightG*plaPrice;
const machineCostTotal=printHours*machineCost;
const totalCost=materialCost+machineCostTotal+laborCost;
const price=totalCost*profit;

document.getElementById('preview_material').textContent='¥'+materialCost.toFixed(2);
document.getElementById('preview_machine').textContent='¥'+machineCostTotal.toFixed(2);
document.getElementById('preview_labor').textContent='¥'+laborCost.toFixed(2);
document.getElementById('preview_total').textContent='¥'+totalCost.toFixed(2);
document.getElementById('preview_price').textContent='¥'+price.toFixed(2);
}

// 保存配置
document.getElementById('configForm').addEventListener('submit',async e=>{
e.preventDefault();

const newConfig={
machine_cost_per_hour:parseFloat(document.getElementById('machine_cost').value),
labor_cost_base:parseFloat(document.getElementById('labor_cost').value),
min_price:parseFloat(document.getElementById('min_price').value),
default_profit_margin:parseFloat(document.getElementById('default_profit').value),
default_layer_height:parseFloat(document.getElementById('layer_height').value),
default_infill:parseInt(document.getElementById('infill').value),
materials:{}
};

// 收集材料配置
const allMaterials=[...categories.nonmetal,...categories.metal];
for(const key of allMaterials){
const densityEl=document.querySelector(`[name="mat_density_${key}"]`);
const priceEl=document.querySelector(`[name="mat_price_${key}"]`);
const descEl=document.querySelector(`[name="mat_desc_${key}"]`);
if(densityEl&&priceEl&&descEl&&config.materials[key]){
newConfig.materials[key]={
density:parseFloat(densityEl.value)||config.materials[key].density,
price_per_g:parseFloat(priceEl.value)||config.materials[key].price_per_g,
name:config.materials[key].name,
desc:descEl.value||config.materials[key].desc
};
}
}

// 收集金属加工费用
newConfig.metal_processing={
cnc_setup_fee:parseFloat(document.getElementById('cnc_setup').value)||50,
cnc_hourly_rate:parseFloat(document.getElementById('cnc_hourly').value)||80,
surface_treatment:{
anodizing:parseFloat(document.getElementById('anodizing').value)||0.5,
plating:parseFloat(document.getElementById('plating').value)||1.0,
painting:parseFloat(document.getElementById('painting').value)||0.3,
polishing:parseFloat(document.getElementById('polishing').value)||0.8
}
};

try{
const res=await fetch('/admin/api/config',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify(newConfig)
});
const result=await res.json();
if(result.success){
showMsg('✅ 配置已保存','success');
config=newConfig;
}else{
showMsg('❌ 保存失败：'+result.error,'error');
}
}catch(err){
showMsg('❌ 保存失败：'+err.message,'error');
}
});

function showMsg(msg,type){
const div=document.getElementById('msg');
div.className='alert alert-'+type;
div.textContent=msg;
div.style.display='block';
setTimeout(()=>div.style.display='none',3000);
}

// 实时预览
document.querySelectorAll('input').forEach(inp=>{
inp.addEventListener('input',updatePreview);
});

loadConfig();
</script>
</body>
</html>'''

class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/admin' or parsed.path == '/admin/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(ADMIN_HTML.encode('utf-8'))
        
        elif parsed.path == '/admin/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            config = load_config()
            self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/admin/api/config':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                new_config = json.loads(post_data.decode('utf-8'))
                
                # 保存配置
                save_config(new_config)
                
                self.send_json({'success': True, 'config': new_config})
            except Exception as e:
                self.send_json({'success': False, 'error': str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[Admin] {args[0]}")

def run_admin(port=5001):
    server = HTTPServer(('0.0.0.0', port), AdminHandler)
    print("=" * 60)
    print("⚙️  3D 打印报价 - 管理后台")
    print("=" * 60)
    print(f"🌐 访问地址：http://localhost:{port}/admin")
    print(f"📁 配置文件：{CONFIG_FILE}")
    print("=" * 60)
    server.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    run_admin(port)
