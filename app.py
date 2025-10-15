from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import json

# --- إعدادات المسارات المطلقة ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')
UPLOAD_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
SETTINGS_FILE_PATH = os.path.join(BASE_DIR, 'settings.json')

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH
IQD_RATE = 1460

# --- نظام الترجمة ---
TRANSLATIONS = {
    'en': { 'home': 'Home', 'shop': 'Shop', 'free_games': 'Free Games', 'contact_us': 'Contact Us', 'sign_in': 'SIGN IN', 'dashboard': 'Dashboard', 'manage_admins': 'Manage Admins', 'logout': 'Logout', 'welcome': 'Welcome', 'add_new_game': 'Add New Game', 'shop_games': 'Shop Games', 'new_orders': 'New Purchase Orders', 'free_games_title': 'Free Games', 'customer_name': 'Customer Name', 'phone': 'Phone', 'game': 'Game', 'date': 'Date', 'actions': 'Actions', 'price': 'Price', 'edit': 'Edit', 'delete': 'Delete', 'order_form': 'Order Form', 'your_name': 'Your Full Name', 'your_phone': 'Your Phone Number', 'order_notice': 'We will contact you via phone to complete the purchase process.', 'place_order': 'Confirm Order', 'order_success_title': 'Order Received', 'order_success_msg': 'Thank you! Your order has been received successfully. We will contact you soon.', 'back_to_shop': 'Back to Shop', 'buy_now': 'Buy Now', 'get_now': 'Get Now', 'admin_login': 'Admin Login', 'no_new_orders': 'There are no new orders.', 'no_paid_games': 'No games have been added to the shop yet.', 'edit_index': 'Edit Home Page', 'view_messages': 'View Messages', 'no_free_games': 'No free games have been added yet.' },
    'ar': { 'home': 'الرئيسية', 'shop': 'المتجر', 'free_games': 'ألعاب مجانية', 'contact_us': 'تواصل معنا', 'sign_in': 'تسجيل الدخول', 'dashboard': 'لوحة التحكم', 'manage_admins': 'إدارة المشرفين', 'logout': 'تسجيل الخروج', 'welcome': 'أهلاً بك', 'add_new_game': 'إضافة لعبة جديدة', 'shop_games': 'ألعاب المتجر', 'new_orders': 'طلبات الشراء الجديدة', 'free_games_title': 'الألعاب المجانية', 'customer_name': 'اسم الزبون', 'phone': 'رقم الهاتف', 'game': 'اللعبة', 'date': 'التاريخ', 'actions': 'الإجراءات', 'price': 'السعر', 'edit': 'تعديل', 'delete': 'حذف', 'order_form': 'نموذج الطلب', 'your_name': 'اسمك الكامل', 'your_phone': 'رقم هاتفك', 'order_notice': 'سنتواصل معك عبر الهاتف لإكمال عملية الشراء.', 'place_order': 'تأكيد الطلب', 'order_success_title': 'تم استلام الطلب', 'order_success_msg': 'شكراً لك! لقد تم استلام طلبك بنجاح. سنتواصل معك قريباً.', 'back_to_shop': 'العودة للمتجر', 'buy_now': 'شراء الآن', 'get_now': 'احصل عليها الآن', 'admin_login': 'دخول المشرفين', 'no_new_orders': 'لا توجد طلبات شراء جديدة.', 'no_paid_games': 'لم تتم إضافة أي ألعاب للمتجر بعد.', 'edit_index': 'تعديل الصفحة الرئيسية', 'view_messages': 'عرض الرسائل', 'no_free_games': 'لم تتم إضافة أي ألعاب مجانية بعد.' }
}

# --- دوال مساعدة ---
@app.context_processor
def inject_global_vars():
    lang = session.get('language', 'en')
    unread_count = 0
    if 'admin_id' in session:
        try:
            conn = get_db_connection()
            count_cursor = conn.execute("SELECT COUNT(id) FROM messages WHERE is_read = 0")
            result = count_cursor.fetchone()
            if result:
                unread_count = result[0]
            conn.close()
        except Exception as e:
            print(f"Error fetching unread count: {e}")
            unread_count = 0
    
    def get_text(key):
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
        
    return dict(get_text=get_text, currency=session.get('currency', 'USD'), IQD_RATE=IQD_RATE, endpoint=request.endpoint, unread_count=unread_count)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_index_settings():
    try:
        with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'title_part1': 'YOUR NEXT', 'title_part2': 'ADVENTURE', 'title_part3': 'AWAITS', 'subtitle': 'The premium hub for exclusive game accounts.', 'discount': '70'}

# --- تهيئة قاعدة البيانات ---
def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT, price REAL NOT NULL, category TEXT, image_filename TEXT, is_free BOOLEAN NOT NULL DEFAULT 0, game_username TEXT, game_password TEXT);')
    conn.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);')
    conn.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL, game_id INTEGER NOT NULL, game_name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
    conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL, is_read BOOLEAN NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", ('admin',))
    if cursor.fetchone() is None:
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', hashed_password))
        conn.commit()
    conn.close()

init_db()

# --- الصفحات العامة ---
@app.route('/')
def index():
    settings = get_index_settings()
    return render_template('index.html', settings=settings)

