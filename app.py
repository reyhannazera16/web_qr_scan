from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import json
import requests
from io import StringIO, BytesIO
import qrcode
from PIL import Image
import os

app = Flask(__name__)
CORS(app)

# File untuk menyimpan links
LINKS_FILE = 'link.txt'

# Simpan daftar link spreadsheet
spreadsheet_links = []

# Load links dari file saat startup
def load_links_from_file():
    global spreadsheet_links
    if os.path.exists(LINKS_FILE):
        try:
            with open(LINKS_FILE, 'r') as f:
                spreadsheet_links = [line.strip() for line in f.readlines() if line.strip()]
            print(f"Loaded {len(spreadsheet_links)} links from {LINKS_FILE}")
        except Exception as e:
            print(f"Error loading links: {e}")
            spreadsheet_links = []
    else:
        spreadsheet_links = []

# Save links ke file
def save_links_to_file():
    try:
        with open(LINKS_FILE, 'w') as f:
            for link in spreadsheet_links:
                f.write(link + '\n')
    except Exception as e:
        print(f"Error saving links: {e}")

# Load links saat aplikasi dimulai
load_links_from_file()

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem QR Code Product Checker</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .container-main {
            max-width: 1200px;
            margin: 0 auto;
        }
        .detail-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .product-image {
            width: 100%;
            height: 300px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 60px;
        }
        .spec-item {
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .spec-item:last-child {
            border-bottom: none;
        }
        .spec-label {
            font-weight: 600;
            color: #667eea;
            min-width: 150px;
        }
        .stock-badge {
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        }
        .stock-available {
            background: #d4edda;
            color: #155724;
        }
        .stock-empty {
            background: #f8d7da;
            color: #721c24;
        }
        .error-page {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
        }
        .error-box {
            background: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            color: white;
        }
        .header-info {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            padding-top: 20px;
        }
        .price-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .price-label {
            color: #666;
            font-size: 14px;
        }
        .price-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .nav-tabs .nav-link {
            color: #333;
            font-weight: 500;
        }
        .nav-tabs .nav-link.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .form-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .qr-display {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            margin: 15px 0;
        }
        .qr-display canvas {
            margin: 10px auto;
            padding: 10px;
            background: white;
            border-radius: 10px;
        }
        .product-row {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .product-row:hover {
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.15);
        }
        .link-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .link-card .link-info {
            flex: 1;
        }
        .link-card .link-url {
            color: #667eea;
            font-size: 12px;
            word-break: break-all;
            margin-top: 5px;
        }
        .save-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .save-buttons button {
            flex: 1;
            min-width: 120px;
        }
    </style>
</head>
<body>
    <div class="container-main">
        <div id="scanMode" style="display: none;">
            <div class="header-info">
                <h1><i class="fas fa-qrcode"></i> Informasi Barang</h1>
            </div>
            <div id="loadingSpinner" class="loading">
                <div>
                    <div class="spinner-border text-white"></div>
                    <p class="mt-3">Memuat data barang...</p>
                </div>
            </div>
            <div id="productDetail" class="detail-card"></div>
            <div id="errorMessage" class="error-page" style="display: none;">
                <div class="error-box">
                    <i class="fas fa-exclamation-circle" style="font-size: 50px; color: #dc3545;"></i>
                    <h2 class="mt-3">Barang Tidak Ditemukan</h2>
                    <p id="errorText"></p>
                    <a href="/" class="btn btn-primary mt-3">Kembali</a>
                </div>
            </div>
        </div>

        <div id="adminMode">
            <div class="header-info">
                <h1><i class="fas fa-cog"></i> Sistem Manajemen QR Code</h1>
                <p>Multi-Spreadsheet QR Code Generator</p>
            </div>

            <ul class="nav nav-tabs mb-4" role="tablist">
                <li class="nav-item">
                    <a class="nav-link active" data-bs-toggle="tab" href="#links">1. Kelola Link</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#qrgen">2. Generate QR</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#products">3. Daftar Barang</a>
                </li>
            </ul>

            <div class="tab-content">
                <!-- Kelola Link Tab -->
                <div class="tab-pane fade show active" id="links">
                    <div class="form-section">
                        <h3><i class="fas fa-link"></i> Kelola Link Spreadsheet</h3>
                        <p class="text-muted mb-3">Tambahkan link Google Sheets yang sudah di-publish ke web</p>
                        
                        <div class="mb-3">
                            <label class="form-label"><strong>Paste Link CSV Google Sheets:</strong></label>
                            <div class="input-group">
                                <input type="text" class="form-control" id="newLink" placeholder="https://docs.google.com/spreadsheets/d/.../pub?output=csv">
                                <button class="btn btn-primary" onclick="addLink()">
                                    <i class="fas fa-plus"></i> Tambah
                                </button>
                            </div>
                            <small class="text-muted d-block mt-2">
                                Caranya: Buka Sheet → Share → Publish to web → Copy URL yang ada di kanan
                            </small>
                        </div>

                        <div id="linkStatus" class="mt-2"></div>

                        <hr class="my-4">
                        <h5>Link Yang Tersimpan:</h5>
                        <div id="linksList"></div>
                    </div>
                </div>

                <!-- Generate QR Tab -->
                <div class="tab-pane fade" id="qrgen">
                    <div class="form-section">
                        <h3><i class="fas fa-qrcode"></i> Generate QR Code</h3>
                        <div class="mb-3">
                            <label class="form-label"><strong>Pilih Barang:</strong></label>
                            <select class="form-select form-select-lg" id="productSelect" onchange="generateQR()">
                                <option value="">-- Pilih Barang --</option>
                            </select>
                        </div>
                        <div id="qrContainer"></div>
                        <div id="urlContainer" style="display: none;" class="mt-4">
                            <label class="form-label"><strong>URL untuk QR Code:</strong></label>
                            <div class="input-group mb-3">
                                <input type="text" class="form-control" id="qrUrl" readonly>
                                <button class="btn btn-outline-secondary" onclick="copyURL()">
                                    <i class="fas fa-copy"></i> Copy
                                </button>
                            </div>
                            <div class="save-buttons">
                                <button class="btn btn-success" onclick="saveQRCode('png')">
                                    <i class="fas fa-download"></i> PNG
                                </button>
                                <button class="btn btn-info" onclick="saveQRCode('jpg')">
                                    <i class="fas fa-download"></i> JPG
                                </button>
                                <button class="btn btn-warning" onclick="printQRCode()">
                                    <i class="fas fa-print"></i> Print
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Daftar Barang Tab -->
                <div class="tab-pane fade" id="products">
                    <div class="form-section">
                        <h3><i class="fas fa-list"></i> Daftar Barang</h3>
                        <button class="btn btn-info btn-sm mb-3" onclick="loadProducts()">
                            <i class="fas fa-sync"></i> Refresh
                        </button>
                        <div id="productsList"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script>
        let allProducts = [];
        let currentQRUrl = '';
        const urlParams = new URLSearchParams(window.location.search);
        const productId = urlParams.get('id');

        if (productId) {
            document.getElementById('scanMode').style.display = 'block';
            document.getElementById('adminMode').style.display = 'none';
            loadProductForScan(productId);
        } else {
            document.getElementById('adminMode').style.display = 'block';
            document.getElementById('scanMode').style.display = 'none';
            loadLinks();
            loadProducts();
        }

        async function addLink() {
            const link = document.getElementById('newLink').value.trim();
            if (!link) {
                alert('Masukkan link terlebih dahulu');
                return;
            }

            try {
                const response = await fetch('/api/add-link', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({link: link})
                });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('linkStatus').innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle"></i> ${data.message}
                        </div>
                    `;
                    document.getElementById('newLink').value = '';
                    loadLinks();
                    loadProducts();
                } else {
                    document.getElementById('linkStatus').innerHTML = `
                        <div class="alert alert-danger">Gagal: ${data.message}</div>
                    `;
                }
            } catch (error) {
                document.getElementById('linkStatus').innerHTML = `
                    <div class="alert alert-danger">Error: ${error}</div>
                `;
            }
        }

        async function loadLinks() {
            try {
                const response = await fetch('/api/links');
                const data = await response.json();
                displayLinks(data.links);
            } catch (error) {
                console.error('Error:', error);
            }
        }

        function displayLinks(links) {
            const container = document.getElementById('linksList');
            if (links.length === 0) {
                container.innerHTML = '<p class="text-muted">Belum ada link spreadsheet</p>';
                return;
            }

            let html = '';
            links.forEach((link, index) => {
                const shortUrl = link.substring(0, 80) + '...';
                html += `
                    <div class="link-card">
                        <div class="link-info">
                            <div><strong>Link ${index + 1}</strong></div>
                            <div class="link-url">${shortUrl}</div>
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="removeLink(${index})">
                            <i class="fas fa-trash"></i> Hapus
                        </button>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        async function removeLink(index) {
            if (confirm('Yakin hapus link ini?')) {
                try {
                    const response = await fetch('/api/remove-link', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({index: index})
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        loadLinks();
                        loadProducts();
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
        }

        async function loadProducts() {
            try {
                const response = await fetch('/api/products');
                allProducts = await response.json();
                updateProductSelect();
                displayProductsList();
            } catch (error) {
                console.error('Error:', error);
            }
        }

        function updateProductSelect() {
            const select = document.getElementById('productSelect');
            select.innerHTML = '<option value="">-- Pilih Barang --</option>';
            allProducts.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = `${p.id} - ${p.nama}`;
                select.appendChild(option);
            });
        }

        function generateQR() {
            const productId = document.getElementById('productSelect').value;
            if (!productId) return;

            const baseUrl = window.location.origin + window.location.pathname;
            const qrUrl = `${baseUrl}?id=${productId}`;
            currentQRUrl = qrUrl;
            
            document.getElementById('qrUrl').value = qrUrl;
            
            const container = document.getElementById('qrContainer');
            container.innerHTML = '<div class="qr-display" id="qrcode"></div>';
            
            setTimeout(() => {
                new QRCode(document.getElementById('qrcode'), {
                    text: qrUrl,
                    width: 300,
                    height: 300,
                    colorDark: '#000000',
                    colorLight: '#ffffff',
                    correctLevel: QRCode.CorrectLevel.H
                });
                document.getElementById('urlContainer').style.display = 'block';
            }, 100);
        }

        function copyURL() {
            document.getElementById('qrUrl').select();
            document.execCommand('copy');
            alert('URL dicopy!');
        }

        async function saveQRCode(format) {
            const productId = document.getElementById('productSelect').value;
            if (!productId) {
                alert('Pilih barang terlebih dahulu');
                return;
            }

            try {
                const response = await fetch('/api/save-qr', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        url: currentQRUrl,
                        productId: productId,
                        format: format
                    })
                });

                if (!response.ok) throw new Error('Gagal menyimpan QR Code');
                
                const blob = await response.blob();
                const urlBlob = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = urlBlob;
                a.download = `QR_${productId}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(urlBlob);
                document.body.removeChild(a);
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        function printQRCode() {
            const productId = document.getElementById('productSelect').value;
            if (!productId) {
                alert('Pilih barang terlebih dahulu');
                return;
            }

            const qrElement = document.getElementById('qrcode');
            if (!qrElement) {
                alert('Generate QR Code terlebih dahulu');
                return;
            }

            const printWindow = window.open('', '', 'width=600,height=400');
            printWindow.document.write(`
                <html>
                <head>
                    <title>Print QR Code</title>
                    <style>
                        body { text-align: center; padding: 20px; font-family: Arial; }
                        .qr-container { margin: 20px 0; }
                        h3 { color: #333; }
                    </style>
                </head>
                <body>
                    <h3>QR Code - ${productId}</h3>
                    <div class="qr-container">
                        ${qrElement.innerHTML}
                    </div>
                    <p>${currentQRUrl}</p>
                </body>
                </html>
            `);
            printWindow.document.close();
            setTimeout(() => {
                printWindow.print();
                printWindow.close();
            }, 250);
        }

        function displayProductsList() {
            const container = document.getElementById('productsList');
            if (allProducts.length === 0) {
                container.innerHTML = '<p class="text-muted">Belum ada data barang</p>';
                return;
            }

            let html = '';
            allProducts.forEach(p => {
                const stock = parseInt(p.stok) || 0;
                const price = parseInt(p.harga) || 0;
                html += `
                    <div class="product-row">
                        <div class="row">
                            <div class="col-md-8">
                                <h6>${p.nama}</h6>
                                <small class="text-muted">ID: ${p.id} | ${p.kategori}</small>
                                <div class="mt-2">Rp ${price.toLocaleString('id-ID')} | Stok: ${stock}</div>
                            </div>
                            <div class="col-md-4 text-end">
                                <button class="btn btn-sm btn-info" onclick="quickQR('${p.id}')">
                                    <i class="fas fa-qrcode"></i> QR
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        function quickQR(id) {
            document.getElementById('productSelect').value = id;
            generateQR();
            document.querySelector('a[href="#qrgen"]').click();
        }

        async function loadProductForScan(id) {
            try {
                const response = await fetch(`/api/product/${id}`);
                const product = await response.json();

                if (product.error) {
                    showError(`Barang dengan ID "${id}" tidak ditemukan`);
                } else {
                    displayProductDetail(product);
                }
            } catch (error) {
                showError('Gagal memuat data');
            }
        }

        function displayProductDetail(product) {
            const price = parseInt(product.harga) || 0;
            const stock = parseInt(product.stok) || 0;
            const isAvailable = stock > 0;

            const icons = {
                'ac': 'fa-snowflake',
                'tv': 'fa-tv',
                'elektronik': 'fa-laptop',
                'furniture': 'fa-chair',
                'default': 'fa-box'
            };

            const icon = icons[product.kategori?.toLowerCase()] || icons['default'];

            let html = `
                <div class="row g-0">
                    <div class="col-md-4">
                        <div class="product-image">
                            <i class="fas ${icon}"></i>
                        </div>
                    </div>
                    <div class="col-md-8" style="padding: 30px;">
                        <h2>${product.nama}</h2>
                        <p class="text-muted">${product.kategori}</p>
                        
                        <div class="stock-badge ${isAvailable ? 'stock-available' : 'stock-empty'}">
                            ${isAvailable ? '✓ TERSEDIA' : '✗ HABIS'} | Stok: ${stock}
                        </div>

                        <div class="price-section">
                            <div class="price-label">Harga</div>
                            <div class="price-value">Rp ${price.toLocaleString('id-ID')}</div>
                        </div>

                        <h5 class="mt-4">Spesifikasi Detail</h5>
            `;

            const standardFields = ['id', 'nama', 'kategori', 'harga', 'stok'];
            Object.keys(product).forEach(key => {
                if (!standardFields.includes(key) && product[key]) {
                    const label = key.charAt(0).toUpperCase() + key.slice(1);
                    html += `
                        <div class="spec-item">
                            <span class="spec-label">${label}:</span>
                            <span>${product[key]}</span>
                        </div>
                    `;
                }
            });

            html += `
                        <a href="/" class="btn btn-secondary mt-3">
                            <i class="fas fa-arrow-left"></i> Kembali
                        </a>
                    </div>
                </div>
            `;

            document.getElementById('productDetail').innerHTML = html;
            document.getElementById('loadingSpinner').style.display = 'none';
        }

        function showError(msg) {
            document.getElementById('errorText').textContent = msg;
            document.getElementById('loadingSpinner').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'flex';
        }
    </script>
</body>
</html>
'''

# Route: Home
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Route: Add link
@app.route('/api/add-link', methods=['POST'])
def add_link():
    try:
        data = request.json
        link = data.get('link', '').strip()
        
        if not link:
            return jsonify({'success': False, 'message': 'Link kosong'})
        
        print(f"Testing link: {link}")
        
        try:
            response = requests.get(link, timeout=10)
            print(f"Status code: {response.status_code}")
            
            if response.status_code != 200:
                return jsonify({'success': False, 'message': f'Link tidak bisa diakses (Status: {response.status_code})'})
            
            print(f"Response preview (first 500 chars):\n{response.text[:500]}")
            
            try:
                df = pd.read_csv(StringIO(response.text))
            except:
                df = pd.read_csv(StringIO(response.text), skip_blank_lines=True)
            
            if any('unnamed' in str(col).lower() for col in df.columns):
                print("Header terdeteksi kosong, menggunakan baris pertama sebagai header")
                df = pd.read_csv(StringIO(response.text), header=0)
                if any('unnamed' in str(col).lower() for col in df.columns):
                    df = pd.read_csv(StringIO(response.text), skiprows=1, header=0)
            
            df.columns = df.columns.str.lower().str.strip()
            
            print(f"Columns found: {df.columns.tolist()}")
            print(f"Data preview:\n{df.head()}")
            
            if 'id' not in df.columns:
                return jsonify({'success': False, 'message': f'Sheet harus memiliki kolom ID. Kolom yang ada: {", ".join(df.columns.tolist())}'})
        
        except Exception as e:
            print(f"Error details: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        
        if link not in spreadsheet_links:
            spreadsheet_links.append(link)
            save_links_to_file()
        
        return jsonify({'success': True, 'message': 'Link berhasil ditambahkan'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Route: Remove link
@app.route('/api/remove-link', methods=['POST'])
def remove_link():
    try:
        data = request.json
        index = data.get('index')
        
        if 0 <= index < len(spreadsheet_links):
            spreadsheet_links.pop(index)
            save_links_to_file()
            return jsonify({'success': True, 'message': 'Link dihapus'})
        
        return jsonify({'success': False, 'message': 'Index tidak valid'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Route: Get all links
@app.route('/api/links', methods=['GET'])
def get_links():
    return jsonify({'links': spreadsheet_links})

# Route: Get all products from all links
@app.route('/api/products', methods=['GET'])
def get_products():
    all_products = []
    
    for link in spreadsheet_links:
        try:
            response = requests.get(link, timeout=10)
            
            try:
                df = pd.read_csv(StringIO(response.text))
            except:
                df = pd.read_csv(StringIO(response.text), skip_blank_lines=True)
            
            if any('unnamed' in str(col).lower() for col in df.columns):
                df = pd.read_csv(StringIO(response.text), skiprows=1, header=0)
            
            df.columns = df.columns.str.lower().str.strip()
            
            products = df.to_dict('records')
            all_products.extend(products)
        except Exception as e:
            print(f"Error reading {link}: {str(e)}")
            continue
    
    return jsonify(all_products)

# Route: Get single product
@app.route('/api/product/<product_id>', methods=['GET'])
def get_product(product_id):
    for link in spreadsheet_links:
        try:
            response = requests.get(link, timeout=10)
            
            try:
                df = pd.read_csv(StringIO(response.text))
            except:
                df = pd.read_csv(StringIO(response.text), skip_blank_lines=True)
            
            if any('unnamed' in str(col).lower() for col in df.columns):
                df = pd.read_csv(StringIO(response.text), skiprows=1, header=0)
            
            df.columns = df.columns.str.lower().str.strip()
            
            for _, row in df.iterrows():
                if row.get('id', '').lower() == product_id.lower():
                    product = row.to_dict()
                    return jsonify(product)
        except Exception as e:
            print(f"Error reading {link}: {str(e)}")
            continue
    
    return jsonify({'error': 'Product not found'}), 404

# Route: Save QR Code
@app.route('/api/save-qr', methods=['POST'])
def save_qr():
    try:
        data = request.json
        qr_url = data.get('url', '')
        product_id = data.get('productId', '')
        file_format = data.get('format', 'png').lower()
        
        if not qr_url:
            return jsonify({'error': 'URL tidak ada'}), 400
        
        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color='#667eea', back_color='white')
        
        # Convert to requested format
        if file_format == 'jpg':
            # Convert RGBA to RGB
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
                img = rgb_img
            
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=95)
        else:  # PNG
            img_io = BytesIO()
            img.save(img_io, format='PNG')
        
        img_io.seek(0)
        return send_file(
            img_io,
            mimetype=f'image/{file_format}',
            as_attachment=True,
            download_name=f'QR_{product_id}.{file_format}'
        )
    
    except Exception as e:
        print(f"Error saving QR: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)