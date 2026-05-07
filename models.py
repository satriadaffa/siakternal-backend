"""
SIAKTERNAK - models.py
Definisi skema database dan fungsi inisialisasi SQLite
"""

import sqlite3
from flask import g, current_app


def get_db():
    """Mendapatkan koneksi database dari context aplikasi Flask."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Kembalikan hasil query sebagai dictionary agar mudah diakses
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Menutup koneksi database setelah request selesai."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """
    Membuat tabel transaksi jika belum ada.
    Skema mengikuti prinsip pencatatan keuangan PMK 81/2024:
    - jenis: 'pemasukan' atau 'pengeluaran'
    - kategori: misalnya 'Penjualan Sapi', 'Pakan', dll.
    - jumlah: nominal dalam Rupiah
    - keterangan: catatan tambahan
    - tanggal: format YYYY-MM-DD
    """
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis       TEXT    NOT NULL CHECK(jenis IN ('pemasukan', 'pengeluaran')),
            kategori    TEXT    NOT NULL,
            jumlah      REAL    NOT NULL CHECK(jumlah > 0),
            keterangan  TEXT,
            tanggal     TEXT    NOT NULL
        )
    """)
    db.commit()
    db.close()
    print("[SIAKTERNAK] Database berhasil diinisialisasi.")