@app.route('/shop')
def shop():
    conn = get_db_connection()
    games = conn.execute("SELECT * FROM games WHERE is_free = 0 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('shop.html', games=games)

@app.route('/free-games')
def free_games():
    conn = get_db_connection()
    games = conn.execute("SELECT * FROM games WHERE is_free = 1 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('free-games.html', games=games)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        with get_db_connection() as conn:
            conn.execute("INSERT INTO messages (name, email, message) VALUES (?, ?, ?)", (name, email, message))
            conn.commit()
        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/order/<int:game_id>', methods=['GET', 'POST'])
def order_form(game_id):
    conn = get_db_connection()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND is_free = 0", (game_id,)).fetchone()
    if game is None:
        conn.close()
        flash("This game is not available for purchase.", "error")
        return redirect(url_for('shop'))
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_phone = request.form['customer_phone']
        with get_db_connection() as conn_post:
            conn_post.execute("INSERT INTO orders (customer_name, customer_phone, game_id, game_name) VALUES (?, ?, ?, ?)", (customer_name, customer_phone, game_id, game['name']))
            conn_post.commit()
        return redirect(url_for('order_success'))
    conn.close()
    return render_template('order-form.html', game=game)

@app.route('/order-success')
def order_success():
    return render_template('order-success.html')

@app.route('/reveal/<int:game_id>')
def reveal_credentials(game_id):
    conn = get_db_connection()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND is_free = 1", (game_id,)).fetchone()
    conn.close()
    if game is None:
        flash("Sorry, this free game is not available.", "error")
        return redirect(url_for('free_games'))
    return render_template('reveal-credentials.html', game=game)

# --- صفحات المشرفين (Admin) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
    return render_template('admin-login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    shop_games = conn.execute("SELECT * FROM games WHERE is_free = 0 ORDER BY id DESC").fetchall()
    free_games = conn.execute("SELECT * FROM games WHERE is_free = 1 ORDER BY id DESC").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('dashboard.html', shop_games=shop_games, free_games=free_games, orders=orders)

@app.route('/add-game', methods=['POST'])
def add_game():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    file = request.files.get('image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        with get_db_connection() as conn:
            conn.execute("INSERT INTO games (name, price, description, category, image_filename, is_free, game_username, game_password) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (request.form['name'], float(request.form['price']), request.form['description'], request.form['category'], filename, 1 if 'is_free' in request.form else 0, request.form.get('game_username'), request.form.get('game_password')))
            conn.commit()
        flash(f"Game '{request.form['name']}' added successfully!", "success")
    else:
        flash("Image is a required field.", "error")
    return redirect(url_for('dashboard'))

@app.route('/edit-game/<int:game_id>', methods=['GET', 'POST'])
def edit_game(game_id):
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']; price = request.form['price']; description = request.form['description']
        category = request.form['category']; is_free = 1 if 'is_free' in request.form else 0
        game_username = request.form['game_username']; game_password = request.form['game_password']
        price_val = 0.0 if is_free else float(price)
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn.execute("UPDATE games SET image_filename = ? WHERE id = ?", (filename, game_id))
        conn.execute("UPDATE games SET name=?, price=?, description=?, category=?, is_free=?, game_username=?, game_password=? WHERE id=?", (name, price_val, description, category, is_free, game_username, game_password, game_id))
        conn.commit()
        conn.close()
        flash(f"Game '{name}' updated successfully!", "success")
        return redirect(url_for('dashboard'))
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    conn.close()
    if game is None:
        flash("Game not found!", "error")
        return redirect(url_for('dashboard'))
    return render_template('edit-game.html', game=game)

@app.route('/delete-game/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    with get_db_connection() as conn:
        conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
        conn.commit()
    flash("Game deleted successfully.", "success")
    return redirect(url_for('dashboard'))

@app.route('/manage-admins', methods=['GET', 'POST'])
def manage_admins():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_admin':
            username = request.form['username']
            password = request.form['password']
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            try:
                conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                flash(f"Admin '{username}' added successfully.", "success")
            except sqlite3.IntegrityError:
                flash(f"Username '{username}' already exists.", "error")
        elif action == 'delete_admin':
            admin_id_to_delete = request.form['admin_id']
            if int(admin_id_to_delete) != session['admin_id']:
                conn.execute("DELETE FROM admins WHERE id = ?", (admin_id_to_delete,))
                conn.commit()
                flash("Admin deleted successfully.", "success")
            else:
                flash("You cannot delete your own account.", "error")
        elif action == 'change_password':
            new_password = request.form['new_password']
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            conn.execute("UPDATE admins SET password = ? WHERE id = ?", (hashed_password, session['admin_id']))
            conn.commit()
            flash("Your password has been updated successfully.", "success")
        conn.close()
        return redirect(url_for('manage_admins'))
    admins = conn.execute("SELECT id, username FROM admins").fetchall()
    conn.close()
    return render_template('manage-admins.html', admins=admins)

@app.route('/edit-index', methods=['GET', 'POST'])
def edit_index():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    if request.method == 'POST':
        settings = {'title_part1': request.form['title_part1'], 'title_part2': request.form['title_part2'], 'title_part3': request.form['title_part3'], 'subtitle': request.form['subtitle'], 'discount': request.form['discount']}
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        file = request.files.get('home_image')
        if file and file.filename != '':
            filename = "home_image.png"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('Home page content updated successfully!', 'success')
        return redirect(url_for('edit_index'))
    settings = get_index_settings()
    return render_template('index-editor.html', settings=settings)
    
@app.route('/view-messages')
def view_messages():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    messages = conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall()
    conn.execute("UPDATE messages SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    conn.close()
    return render_template('view-messages.html', messages=messages)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- إعدادات اللغة والعملة ---
@app.route('/set-currency/<currency>')
def set_currency(currency):
    session['currency'] = currency
    return redirect(request.referrer or url_for('index'))
    
@app.route('/language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)