# 🐄 HayvonMarket — Hayvonlar savdosi platformasi

## Ishga tushirish

### 1. Talablar
- Python 3.8+
- Flask (`pip install flask`)

### 2. O'rnatish
```bash
# Loyihani yuklab oling
# Papkaga o'ting
cd hayvonmarket

# Flask o'rnating
pip install flask

# Ishga tushiring
python app.py
```

### 3. Brauzerda oching
```
http://127.0.0.1:5000
```

## Kirish ma'lumotlari

| Rol   | Login   | Parol    |
|-------|---------|----------|
| Admin | admin   | admin123 |
| Demo  | sardor  | demo123  |
| Demo  | aziz    | demo123  |
| Demo  | malika  | demo123  |

## Sayt sahifalari

| URL | Tavsif |
|-----|--------|
| `/` | Bosh sahifa |
| `/catalog` | Barcha e'lonlar (filter, qidiruv) |
| `/listing/<id>` | E'lon tafsilotlari |
| `/listing/new` | Yangi e'lon joylash |
| `/favorites` | Sevimli e'lonlar |
| `/messages` | Xabarlar |
| `/profile` | Profil tahrirlash |
| `/my-listings` | Mening e'lonlarim |
| `/register` | Ro'yxatdan o'tish |
| `/login` | Kirish |
| `/admin/` | Admin panel |

## Imkoniyatlar
- ✅ To'liq autentifikatsiya (kirish/ro'yxat/chiqish)
- ✅ E'lon joylash, tahrirlash, o'chirish
- ✅ Qidiruv va filtr (tur, viloyat, narx)
- ✅ Sevimlilar
- ✅ Xabar almashish (chat)
- ✅ Foydalanuvchi profili
- ✅ Reyting tizimi
- ✅ Admin panel (foydalanuvchilar, e'lonlar boshqaruvi)
- ✅ Animatsiyalar va zamonaviy UI
- ✅ Xush kelibsiz banner
- ✅ Qidiruv autocomplete
- ✅ Mobil qurilmalar uchun adaptiv dizayn

## Texnologiyalar
- **Backend**: Python Flask
- **Ma'lumotlar bazasi**: SQLite
- **Frontend**: Vanilla CSS + JS (animatsiyalar, particles)
- **Shrift**: Plus Jakarta Sans (Google Fonts)
