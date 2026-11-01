# Paket Automation UMKM — n8n

Enam workflow siap pakai untuk UMKM Indonesia. Semua pakai node bawaan n8n.

| # | Workflow | File | Nodes | Fungsi |
|---|---|---|---|---|
| 01 | Auto-Reply Bot | `umkm-01-auto-reply-bot.json` | 12 | Balas chat otomatis (harga, jam, alamat, order) |
| 02 | Order → Notifikasi | `umkm-02-order-notifikasi.json` | 6 | Order masuk → Sheets + Telegram + konfirmasi |
| 03 | Invoice Otomatis | `umkm-03-invoice-otomatis.json` | 7 | Bayar → invoice PDF → kirim |
| 04 | Laporan Harian | `umkm-04-laporan-harian.json` | 5 | Rekap penjualan tiap jam 8 malam |
| 05 | Form Order → Notif | `umkm-05-form-order-notif.json` | 5 | Google Form isi → kabar 1 menit |
| 06 | Minta Review | `umkm-06-minta-review.json` | 6 | Order selesai +24 jam → minta review Google |

**Total: 41 nodes, 6 workflow.**

---

## Cara import

1. Buka n8n (`http://localhost:5678`)
2. **Workflows** → tombol **...** kanan atas → **Import from File**
3. Pilih file `.json`
4. Klik **Open**

---

## Yang harus disiapkan sekali

| Item | Dari mana | Dipakai di |
|---|---|---|
| **Telegram Bot Token** | @BotFather → `/newbot` | Semua workflow |
| **Chat ID** | @userinfobot | Semua workflow |
| **Google Sheets credential** | n8n Credentials → Google Sheets OAuth2 | 02, 04, 05, 06 |
| **Google Sheet** | sheets.google.com | 02, 04, 05, 06 |

---

## Yang harus diedit per client

| Placeholder | Di mana | Ganti dengan |
|---|---|---|
| `GANTI_CREDENTIAL_ID` | Semua node Telegram/Sheets | ID credential n8n |
| `GANTI_CHAT_ID` | Node kirim Telegram | Chat ID client |
| `GANTI_SPREADSHEET_ID` | Node Google Sheets | ID sheet client |
| `[NAMA TOKO ANDA]` | UMKM 01, 03, 06 | Nama toko client |
| `[ALAMAT TOKO ANDA]` | UMKM 03 | Alamat toko |
| `GANTI_PLACE_ID` | UMKM 06 | Link review Google Business |

---

## Paket jual

| Paket | Isi | Harga |
|---|---|---|
| **Basic** | 1 workflow + setup + 1x revisi | Rp 500.000 - 800.000 |
| **Standard** | 3 workflow + dokumentasi + training 1 jam | Rp 1.500.000 - 2.500.000 |
| **Premium** | Self-hosted n8n di VPS + 5 workflow + training + 1 bulan support | Rp 3.500.000 - 6.000.000 |
| **Retainer** | Maintenance + 1 workflow baru/bulan | Rp 1.000.000 - 2.000.000/bulan |

---

## Selling point

| Poin | Penjelasan ke client |
|---|---|
| **Self-hosted** | Data pelanggan gak keluar dari server lo |
| **Sekali bayar** | Bukan langganan bulanan kayak Zapier |
| **Bisa dikembangin** | Node sendiri, logic sendiri, gak dibatasi platform |
| **Bahasa Indonesia** | Dokumentasi + support Bahasa Indonesia |

---

## Catatan teknis

- Semua workflow pakai node bawaan n8n — tidak butuh community node
- UMKM 02 & 03 pakai Webhook — butuh n8n yang bisa diakses dari internet (VPS atau tunnel)
- UMKM 04 & 05 pakai Google Sheets trigger — polling tiap menit
- UMKM 06 pakai Wait node — butuh n8n tetap jalan (jangan matiin)
