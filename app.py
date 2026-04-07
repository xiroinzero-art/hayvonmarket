"""
HayvonMarket — Hayvonlar savdosi platformasi
Flask web application (Django-style: MVC, ORM, Admin, Auth)
Run: python app.py
Open: http://127.0.0.1:5000
Admin: admin / admin123
Demo:  sardor / demo123
"""
import os, sqlite3, hashlib, secrets, json, re, urllib.request, urllib.parse
from functools import wraps
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, g, jsonify, abort)

GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI', 'https://hayvonmarket-production.up.railway.app/auth/google/callback')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hayvon-market-ultra-secret-key-2024')
DATABASE = os.path.join(BASE_DIR, 'instance', 'db.sqlite3')

ANIMAL_TYPES = [
    ('sigir',    '🐄', "Sigir"),
    ('qoy',      '🐑', "Qo'y"),
    ('echki',    '🐐', "Echki"),
    ('ot',       '🐴', "Ot"),
    ('tovuq',    '🐓', "Tovuq"),
    ('o_rdak',   '🦆', "O'rdak"),
    ('g_oz',     '🪿', "G'oz"),
    ('quyon',    '🐇', "Quyon"),
    ('qoramol',  '🐂', "Qoramol/Buqa"),
    ('tuyoqli',  '🐪', "Tuya"),
    ('boshqa',   '🐾', "Boshqa"),
]

# Real animal images (Unsplash)
ANIMAL_IMAGES = {
    'sigir':   'https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?w=400&q=80',
    'qoy':     'https://images.unsplash.com/photo-1484557985045-edf25e08da73?w=400&q=80',
    'echki':   'https://images.unsplash.com/photo-1524024973431-2ad916746881?w=400&q=80',
    'ot':      'https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?w=400&q=80',
    'tovuq':   'https://images.unsplash.com/photo-1548550023-2bdb3c5beed7?w=400&q=80',
    'o_rdak':  'https://images.unsplash.com/photo-1518020382113-a7e8fc38eac9?w=400&q=80',
    'g_oz':    'https://images.unsplash.com/photo-1501706362039-c06b2d715385?w=400&q=80',
    'quyon':   'https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=400&q=80',
    'qoramol': 'https://images.unsplash.com/photo-1596733430284-f7437764b1a9?w=400&q=80',
    'tuyoqli': 'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=400&q=80',
    'boshqa':  'https://images.unsplash.com/photo-1516467508483-a7212febe31a?w=400&q=80',
}
REGIONS = ['Toshkent sh.','Toshkent vil.','Samarqand','Buxoro',
           "Andijon","Farg'ona","Namangan","Qashqadaryo",
           "Surxondaryo","Xorazm","Navoiy","Jizzax","Sirdaryo",
           "Qoraqalpog'iston"]

DELIVERY_PERSONS = [
    {'id':'d1','avatar':'J','name':'Jasur Toshmatov','region':'Toshkent sh.','deliveries':142,'rating':4.9,'reviews':38,'price':'30,000 so\'m'},
    {'id':'d2','avatar':'S','name':'Sardor Raximov','region':'Samarqand','deliveries':87,'rating':4.8,'reviews':24,'price':'25,000 so\'m'},
    {'id':'d3','avatar':'B','name':'Bobur Nazarov','region':"Farg'ona",'deliveries':63,'rating':4.7,'reviews':17,'price':'28,000 so\'m'},
    {'id':'d4','avatar':'O','name':'Otabek Mirzayev','region':'Buxoro','deliveries':55,'rating':4.6,'reviews':12,'price':'22,000 so\'m'},
]

VETS = [
    {'id':'v1','avatar':'K','name':'Dr. Kamoliddin Nazarov','region':'Toshkent','exp':15,'spec':'Yirik hayvonlar','rating':4.9,'reviews':34,'last_review':'Juda malakali shifokor, tavsiya qilaman!'},
    {'id':'v2','avatar':'N','name':'Dr. Nilufar Rahimova','region':'Samarqand','exp':10,'spec':'Chorva mollar','rating':4.8,'reviews':28,'last_review':'Tez va sifatli xizmat ko\'rsatdi.'},
    {'id':'v3','avatar':'J','name':'Dr. Jasur Yusupov','region':"Farg'ona",'exp':8,'spec':'Ot, sigir','rating':4.7,'reviews':19,'last_review':None},
    {'id':'v4','avatar':'S','name':'Dr. Shahnoza Mirzayeva','region':'Buxoro','exp':12,'spec':'Parrandalar','rating':4.6,'reviews':22,'last_review':'Parrandalar bo\'yicha eng yaxshi mutaxassis!'},
]

