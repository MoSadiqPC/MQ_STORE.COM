from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
IQD_RATE = 1460 

# --- ## نظام الترجمة المبسط ## ---
TRANSLATIONS = {
    'en': { 'home': 'Home', 'shop': 'Shop', 'free_games': 'Free Games', 'contact_us': 'Contact Us', 'sign_in': 'SIGN IN', 'dashboard': 'Dashboard', 'manage_admins': 'Manage Admins', 'logout': 'Logout', 'welcome': 'Welcome', 'add_new_game': 'Add New Game', 'shop_games': 'Shop Games', 'new_orders': 'New Purchase Orders', 'free_games_title': 'Free Games', 'customer_name': 'Customer Name', 'phone': 'Phone', 'game': 'Game', 'date': 'Date', 'actions': 'Actions', 'price': 'Price', 'edit': 'Edit', 'delete': 'Delete' },
    'ar': { 'home': 'الرئيسية', 'shop': 'المتجر', 'free_games': 'ألعاب مجانية', 'contact_us': 'تواصل معنا', 'sign_in': 'تسجيل الدخول', 'dashboard': 'لوحة التحكم', 'manage_admins': 'إدارة المشرفين', 'logout': 'تسجيل الخروج', 'welcome': 'أهلاً بك', 'add_new_game': 'إضافة لعبة جديدة', 'shop_games': 'ألعاب المتجر', 'new_orders': 'طلبات الشراء الجديدة', 'free_games_title': 'الألعاب المجانية', 'customer_name': 'اسم الزبون', 'phone': 'رقم الهاتف', 'game': 'اللعبة', 'date': 'التاريخ', 'actions': 'الإجراءات', 'price': 'السعر', 'edit': 'تعديل', 'delete': 'حذف' }
}

@app.context_processor
def inject_global_vars():
    lang = session.get('language', 'en')
    def get_text(key):
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    return dict(get_text=get_text, currency=session.get('currency', 'USD'), IQD_RATE=IQD_RATE, endpoint=request.endpoint)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT, price REAL NOT NULL, category TEXT, image_filename TEXT, is_free BOOLEAN NOT NULL DEFAULT 0, game_username TEXT, game_password TEXT);')
    conn.execute('CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);')
    conn.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, customer_phone TEXT NOT NULL, game_id INTEGER NOT NULL, game_name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", ('admin',))
    if cursor.fetchone() is None:
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', hashed_password)); conn.commit()
    conn.close()

