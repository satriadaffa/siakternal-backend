"""
SIAKTERNAK - routes.py
Definisi semua endpoint REST API untuk transaksi dan laporan laba rugi
"""

from flask import Blueprint, request, jsonify
from models import get_db

# Blueprint untuk endpoint transaksi
transaksi_bp = Blueprint('transaksi', __name__)

# Blueprint untuk endpoint laporan
laporan_bp = Blueprint('laporan', __name__)


# ---------------------------------------------------------------------------
# ENDPOINT TRANSAKSI
# ---------------------------------------------------------------------------

@transaksi_bp.route('/transaksi', methods=['POST'])
def tambah_transaksi():
    """
    POST /transaksi
    Menambahkan transaksi baru (pemasukan atau pengeluaran).

    Body JSON:
    {
        "jenis"     : "pemasukan" | "pengeluaran",
        "kategori"  : string,
        "jumlah"    : float,
        "keterangan": string (opsional),
        "tanggal"   : "YYYY-MM-DD"
    }
    """
    data = request.get_json()

    # Validasi field wajib
    required_fields = ['jenis', 'kategori', 'jumlah', 'tanggal']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Field "{field}" wajib diisi.'}), 400

    if data['jenis'] not in ['pemasukan', 'pengeluaran']:
        return jsonify({'error': 'Jenis harus "pemasukan" atau "pengeluaran".'}), 400

    try:
        jumlah = float(data['jumlah'])
        if jumlah <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Jumlah harus berupa angka positif.'}), 400

    db = get_db()
    db.execute(
        """
        INSERT INTO transaksi (jenis, kategori, jumlah, keterangan, tanggal)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data['jenis'],
            data['kategori'],
            jumlah,
            data.get('keterangan', ''),
            data['tanggal'],
        )
    )
    db.commit()

    return jsonify({'pesan': 'Transaksi berhasil disimpan.'}), 201


@transaksi_bp.route('/transaksi', methods=['GET'])
def ambil_semua_transaksi():
    """
    GET /transaksi
    Mengambil seluruh data transaksi, diurutkan terbaru di atas.

    Query params opsional:
    - bulan : angka bulan (1-12) untuk filter
    - tahun : angka tahun untuk filter
    """
    bulan = request.args.get('bulan')
    tahun = request.args.get('tahun')

    db = get_db()
    query = "SELECT * FROM transaksi WHERE 1=1"
    params = []

    if tahun:
        query += " AND strftime('%Y', tanggal) = ?"
        params.append(str(tahun).zfill(4))
    if bulan:
        query += " AND strftime('%m', tanggal) = ?"
        params.append(str(bulan).zfill(2))

    query += " ORDER BY tanggal DESC, id DESC"

    rows = db.execute(query, params).fetchall()
    hasil = [dict(row) for row in rows]

    return jsonify(hasil), 200


@transaksi_bp.route('/transaksi/<int:transaksi_id>', methods=['GET'])
def ambil_transaksi_detail(transaksi_id):
    """
    GET /transaksi/<id>
    Mengambil detail satu transaksi berdasarkan ID.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM transaksi WHERE id = ?", (transaksi_id,)
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Transaksi tidak ditemukan.'}), 404

    return jsonify(dict(row)), 200


@transaksi_bp.route('/transaksi/<int:transaksi_id>', methods=['PUT'])
def edit_transaksi(transaksi_id):
    """
    PUT /transaksi/<id>
    Memperbarui data transaksi berdasarkan ID.
    """
    data = request.get_json()
    db = get_db()

    # Pastikan transaksi ada
    row = db.execute(
        "SELECT * FROM transaksi WHERE id = ?", (transaksi_id,)
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Transaksi tidak ditemukan.'}), 404

    # Gunakan nilai lama jika field tidak dikirim
    existing = dict(row)
    jenis      = data.get('jenis', existing['jenis'])
    kategori   = data.get('kategori', existing['kategori'])
    jumlah     = float(data.get('jumlah', existing['jumlah']))
    keterangan = data.get('keterangan', existing['keterangan'])
    tanggal    = data.get('tanggal', existing['tanggal'])

    if jenis not in ['pemasukan', 'pengeluaran']:
        return jsonify({'error': 'Jenis harus "pemasukan" atau "pengeluaran".'}), 400

    db.execute(
        """
        UPDATE transaksi
        SET jenis=?, kategori=?, jumlah=?, keterangan=?, tanggal=?
        WHERE id=?
        """,
        (jenis, kategori, jumlah, keterangan, tanggal, transaksi_id)
    )
    db.commit()

    return jsonify({'pesan': 'Transaksi berhasil diperbarui.'}), 200


@transaksi_bp.route('/transaksi/<int:transaksi_id>', methods=['DELETE'])
def hapus_transaksi(transaksi_id):
    """
    DELETE /transaksi/<id>
    Menghapus transaksi berdasarkan ID.
    """
    db = get_db()

    row = db.execute(
        "SELECT id FROM transaksi WHERE id = ?", (transaksi_id,)
    ).fetchone()

    if row is None:
        return jsonify({'error': 'Transaksi tidak ditemukan.'}), 404

    db.execute("DELETE FROM transaksi WHERE id = ?", (transaksi_id,))
    db.commit()

    return jsonify({'pesan': 'Transaksi berhasil dihapus.'}), 200


# ---------------------------------------------------------------------------
# ENDPOINT LAPORAN LABA RUGI
# ---------------------------------------------------------------------------

@laporan_bp.route('/laporan', methods=['GET'])
def laporan_laba_rugi():
    """
    GET /laporan
    Mengambil laporan laba rugi otomatis sesuai prinsip PMK 81/2024.

    Rumus:
        Laba/Rugi = Total Pemasukan - Total Pengeluaran

    Query params opsional:
    - bulan : angka bulan (1-12)
    - tahun : angka tahun
    """
    bulan = request.args.get('bulan')
    tahun = request.args.get('tahun')

    db = get_db()
    where = "WHERE 1=1"
    params = []

    if tahun:
        where += " AND strftime('%Y', tanggal) = ?"
        params.append(str(tahun).zfill(4))
    if bulan:
        where += " AND strftime('%m', tanggal) = ?"
        params.append(str(bulan).zfill(2))

    # Hitung total pemasukan
    row_masuk = db.execute(
        f"SELECT COALESCE(SUM(jumlah), 0) AS total FROM transaksi {where} AND jenis='pemasukan'",
        params
    ).fetchone()

    # Hitung total pengeluaran
    row_keluar = db.execute(
        f"SELECT COALESCE(SUM(jumlah), 0) AS total FROM transaksi {where} AND jenis='pengeluaran'",
        params
    ).fetchone()

    # Ambil rincian per kategori pemasukan
    rincian_masuk = db.execute(
        f"""
        SELECT kategori, SUM(jumlah) AS total
        FROM transaksi {where} AND jenis='pemasukan'
        GROUP BY kategori ORDER BY total DESC
        """,
        params
    ).fetchall()

    # Ambil rincian per kategori pengeluaran
    rincian_keluar = db.execute(
        f"""
        SELECT kategori, SUM(jumlah) AS total
        FROM transaksi {where} AND jenis='pengeluaran'
        GROUP BY kategori ORDER BY total DESC
        """,
        params
    ).fetchall()

    total_pemasukan  = row_masuk['total']
    total_pengeluaran = row_keluar['total']
    laba_rugi         = total_pemasukan - total_pengeluaran

    return jsonify({
        'filter': {
            'bulan': bulan,
            'tahun': tahun,
        },
        'total_pemasukan'  : total_pemasukan,
        'total_pengeluaran': total_pengeluaran,
        'laba_rugi'        : laba_rugi,
        'status'           : 'laba' if laba_rugi >= 0 else 'rugi',
        'rincian_pemasukan' : [dict(r) for r in rincian_masuk],
        'rincian_pengeluaran': [dict(r) for r in rincian_keluar],
    }), 200
