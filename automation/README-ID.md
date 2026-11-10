# TWIST Automation Studio — Website Publik

Folder ini berisi website katalog automation beserta koleksi workflow n8n yang dipublikasikan pada:

https://twist5202-ux.github.io/automation/

## Struktur utama

- `index.html` — halaman utama automation
- `cs/`, `demo/`, `harga/` — halaman pendukung
- Folder kategori workflow — kumpulan file ekspor JSON n8n
- `automation/` — koleksi tambahan yang bertingkat; isinya belum tentu sama dengan folder kategori di atasnya
- `README.md` — dokumentasi bahasa Inggris

## Cara mengelola

Folder ini adalah bagian dari repository yang menayangkan website publik. Jangan memindahkan `index.html`, mengubah alamat aset, atau menghapus direktori yang kelihatan mirip sebelum memeriksa link serta fungsi website. Periksa credential, webhook, dan endpoint sebelum mengimpor atau mengaktifkan template n8n.

Repository [twist-automation](https://github.com/twist5202-ux/twist-automation) adalah salinan project terpisah. Perubahan di sana **tidak otomatis tersinkron** ke folder website publik ini.

Dokumentasi security research ada di [security-writeups](https://github.com/twist5202-ux/security-writeups).