init_db()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/shop')
def shop():
    conn = get_db_connection()
    games = conn.execute("SELECT * FROM games WHERE is_free = 0 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('our-shop.html', games=games)

@app.route('/free-games')
def free_games():
    conn = get_db_connection()
    games = conn.execute("SELECT * FROM games WHERE is_free = 1 ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('free-games.html', games=games)

@app.route('/set-currency/<currency>')
def set_currency(currency):
    session['currency'] = currency
    return redirect(request.referrer or url_for('index'))
    
@app.route('/language/<lang>')
def set_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/reveal/<int:game_id>')
def reveal_credentials(game_id):
    conn = get_db_connection()
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    conn.close()
    if game is None:
        flash("Sorry, this game is not available.", "error"); return redirect(url_for('index'))
    return render_template('reveal-credentials.html', game=game)

@app.route('/order/<int:game_id>')
def order_form(game_id):
    conn = get_db_connection()
    game = conn.execute("SELECT * FROM games WHERE id = ? AND is_free = 0", (game_id,)).fetchone()
    conn.close()
    if game is None:
        flash("This game is not available for purchase.", "error"); return redirect(url_for('shop'))
    return render_template('order-form.html', game=game)
    
@app.route('/submit-order/<int:game_id>', methods=['POST'])
def submit_order(game_id):
    customer_name = request.form['customer_name']; customer_phone = request.form['customer_phone']
    conn = get_db_connection()
    game = conn.execute("SELECT name FROM games WHERE id = ?", (game_id,)).fetchone()
    if game:
        conn.execute("INSERT INTO orders (customer_name, customer_phone, game_id, game_name) VALUES (?, ?, ?, ?)", (customer_name, customer_phone, game_id, game['name'])); conn.commit()
    conn.close()
    flash("Thank you! Your order has been received. We will contact you shortly.", "success")
    return redirect(url_for('shop'))

@app.route('/contact')
def contact():
    return render_template('contact-us.html')

@app.route('/signin')
def signin(): return render_template('sign-in.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']
        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']; session['username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
    return render_template('admin.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    shop_games = conn.execute("SELECT * FROM games WHERE is_free = 0 ORDER BY id DESC").fetchall()
    free_games = conn.execute("SELECT * FROM games WHERE is_free = 1 ORDER BY id DESC").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('dashboard.html', shop_games=shop_games, free_games=free_games, orders=orders)
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add-game', methods=['POST'])
def add_game():
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    file = request.files.get('image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = get_db_connection()
        conn.execute("INSERT INTO games (name, price, description, category, image_filename, is_free, game_username, game_password) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (request.form['name'], float(request.form['price']), request.form['description'], request.form['category'], filename, 1 if 'is_free' in request.form else 0, request.form['game_username'], request.form['game_password']))
        conn.commit(); conn.close()
        flash(f"Game '{request.form['name']}' added successfully!", "success")
    else:
        flash("Image is a required field.", "error")
    return redirect(url_for('dashboard'))

@app.route('/delete-game/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM games WHERE id = ?", (game_id,)); conn.commit(); conn.close()
    flash("Game deleted successfully.", "success")
    return redirect(url_for('dashboard'))

@app.route('/edit-game/<int:game_id>', methods=['GET'])
def edit_game(game_id):
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    game = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    conn.close()
    if game is None:
        flash("Game not found!", "error"); return redirect(url_for('dashboard'))
    return render_template('edit-game.html', game=game)

@app.route('/update-game/<int:game_id>', methods=['POST'])
def update_game(game_id):
    if 'admin_id' not in session: return redirect(url_for('admin_login'))
    name = request.form['name']; price = request.form['price']; description = request.form['description']
    category = request.form['category']; is_free = 1 if 'is_free' in request.form else 0;
    game_username = request.form['game_username']; game_password = request.form['game_password']
    price_val = 0.0 if is_free else float(price)
    conn = get_db_connection()
    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn.execute("UPDATE games SET image_filename = ? WHERE id = ?", (filename, game_id))
    
    conn.execute("UPDATE games SET name=?, price=?, description=?, category=?, is_free=?, game_username=?, game_password=? WHERE id=?",
                 (name, price_val, description, category, is_free, game_username, game_password, game_id))
    conn.commit(); conn.close()
    flash(f"Game '{name}' updated successfully!", "success")
    return redirect(url_for('dashboard'))

# --- ## الكود الكامل والصحيح لهذه الوظيفة ## ---
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
                conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password)); conn.commit()
                flash(f"Admin '{username}' added successfully.", "success")
            except sqlite3.IntegrityError:
                flash(f"Username '{username}' already exists.", "error")
        elif action == 'delete_admin':
            admin_id_to_delete = request.form['admin_id']
            if int(admin_id_to_delete) != session['admin_id']:
                conn.execute("DELETE FROM admins WHERE id = ?", (admin_id_to_delete,)); conn.commit()
                flash("Admin deleted successfully.", "success")
            else:
                flash("You cannot delete your own account.", "error")
        elif action == 'change_password':
            new_password = request.form['new_password']
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            conn.execute("UPDATE admins SET password = ? WHERE id = ?", (hashed_password, session['admin_id'])); conn.commit()
            flash("Your password has been updated successfully.", "success")
    
    admins = conn.execute("SELECT id, username FROM admins").fetchall()
    conn.close()
    return render_template('manage-admins.html', admins=admins)

if __name__ == '__main__':
    app.run(debug=True)