# ─── DB helpers ────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        username   TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        role       TEXT DEFAULT 'buyer',
        full_name  TEXT DEFAULT '',
        phone      TEXT DEFAULT '',
        region     TEXT DEFAULT '',
        email      TEXT DEFAULT '',
        bio        TEXT DEFAULT '',
        avatar_letter TEXT DEFAULT '',
        rating     REAL DEFAULT 5.0,
        total_sales INTEGER DEFAULT 0,
        is_verified INTEGER DEFAULT 0,
        is_admin   INTEGER DEFAULT 0,
        google_id  TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS listings (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        title        TEXT NOT NULL,
        animal_slug  TEXT NOT NULL,
        animal_emoji TEXT DEFAULT '🐾',
        animal_name  TEXT DEFAULT '',
        price        INTEGER NOT NULL,
        region       TEXT NOT NULL,
        district     TEXT DEFAULT '',
        age          TEXT DEFAULT '',
        gender       TEXT DEFAULT '',
        breed        TEXT DEFAULT '',
        count        INTEGER DEFAULT 1,
        weight       TEXT DEFAULT '',
        description  TEXT DEFAULT '',
        is_active    INTEGER DEFAULT 1,
        is_premium   INTEGER DEFAULT 0,
        is_sold      INTEGER DEFAULT 0,
        views        INTEGER DEFAULT 0,
        created_at   TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS messages (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id      INTEGER NOT NULL,
        to_id        INTEGER NOT NULL,
        listing_id   INTEGER,
        body         TEXT NOT NULL,
        is_read      INTEGER DEFAULT 0,
        created_at   TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(from_id) REFERENCES users(id),
        FOREIGN KEY(to_id)   REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS favorites (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        listing_id INTEGER NOT NULL,
        UNIQUE(user_id, listing_id)
    );
    CREATE TABLE IF NOT EXISTS reviews (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER NOT NULL,
        to_id   INTEGER NOT NULL,
        rating  INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        body    TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    try:
        db.execute("ALTER TABLE users ADD COLUMN google_id TEXT DEFAULT ''")
        db.commit()
    except:
        pass
    try:
        db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
        db.commit()
    except:
        pass
    try:
        db.execute("ALTER TABLE listings ADD COLUMN is_premium INTEGER DEFAULT 0")
        db.commit()
    except:
        pass
    try:
        db.execute("ALTER TABLE listings ADD COLUMN photos TEXT DEFAULT ''")
        db.commit()
    except:
        pass
    try:
        db.execute("ALTER TABLE listings ADD COLUMN video TEXT DEFAULT ''")
        db.commit()
    except:
        pass
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        _seed(db)
    db.commit()
    db.close()

def _seed(db):
    def hp(p): return hashlib.sha256(p.encode()).hexdigest()
    db.execute("""INSERT INTO users (username,password,full_name,phone,region,bio,rating,total_sales,is_verified,is_admin,avatar_letter)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
               ('admin',hp('admin123'),'Administrator','','','',5.0,0,1,1,'A'))
    sellers = [
        ('sardor',  hp('demo123'),'Sardor Abdullayev','+998901234567','Samarqand',
         "10 yildan beri chorvachilik bilan shug'ullanaman.",4.9,23,1,'S'),
        ('aziz',    hp('demo123'),'Aziz Karimov','+998912345678',"Toshkent vil.",
         "Qo'y va echki fermasi. Barcha hayvonlar emlangan.",4.7,15,1,'A'),
        ('malika',  hp('demo123'),'Malika Yusupova','+998933456789','Buxoro',
         "Oilaviy ferma. 20 yillik tajriba.",4.8,31,1,'M'),
        ('bobur',   hp('demo123'),'Bobur Toshmatov','+998944567890',"Farg'ona",
         "Otchilik mutaxassisi. Zotli otlar.",4.6,8,0,'B'),
    ]
    for row in sellers:
        db.execute("""INSERT INTO users (username,password,full_name,phone,region,bio,rating,total_sales,is_verified,avatar_letter)
                      VALUES (?,?,?,?,?,?,?,?,?,?)""", row)
    uids = {r['username']:r['id'] for r in db.execute("SELECT id,username FROM users").fetchall()}
    listings = [
        (uids['sardor'],'Sut sigiri — Holstein zoti','sigir','🐄',"Sigir",12000000,
         'Samarqand','Urgut','4 yosh',"Urg'ochi",'Holstein',1,'350 kg',
         "Kuniga 25 litr sut beradi. Sog'lom, emlangan. Barcha hujjatlari bor.",1,1),
        (uids['aziz'],"Qo'y (3 bosh)",'qoy','🐑',"Qo'y",4500000,
         "Toshkent vil.",'Zangiota','2-3 yosh','Aralash',"O'zbek zoti",3,'65 kg',
         "Uchta qo'y. Sog'lom, semiz, emlangan.",1,0),
        (uids['bobur'],'Zotli Arab oti','ot','🐴',"Ot",25000000,
         "Farg'ona",'Marg\'ilon','5 yosh','Erkak','Arab zoti',1,'480 kg',
         "Toza zotli, mashg'ullanilgan, hujjatli. Poyga uchun.",1,1),
        (uids['aziz'],'Echki (2 bosh) — sut zoti','echki','🐐',"Echki",2800000,
         "Toshkent vil.",'Kibray','1-2 yosh',"Urg'ochi",'Zanen',2,'42 kg',
         "Sut echkilari. Har biri kuniga 3 litr sut.",1,0),
        (uids['malika'],'Broiler tovuq (20 bosh)','tovuq','🐓',"Tovuq",1200000,
         'Buxoro','Buxoro sh.','45 kunlik','Aralash','Broiler',20,'2.5 kg',
         "Tayyor savdo uchun. Vazni 2.5-3 kg.",1,0),
        (uids['sardor'],"Qoramol — go'sht uchun",'qoramol','🐂',"Qoramol",8500000,
         'Samarqand','Samarqand sh.','3 yosh','Erkak','Aralash',1,'380 kg',
         "380 kg. Go'sht uchun semirtirilgan.",1,0),
        (uids['malika'],"Qo'y (5 bosh) — Gissar",'qoy','🐑',"Qo'y",9000000,
         'Buxoro','Kogon','2-4 yosh','Erkak','Gissar',5,'80 kg',
         "Gissar zoti. Semiz, sog'lom.",1,1),
        (uids['bobur'],'Sut sigiri — Simmental','sigir','🐄',"Sigir",15000000,
         "Farg'ona","Farg'ona sh.",'5 yosh',"Urg'ochi",'Simmental',1,'420 kg',
         "Oyiga 700 litr sut. Hujjatlar mavjud.",1,0),
        (uids['aziz'],"O'rdak (10 bosh)",'o_rdak','🦆',"O'rdak",800000,
         "Toshkent vil.",'Chinoz','3 oylik','Aralash','Pekin zoti',10,'1.8 kg',
         "Pekin zoti. Ozuqa bilan birga.",1,0),
        (uids['malika'],"G'oz (6 bosh)",'g_oz','🪿',"G'oz",1500000,
         'Buxoro','Shofirkon','4 oylik','Aralash','Oddiy',6,'3 kg',
         "Katta g'ozlar.",1,0),
    ]
    for i,l in enumerate(listings):
        db.execute("""INSERT INTO listings
            (user_id,title,animal_slug,animal_emoji,animal_name,price,region,district,
             age,gender,breed,count,weight,description,is_active,is_premium,views)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            l[:16] + (secrets.randbelow(300)+20,))
    # Demo reviews
    db.execute("INSERT INTO reviews (from_id,to_id,rating,body) VALUES (?,?,?,?)",
               (uids['aziz'],uids['sardor'],5,"Juda ishonchli sotuvchi! Hayvon tasvirda ko'ringanidek."))
    db.execute("INSERT INTO reviews (from_id,to_id,rating,body) VALUES (?,?,?,?)",
               (uids['malika'],uids['sardor'],5,"Tez javob berdi. Hammasi yaxshi bo'ldi."))
    db.execute("INSERT INTO reviews (from_id,to_id,rating,body) VALUES (?,?,?,?)",
               (uids['sardor'],uids['aziz'],4,"Yaxshi sotuvchi, hayvon sog'lom edi."))

# ─── Auth helpers ──────────────────────────────────────────────
def hp(p): return hashlib.sha256(p.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def deco(*a,**kw):
        if 'uid' not in session:
            flash("Iltimos avval tizimga kiring", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*a,**kw)
    return deco

def admin_required(f):
    @wraps(f)
    def deco(*a,**kw):
        u = _me()
        if not u or not u['is_admin']:
            abort(403)
        return f(*a,**kw)
    return deco

def _me():
    if 'uid' in session:
        return get_db().execute("SELECT * FROM users WHERE id=?", (session['uid'],)).fetchone()
    return None

@app.context_processor
def _ctx():
    u = _me()
    unread = favs = 0
    if u:
        unread = get_db().execute("SELECT COUNT(*) FROM messages WHERE to_id=? AND is_read=0",(u['id'],)).fetchone()[0]
        favs   = get_db().execute("SELECT COUNT(*) FROM favorites WHERE user_id=?",(u['id'],)).fetchone()[0]
    return dict(me=u, unread=unread, fav_count=favs,
                animal_types=ANIMAL_TYPES, regions=REGIONS,
                animal_images=ANIMAL_IMAGES,
                now=datetime.now())

def fmt(v):
    try: return f"{int(v):,}".replace(',',' ')
    except: return str(v)
app.jinja_env.filters['fmt'] = fmt
app.jinja_env.filters['stars'] = lambda r: '⭐'*int(r or 5)+'☆'*(5-int(r or 5))

# ─── HOME ──────────────────────────────────────────────────────
@app.route('/')
def home():
    db = get_db()
    try:
        premium = db.execute("""SELECT l.*,u.full_name,u.rating,u.is_verified,u.username
            FROM listings l JOIN users u ON l.user_id=u.id
            WHERE l.is_active=1 AND l.is_sold=0 AND l.is_premium=1
            ORDER BY l.created_at DESC LIMIT 4""").fetchall()
    except:
        premium = []
    try:
        recent = db.execute("""SELECT l.*,u.full_name,u.rating,u.is_verified,u.username
            FROM listings l JOIN users u ON l.user_id=u.id
            WHERE l.is_active=1 AND l.is_sold=0
            ORDER BY l.created_at DESC LIMIT 8""").fetchall()
    except:
        recent = []
    stats = dict(
        listings = db.execute("SELECT COUNT(*) FROM listings WHERE is_active=1").fetchone()[0],
        users    = db.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
        sold     = db.execute("SELECT COUNT(*) FROM listings WHERE is_sold=1").fetchone()[0]+120,
        regions  = len(REGIONS),
    )
    top = db.execute("SELECT * FROM users WHERE is_admin=0 ORDER BY total_sales DESC LIMIT 4").fetchall()
    return render_template('main/home.html', premium=premium, recent=recent, stats=stats, top=top)

# ─── CATALOG ────────────────────────────────────────────────────
@app.route('/catalog')
def catalog():
    db   = get_db()
    q    = request.args.get('q','').strip()
    atype= request.args.get('type','')
    reg  = request.args.get('region','')
    minp = request.args.get('min','')
    maxp = request.args.get('max','')
    sort = request.args.get('sort','new')
    page = max(1,int(request.args.get('page','1') or 1))
    per  = 12

    sql  = """SELECT l.*,u.full_name,u.rating,u.is_verified,u.username
              FROM listings l JOIN users u ON l.user_id=u.id
              WHERE l.is_active=1 AND l.is_sold=0"""
    prm  = []
    if q:     sql+=" AND (l.title LIKE ? OR l.breed LIKE ? OR l.description LIKE ?)"; prm+=[f'%{q}%']*3
    if atype: sql+=" AND l.animal_slug=?"; prm.append(atype)
    if reg:   sql+=" AND l.region=?"; prm.append(reg)
    if minp:  sql+=" AND l.price>=?"; prm.append(int(minp))
    if maxp:  sql+=" AND l.price<=?"; prm.append(int(maxp))
    ord_map = {'new':'l.created_at DESC','price_asc':'l.price ASC',
               'price_desc':'l.price DESC','popular':'l.views DESC'}
    sql += f" ORDER BY l.is_premium DESC,{ord_map.get(sort,'l.created_at DESC')}"

    all_items = db.execute(sql,prm).fetchall()
    total = len(all_items)
    pages = max(1,(total+per-1)//per)
    items = all_items[(page-1)*per:page*per]
    return render_template('main/catalog.html', items=items, total=total,
                           pages=pages, page=page, q=q, atype=atype,
                           reg=reg, minp=minp, maxp=maxp, sort=sort)

# ─── DELIVERY CATALOG ────────────────────────────────────────────
UZBEKISTAN_DISTRICTS = {
    "Toshkent sh.": ["Yakkasaroy","Mirzo Ulug'bek","Yunusobod","Chilonzor","Uchtepa","Sergeli","Olmazor","Shayxontohur","Mirobod","Bektemir","Yashnobod","Zangiota"],
    "Toshkent vil.": ["Nurafshon","Olmaliq","Angren","Chirchiq","Bo'ka","Ohangaron","Parkent","Piskent","Qibray","Toshloq","Zangiota","Bostonliq","Orta Chirchiq","Yuqori Chirchiq","Quyi Chirchiq"],
    "Samarqand": ["Samarqand sh.","Urgut","Kattaqo'rg'on","Ishtixon","Jomboy","Payariq","Pastdarg'om","Oqdaryo","Bulungur","Narpay","Toyloq","Nurobod","Paxtachi","Qo'shrabot"],
    "Buxoro": ["Buxoro sh.","G'ijduvon","Kogon","Qorovulbozor","Romitan","Shofirkon","Vobkent","Jondor","Olot","Peshku","Qorako'l"],
    "Andijon": ["Andijon sh.","Asaka","Xonobod","Oltinko'l","Baliqchi","Bo'z","Buloqboshi","Izboskan","Jalaquduq","Ulug'nor","Marxamat","Paxtaobod","Qo'rg'ontepa","Shahrixon"],
    "Farg'ona": ["Farg'ona sh.","Marg'ilon","Qo'qon","Quva","Rishton","O'zbekiston","Dang'ara","Bag'dod","Beshariq","Buvayda","Furqat","Hamza","Oltiariq","Toshloq","Uchko'prik","Yozyovon"],
    "Namangan": ["Namangan sh.","Chortoq","Chust","Kosonsoy","Mingbuloq","Norin","Pop","To'raqo'rg'on","Uychi","Yangiqo'rg'on"],
    "Qashqadaryo": ["Qarshi sh.","Shahrisabz","G'uzor","Kasbi","Kitob","Ko'kdala","Mirishkor","Muborak","Nishon","Qamashi","Chiroqchi","Dehqonobod","Guzor","Yakkabog'"],
    "Surxondaryo": ["Termiz sh.","Boysun","Denov","Jarqo'rg'on","Qiziriq","Muzrabot","Oltinsoy","Sariosiyo","Sherobod","Shurchi","Uzun","Bandixon","Kumqo'rg'on","Angor"],
    "Xorazm": ["Urganch sh.","Xiva","Bog'ot","Gurlan","Hazorasp","Xonqa","Qo'shko'pir","Shovot","Tuproqqal'a","Yangiariq","Yangibozor"],
    "Navoiy": ["Navoiy sh.","Zarafshon","Karmana","Konimex","Nurota","Qiziltepa","Tomdi","Uchquduq","Xatirchi"],
    "Jizzax": ["Jizzax sh.","G'allaorol","Arnasoy","Baxmal","Do'stlik","Forish","Mirzacho'l","Paxtakor","Sharof Rashidov","Yangiobod","Zarbdor","Zafar"],
    "Sirdaryo": ["Guliston sh.","Baxt","Boyovut","Gulliston","Mirzaobod","Oqoltin","Sardoba","Sayxunobod","Shirin","Xovos"],
    "Qoraqalpog'iston": ["Nukus sh.","Beruniy","Chimboy","Ellikkala","Kegeyli","Mo'ynoq","Qonliko'l","Qorao'zak","Shumanay","Taxtako'pir","To'rtko'l","Xo'jayli"],
}

@app.route('/delivery')
def delivery():
    db = get_db()
    region = request.args.get('region', '')
    district = request.args.get('district', '')
    q = request.args.get('q', '').strip()
    atype = request.args.get('type', '')
    page = max(1, int(request.args.get('page', '1') or 1))
    per = 12

    sql = """SELECT l.*,u.full_name,u.rating,u.is_verified,u.username
             FROM listings l JOIN users u ON l.user_id=u.id
             WHERE l.is_active=1 AND l.is_sold=0"""
    prm = []
    if q:       sql += " AND (l.title LIKE ? OR l.description LIKE ?)"; prm += [f'%{q}%']*2
    if atype:   sql += " AND l.animal_slug=?"; prm.append(atype)
    if region:  sql += " AND l.region=?"; prm.append(region)
    if district: sql += " AND l.district=?"; prm.append(district)
    sql += " ORDER BY l.is_premium DESC, l.created_at DESC"

    all_items = db.execute(sql, prm).fetchall()
    total = len(all_items)
    pages = max(1, (total + per - 1) // per)
    items = all_items[(page-1)*per:page*per]

    districts = UZBEKISTAN_DISTRICTS.get(region, []) if region else []

    return render_template('main/delivery.html',
                           items=items, total=total, pages=pages, page=page,
                           q=q, atype=atype, region=region, district=district,
                           regions=REGIONS, districts=districts,
                           all_districts=UZBEKISTAN_DISTRICTS,
                           animal_types=ANIMAL_TYPES)

# ─── LISTING DETAIL ─────────────────────────────────────────────
@app.route('/listing/<int:lid>')
def listing(lid):
    db = get_db()
    item = db.execute("""SELECT l.*,u.full_name,u.phone,u.rating,u.is_verified,
                                u.username,u.id as seller_id,u.bio,u.total_sales,u.avatar_letter
                         FROM listings l JOIN users u ON l.user_id=u.id WHERE l.id=?""",(lid,)).fetchone()
    if not item: abort(404)
    db.execute("UPDATE listings SET views=views+1 WHERE id=?",(lid,)); db.commit()
    related = db.execute("""SELECT l.*,u.full_name,u.rating,u.username
        FROM listings l JOIN users u ON l.user_id=u.id
        WHERE l.is_active=1 AND l.animal_slug=? AND l.id!=? AND l.is_sold=0
        ORDER BY l.views DESC LIMIT 3""",(item['animal_slug'],lid)).fetchall()
    seller_other = db.execute("""SELECT * FROM listings
        WHERE user_id=? AND is_active=1 AND id!=? AND is_sold=0 LIMIT 3""",
        (item['seller_id'],lid)).fetchall()
    is_fav = False
    if 'uid' in session:
        is_fav = bool(db.execute("SELECT 1 FROM favorites WHERE user_id=? AND listing_id=?",
                                 (session['uid'],lid)).fetchone())
    rev = db.execute("""SELECT r.*,u.full_name,u.username,u.avatar_letter FROM reviews r
        JOIN users u ON r.from_id=u.id WHERE r.to_id=? ORDER BY r.created_at DESC""",(item['seller_id'],)).fetchall()
    return render_template('main/listing.html', item=item, related=related,
                           seller_other=seller_other, is_fav=is_fav, reviews=rev,
                           delivery_persons=DELIVERY_PERSONS, vets=VETS)

# ─── DELIVERY REVIEW ────────────────────────────────────────────
@app.route('/delivery-review', methods=['POST'])
def delivery_review():
    if not session.get('uid'):
        flash('Iltimos tizimga kiring', 'error')
        return redirect('/login')
    pid  = request.form.get('person_id','')
    rat  = int(request.form.get('rating', 5))
    body = request.form.get('body','').strip()
    flash(f'✅ Yetkazib beruvchiga sharhingiz qabul qilindi! Reyting: {"⭐"*rat}', 'success')
    return redirect(request.referrer or '/catalog')

# ─── VET REVIEW ─────────────────────────────────────────────────
@app.route('/vet-review', methods=['POST'])
def vet_review():
    if not session.get('uid'):
        flash('Iltimos tizimga kiring', 'error')
        return redirect('/login')
    vid  = request.form.get('vet_id','')
    rat  = int(request.form.get('rating', 5))
    body = request.form.get('body','').strip()
    flash(f'✅ Veterinarga sharhingiz qabul qilindi! Reyting: {"⭐"*rat}', 'success')
    return redirect(request.referrer or '/catalog')

# ─── NEW LISTING ────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_IMG = {'png','jpg','jpeg','webp','gif'}
ALLOWED_VID = {'mp4','mov','avi','webm'}

def save_files(files, folder, allowed):
    saved = []
    os.makedirs(folder, exist_ok=True)
    for f in files:
        if f and f.filename:
            ext = f.filename.rsplit('.',1)[-1].lower()
            if ext in allowed:
                fname = secrets.token_hex(8) + '.' + ext
                f.save(os.path.join(folder, fname))
                saved.append(fname)
    return saved

@app.route('/listing/new', methods=['GET','POST'])
@login_required
def new_listing():
    if request.method == 'POST':
        db    = get_db()
        title = request.form.get('title','').strip()
        aslug = request.form.get('animal_slug','')
        price = int(request.form.get('price',0) or 0)
        region= request.form.get('region','')
        if not all([title,aslug,price,region]):
            flash("Barcha majburiy maydonlarni to'ldiring",'error')
            return render_template('main/new_listing.html', animal_types=ANIMAL_TYPES, regions=REGIONS)
        em = {s:e for s,e,_ in ANIMAL_TYPES}.get(aslug,'🐾')
        an = {s:n for s,_,n in ANIMAL_TYPES}.get(aslug,'')
        # Handle photos
        photos = save_files(request.files.getlist('photos'), UPLOAD_FOLDER, ALLOWED_IMG)
        photos_str = ','.join(photos)
        # Handle video
        videos = save_files(request.files.getlist('video'), UPLOAD_FOLDER, ALLOWED_VID)
        video_str = videos[0] if videos else ''
        db.execute("""INSERT INTO listings
            (user_id,title,animal_slug,animal_emoji,animal_name,price,region,
             district,age,gender,breed,count,weight,description,photos,video)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            session['uid'],title,aslug,em,an,price,region,
            request.form.get('district',''), request.form.get('age',''),
            request.form.get('gender',''), request.form.get('breed',''),
            int(request.form.get('count',1) or 1),
            request.form.get('weight',''), request.form.get('description','').strip(),
            photos_str, video_str,
        ))
        db.commit()
        lid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        flash("E'lon muvaffaqiyatli joylandi! 🎉",'success')
        return redirect(url_for('listing',lid=lid))
    return render_template('main/new_listing.html', animal_types=ANIMAL_TYPES, regions=REGIONS)

@app.route('/listing/<int:lid>/edit', methods=['GET','POST'])
@login_required
def edit_listing(lid):
    db   = get_db()
    item = db.execute("SELECT * FROM listings WHERE id=? AND user_id=?",(lid,session['uid'])).fetchone()
    if not item: abort(403)
    if request.method == 'POST':
        aslug = request.form.get('animal_slug', item['animal_slug'])
        em = {s:e for s,e,_ in ANIMAL_TYPES}.get(aslug,'🐾')
        an = {s:n for s,_,n in ANIMAL_TYPES}.get(aslug,'')
        db.execute("""UPDATE listings SET title=?,animal_slug=?,animal_emoji=?,animal_name=?,
                      price=?,region=?,district=?,age=?,gender=?,breed=?,count=?,weight=?,description=?
                      WHERE id=?""", (
            request.form.get('title',item['title']), aslug, em, an,
            int(request.form.get('price',item['price']) or 0),
            request.form.get('region',item['region']),
            request.form.get('district',''), request.form.get('age',''),
            request.form.get('gender',''), request.form.get('breed',''),
            int(request.form.get('count',1) or 1),
            request.form.get('weight',''), request.form.get('description','').strip(), lid,
        ))
        db.commit()
        flash("E'lon yangilandi ✅",'success')
        return redirect(url_for('listing',lid=lid))
    return render_template('main/edit_listing.html', item=item)

@app.route('/listing/<int:lid>/delete', methods=['POST'])
@login_required
def delete_listing(lid):
    db   = get_db()
    item = db.execute("SELECT * FROM listings WHERE id=?",(lid,)).fetchone()
    if not item: abort(404)
    u = _me()
    if item['user_id'] != session['uid'] and not u['is_admin']: abort(403)
    db.execute("DELETE FROM favorites WHERE listing_id=?",(lid,))
    db.execute("DELETE FROM listings WHERE id=?",(lid,))
    db.commit()
    flash("E'lon o'chirildi",'info')
    return redirect(url_for('my_listings') if item['user_id']==session['uid'] else url_for('admin_listings'))

@app.route('/listing/<int:lid>/sold', methods=['POST'])
@login_required
def mark_sold(lid):
    db = get_db()
    db.execute("UPDATE listings SET is_sold=1,is_active=0 WHERE id=? AND user_id=?",(lid,session['uid']))
    db.execute("UPDATE users SET total_sales=total_sales+1 WHERE id=?",(session['uid'],))
    db.commit()
    flash("E'lon 'Sotildi' deb belgilandi ✅",'success')
    return redirect(url_for('my_listings'))

# ─── FAVORITES ──────────────────────────────────────────────────
@app.route('/favorites')
@login_required
def favorites():
    items = get_db().execute("""SELECT l.*,u.full_name,u.rating,u.username
        FROM favorites f JOIN listings l ON f.listing_id=l.id
        JOIN users u ON l.user_id=u.id
        WHERE f.user_id=? ORDER BY f.id DESC""",(session['uid'],)).fetchall()
    return render_template('main/favorites.html', items=items)

@app.route('/favorites/toggle/<int:lid>', methods=['POST'])
@login_required
def toggle_fav(lid):
    db = get_db()
    ex = db.execute("SELECT 1 FROM favorites WHERE user_id=? AND listing_id=?",
                    (session['uid'],lid)).fetchone()
    if ex:
        db.execute("DELETE FROM favorites WHERE user_id=? AND listing_id=?",(session['uid'],lid))
        action='removed'
    else:
        db.execute("INSERT OR IGNORE INTO favorites(user_id,listing_id) VALUES(?,?)",(session['uid'],lid))
        action='added'
    db.commit()
    cnt = db.execute("SELECT COUNT(*) FROM favorites WHERE user_id=?",(session['uid'],)).fetchone()[0]
    if request.headers.get('X-Requested-With')=='XMLHttpRequest':
        return jsonify({'action':action,'count':cnt})
    return redirect(request.referrer or url_for('favorites'))

# ─── MESSAGES ────────────────────────────────────────────────────
@app.route('/messages')
@login_required
def messages():
    db = get_db()
    convs = db.execute("""
        SELECT u.id,u.full_name,u.username,u.avatar_letter,
               MAX(m.created_at) as last_time,
               SUM(CASE WHEN m.to_id=? AND m.is_read=0 THEN 1 ELSE 0 END) as unread_cnt,
               (SELECT m2.body FROM messages m2
                WHERE (m2.from_id=u.id AND m2.to_id=?) OR (m2.from_id=? AND m2.to_id=u.id)
                ORDER BY m2.created_at DESC LIMIT 1) as last_msg
        FROM messages m
        JOIN users u ON (CASE WHEN m.from_id=? THEN m.to_id ELSE m.from_id END)=u.id
        WHERE m.from_id=? OR m.to_id=?
        GROUP BY u.id ORDER BY last_time DESC""",
        (session['uid'],session['uid'],session['uid'],
         session['uid'],session['uid'],session['uid'])).fetchall()
    return render_template('main/messages.html', convs=convs)

@app.route('/messages/<int:uid>', methods=['GET','POST'])
@login_required
def chat(uid):
    db    = get_db()
    other = db.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if not other: abort(404)
    if request.method == 'POST':
        body = request.form.get('body','').strip()
        lid  = request.form.get('listing_id') or None
        if body:
            db.execute("INSERT INTO messages(from_id,to_id,listing_id,body) VALUES(?,?,?,?)",
                       (session['uid'],uid,lid,body))
            db.commit()
        return redirect(url_for('chat',uid=uid))
    db.execute("UPDATE messages SET is_read=1 WHERE from_id=? AND to_id=?",(uid,session['uid']))
    db.commit()
    msgs = db.execute("""SELECT m.*,u.full_name,u.avatar_letter FROM messages m
        JOIN users u ON m.from_id=u.id
        WHERE (m.from_id=? AND m.to_id=?) OR (m.from_id=? AND m.to_id=?)
        ORDER BY m.created_at""",(session['uid'],uid,uid,session['uid'])).fetchall()
    lid = request.args.get('listing_id')
    listing_ref = get_db().execute("SELECT * FROM listings WHERE id=?",(lid,)).fetchone() if lid else None
    return render_template('main/chat.html', other=other, msgs=msgs, listing_ref=listing_ref)

# ─── PROFILE ─────────────────────────────────────────────────────
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    db = get_db()
    if request.method == 'POST':
        fn = request.form.get('full_name','').strip()
        db.execute("UPDATE users SET full_name=?,phone=?,region=?,email=?,bio=?,avatar_letter=? WHERE id=?",
                   (fn,
                    request.form.get('phone','').strip(),
                    request.form.get('region',''),
                    request.form.get('email','').strip(),
                    request.form.get('bio','').strip(),
                    fn[0].upper() if fn else '?',
                    session['uid']))
        op = request.form.get('old_password','')
        np = request.form.get('new_password','')
        if op and np:
            u = db.execute("SELECT * FROM users WHERE id=? AND password=?",
                           (session['uid'],hp(op))).fetchone()
            if u:
                db.execute("UPDATE users SET password=? WHERE id=?",(hp(np),session['uid']))
                flash("Parol o'zgartirildi ✅",'success')
            else:
                flash("Eski parol noto'g'ri",'error')
        db.commit()
        flash("Profil yangilandi ✅",'success')
        return redirect(url_for('profile'))
    user = db.execute("SELECT * FROM users WHERE id=?",(session['uid'],)).fetchone()
    return render_template('main/profile.html', user=user)

@app.route('/my-listings')
@login_required
def my_listings():
    items = get_db().execute("SELECT * FROM listings WHERE user_id=? ORDER BY created_at DESC",
                             (session['uid'],)).fetchall()
    return render_template('main/my_listings.html', items=items)

@app.route('/user/<username>')
def user_page(username):
    db   = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
    if not user: abort(404)
    items = db.execute("""SELECT * FROM listings WHERE user_id=? AND is_active=1 AND is_sold=0
                          ORDER BY is_premium DESC,created_at DESC""",(user['id'],)).fetchall()
    revs  = db.execute("""SELECT r.*,u.full_name,u.username,u.avatar_letter FROM reviews r
        JOIN users u ON r.from_id=u.id WHERE r.to_id=? ORDER BY r.created_at DESC""",(user['id'],)).fetchall()
    avg   = db.execute("SELECT AVG(rating) FROM reviews WHERE to_id=?",(user['id'],)).fetchone()[0]
    return render_template('main/user.html', user=user, items=items,
                           reviews=revs, avg=round(avg or 5.0,1))

@app.route('/user/<int:uid>/review', methods=['POST'])
@login_required
def add_review(uid):
    db = get_db()
    rating = int(request.form.get('rating',5))
    body   = request.form.get('body','').strip()
    if uid == session['uid']:
        flash("O'zingizga baho bera olmaysiz",'error')
        return redirect(request.referrer or url_for('home'))
    db.execute("INSERT INTO reviews(from_id,to_id,rating,body) VALUES(?,?,?,?)",
               (session['uid'],uid,rating,body))
    avg = db.execute("SELECT AVG(rating) FROM reviews WHERE to_id=?",(uid,)).fetchone()[0]
    db.execute("UPDATE users SET rating=? WHERE id=?",(round(avg,1),uid))
    db.commit()
    flash("Sharh qo'shildi ✅",'success')
    return redirect(request.referrer or url_for('home'))

# ─── AUTH ─────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if 'uid' in session: return redirect(url_for('home'))
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        pwd   = request.form.get('password','').strip()
        user  = get_db().execute("SELECT * FROM users WHERE username=? AND password=?",
                                 (uname,hp(pwd))).fetchone()
        if user:
            if user['is_banned']:
                flash("Sizning hisobingiz bloklangan. Admin bilan bog'laning.",'error')
                return render_template('main/login.html')
            session['uid'] = user['id']
            session.permanent = True
            flash(f"Xush kelibsiz, {user['full_name'] or user['username']}! 👋",'success')
            return redirect(request.args.get('next') or url_for('home'))
        flash("Login yoki parol noto'g'ri",'error')
    return render_template('main/login.html')

@app.route('/logout')
def logout():
    session.pop('uid',None)
    flash("Tizimdan chiqildi 👋",'info')
    return redirect(url_for('home'))

@app.route('/auth/google')
def google_login():
    params = urllib.parse.urlencode({
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
    })
    return redirect(f'https://accounts.google.com/o/oauth2/v2/auth?{params}')

@app.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        flash("Google orqali kirishda xatolik", 'error')
        return redirect(url_for('login'))
    try:
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }).encode()
        req = urllib.request.Request('https://oauth2.googleapis.com/token', data=token_data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        with urllib.request.urlopen(req) as resp:
            token_json = json.loads(resp.read())
        access_token = token_json.get('access_token')
        req2 = urllib.request.Request(f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}')
        with urllib.request.urlopen(req2) as resp2:
            info = json.loads(resp2.read())
        google_id = info.get('id','')
        email     = info.get('email','')
        full_name = info.get('name','')
        picture   = info.get('picture','')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE google_id=?", (google_id,)).fetchone()
        if user:
            session['uid'] = user['id']
            flash(f"Xush kelibsiz, {user['full_name'] or user['username']}! 👋", 'success')
            return redirect(url_for('home'))
        user_by_email = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user_by_email:
            db.execute("UPDATE users SET google_id=? WHERE id=?", (google_id, user_by_email['id']))
            db.commit()
            session['uid'] = user_by_email['id']
            flash(f"Xush kelibsiz, {user_by_email['full_name']}! 👋", 'success')
            return redirect(url_for('home'))
        base_username = re.sub(r'[^a-z0-9]', '', email.split('@')[0].lower()) or 'user'
        username = base_username
        counter = 1
        while db.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
            username = f"{base_username}{counter}"
            counter += 1
        avatar = full_name[0].upper() if full_name else 'G'
        db.execute("""INSERT INTO users(username,password,full_name,email,avatar_letter,google_id,is_verified)
                      VALUES(?,?,?,?,?,?,1)""",
                   (username, 'GOOGLE_AUTH', full_name, email, avatar, google_id))
        db.commit()
        uid = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
        session['uid'] = uid
        flash(f"Xush kelibsiz, {full_name}! Google orqali ro'yxatdan o'tdingiz 🎉", 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash(f"Google orqali kirishda xatolik: {str(e)}", 'error')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if 'uid' in session: return redirect(url_for('home'))
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        fn    = request.form.get('full_name','').strip()
        phone = request.form.get('phone','').strip()
        reg   = request.form.get('region','')
        pwd   = request.form.get('password','').strip()
        pwd2  = request.form.get('password2','').strip()
        if not all([uname,fn,phone,reg,pwd]):
            flash("Barcha maydonlarni to'ldiring",'error')
        elif pwd != pwd2:
            flash("Parollar mos emas",'error')
        elif len(pwd) < 6:
            flash("Parol kamida 6 ta belgi",'error')
        elif get_db().execute("SELECT 1 FROM users WHERE username=?",(uname,)).fetchone():
            flash("Bu login band, boshqasini tanlang",'error')
        else:
            db = get_db()
            role = request.form.get('role','buyer')
            db.execute("INSERT INTO users(username,password,full_name,phone,region,avatar_letter,role) VALUES(?,?,?,?,?,?,?)",
                       (uname,hp(pwd),fn,phone,reg,fn[0].upper() if fn else '?',role))
            db.commit()
            uid = db.execute("SELECT id FROM users WHERE username=?",(uname,)).fetchone()[0]
            session['uid'] = uid
            flash(f"Xush kelibsiz, {fn}! Ro'yxatdan o'tdingiz 🎉",'success')
            return redirect(url_for('home'))
    return render_template('main/register.html')

# ─── SEARCH API ───────────────────────────────────────────────────
@app.route('/api/search')
def api_search():
    q = request.args.get('q','').strip()
    if len(q)<2: return jsonify([])
    r = get_db().execute("""SELECT id,title,animal_emoji,price,region FROM listings
        WHERE (title LIKE ? OR breed LIKE ?) AND is_active=1 AND is_sold=0 LIMIT 6""",
        (f'%{q}%',f'%{q}%')).fetchall()
    return jsonify([dict(id=x['id'],title=x['title'],emoji=x['animal_emoji'],
                         price=x['price'],region=x['region']) for x in r])

# ─── ABOUT / CONTACT ──────────────────────────────────────────────
@app.route('/about')
def about():
    return render_template('main/about.html')

@app.route('/contact')
def contact():
    return render_template('main/contact.html')

# ─── ADMIN ────────────────────────────────────────────────────────
@app.route('/admin/')
@login_required
@admin_required
def admin_index():
    db = get_db()
    stats = dict(
        users    = db.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
        listings = db.execute("SELECT COUNT(*) FROM listings").fetchone()[0],
        active   = db.execute("SELECT COUNT(*) FROM listings WHERE is_active=1").fetchone()[0],
        sold     = db.execute("SELECT COUNT(*) FROM listings WHERE is_sold=1").fetchone()[0],
        msgs     = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        reviews  = db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
    )
    recent_users = db.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 8").fetchall()
    recent_listings = db.execute("""SELECT l.*,u.username FROM listings l JOIN users u ON l.user_id=u.id
        ORDER BY l.created_at DESC LIMIT 10""").fetchall()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_users=recent_users, recent_listings=recent_listings)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    q = request.args.get("q","")
    if q:
        users = get_db().execute("SELECT * FROM users WHERE username LIKE ? OR full_name LIKE ? ORDER BY created_at DESC",("%"+q+"%","%"+q+"%")).fetchall()
    else:
        users = get_db().execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return render_template("admin/users.html", users=users, q=q)

@app.route('/admin/users/<int:uid>/verify', methods=['POST'])
@login_required
@admin_required
def admin_verify(uid):
    db = get_db()
    u  = db.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if u:
        db.execute("UPDATE users SET is_verified=? WHERE id=?",(0 if u['is_verified'] else 1,uid))
        db.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:uid>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(uid):
    if uid == session['uid']:
        flash("O'zingizni o'chira olmaysiz",'error')
        return redirect(url_for('admin_users'))
    db = get_db()
    db.execute("DELETE FROM listings WHERE user_id=?",(uid,))
    db.execute("DELETE FROM messages WHERE from_id=? OR to_id=?",(uid,uid))
    db.execute("DELETE FROM favorites WHERE user_id=?",(uid,))
    db.execute("DELETE FROM reviews WHERE from_id=? OR to_id=?",(uid,uid))
    db.execute("DELETE FROM users WHERE id=?",(uid,))
    db.commit()
    flash("Foydalanuvchi o'chirildi",'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/listings')
@login_required
@admin_required
def admin_listings():
    items = get_db().execute("""SELECT l.*,u.username,u.full_name FROM listings l
        JOIN users u ON l.user_id=u.id ORDER BY l.created_at DESC""").fetchall()
    return render_template('admin/listings.html', items=items)

@app.route('/admin/listings/<int:lid>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_listing(lid):
    db = get_db()
    item = db.execute("SELECT * FROM listings WHERE id=?",(lid,)).fetchone()
    if item:
        db.execute("UPDATE listings SET is_active=?,is_premium=? WHERE id=?",
                   (0 if item['is_active'] else 1,
                    1 if request.form.get('premium') else item['is_premium'], lid))
        db.commit()
    return redirect(url_for('admin_listings'))

@app.route('/admin/users/<int:uid>/ban', methods=['POST'])
@login_required
@admin_required
def admin_ban(uid):
    if uid == session['uid']:
        flash("O'zingizni ban qila olmaysiz",'error')
        return redirect(url_for('admin_users'))
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if u:
        db.execute("UPDATE users SET is_banned=? WHERE id=?",(0 if u['is_banned'] else 1, uid))
        db.commit()
        flash(f"{'Foydalanuvchi ban qilindi' if not u['is_banned'] else 'Ban olindi'}",'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:uid>/make-admin', methods=['POST'])
@login_required
@admin_required
def admin_make_admin(uid):
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    if u:
        db.execute("UPDATE users SET is_admin=? WHERE id=?",(0 if u['is_admin'] else 1, uid))
        db.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/listings/<int:lid>/premium', methods=['POST'])
@login_required
@admin_required
def admin_premium(lid):
    db = get_db()
    item = db.execute("SELECT * FROM listings WHERE id=?",(lid,)).fetchone()
    if item:
        db.execute("UPDATE listings SET is_premium=? WHERE id=?",(0 if item['is_premium'] else 1, lid))
        db.commit()
    return redirect(url_for('admin_listings'))

@app.route('/admin/stats-api')
@login_required
@admin_required
def admin_stats_api():
    db = get_db()
    return jsonify({
        'users': db.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0],
        'listings': db.execute("SELECT COUNT(*) FROM listings").fetchone()[0],
        'active': db.execute("SELECT COUNT(*) FROM listings WHERE is_active=1").fetchone()[0],
        'sold': db.execute("SELECT COUNT(*) FROM listings WHERE is_sold=1").fetchone()[0],
        'msgs': db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        'banned': db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0],
    })

@app.route('/admin/listings/<int:lid>/delete', methods=['POST'])
@login_required
@admin_required
def admin_del_listing(lid):
    db = get_db()
    db.execute("DELETE FROM favorites WHERE listing_id=?",(lid,))
    db.execute("DELETE FROM listings WHERE id=?",(lid,))
    db.commit()
    flash("E'lon o'chirildi",'info')
    return redirect(url_for('admin_listings'))

# ─── ERROR HANDLERS ──────────────────────────────────────────────
@app.errorhandler(404)
def e404(e): return render_template('main/404.html'), 404
@app.errorhandler(403)
def e403(e): return render_template('main/403.html'), 403

# ─── INIT DB on startup (works with gunicorn too) ────────────────
init_db()

# ─── RUN ─────────────────────────────────────────────────────────
if __name__=='__main__':
    print("\n"+"═"*54)
    print("  🐄  HayvonMarket ishga tushdi!")
    print("  →  http://127.0.0.1:5000")
    print("  →  Admin:  admin   / admin123")
    print("  →  Demo:   sardor  / demo123")
    print("═"*54+"\n")
    app.run(debug=os.environ.get("FLASK_DEBUG","false").lower()=="true", port=int(os.environ.get("PORT",5000)), host="0.0.0.0")
