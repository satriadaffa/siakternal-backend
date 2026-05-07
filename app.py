"""
SIAKTERNAK - Sistem Informasi Akuntansi Peternakan
Entry point aplikasi Flask
"""

import os

from flask import Flask
from flask_cors import CORS
from routes import transaksi_bp, laporan_bp
from models import init_db

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Aktifkan CORS agar Flutter bisa mengakses API ini
CORS(app)

# Konfigurasi database SQLite
app.config['DATABASE'] = 'database.db'

# Daftarkan blueprint routes
app.register_blueprint(transaksi_bp)
app.register_blueprint(laporan_bp)

# Inisialisasi database saat aplikasi pertama kali dijalankan
with app.app_context():
    init_db()

if __name__ == '__main__':
    with app.app_context():
    init_db()
    # Railway menyediakan PORT melalui environment variable
    # Fallback ke 5000 saat dijalankan secara lokal
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
