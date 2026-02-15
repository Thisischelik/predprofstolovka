from flask import Flask, render_template, request, redirect, url_for, session, flash

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from cryptography.fernet import Fernet

from datetime import datetime, timedelta

import os

app = Flask(__name__, static_folder='templates', static_url_path='')

app.secret_key = '123' 


ENCRYPTION_KEY_PATH = os.path.join(os.path.dirname(__file__), 'encryption.key')
if not os.path.exists(ENCRYPTION_KEY_PATH):
    key = Fernet.generate_key()
    with open(ENCRYPTION_KEY_PATH, 'wb') as key_file:
        key_file.write(key)
else:
    with open(ENCRYPTION_KEY_PATH, 'rb') as key_file:
        key = key_file.read()

cipher_suite = Fernet(key)

basedir = os.path.abspath(os.path.dirname(__file__))

instance_path = os.path.join(basedir, 'instance')

if not os.path.exists(instance_path):

    os.makedirs(instance_path)

    

db_path = os.path.join(instance_path, 'users.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)

def get_msk_time():

    return datetime.utcnow() + timedelta(hours=3)

class Stud(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String, unique=True, nullable=False)

    fio = db.Column(db.String, nullable=False)

    password = db.Column(db.String(128), nullable=False)

    classes = db.Column(db.String, nullable=False)

    allergy = db.Column(db.String,)

    preferences = db.Column(db.String)

    balance = db.Column(db.Float, default=0.0)

class MealProduct(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    meal_type = db.Column(db.String, nullable=False)

    ingredients = db.Column(db.String, nullable=False)

class Chef(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String, nullable=True)

    password = db.Column(db.String(128), nullable=False)

class Adm(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String, nullable=True)

    password = db.Column(db.String(128), nullable=False)

class SavedCard(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    card_number = db.Column(db.Text, nullable=False) 

    card_holder = db.Column(db.String(100), nullable=False)

    expiry = db.Column(db.Text, nullable=False)      

    last_four = db.Column(db.String(4), nullable=False)

    def get_decrypted_number(self):
        try:
            return cipher_suite.decrypt(self.card_number.encode()).decode()
        except:
            return "Ошибка расшифровки"

    def get_decrypted_expiry(self):
        try:
            return cipher_suite.decrypt(self.expiry.encode()).decode()
        except:
            return "??/??"

    def get_masked_number(self):
        decrypted = self.get_decrypted_number()
        if len(decrypted) == 16:
            return f"{decrypted[:4]} **** **** {decrypted[-4:]}"
        return self.card_number 

class Transaction(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    amount = db.Column(db.Float, nullable=False)

    type = db.Column(db.String(20), default='Top-up')

    status = db.Column(db.String(20), default='Completed')

    timestamp = db.Column(db.DateTime, default=get_msk_time)

    card_used = db.Column(db.String(20))

class MealOrder(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    user_name = db.Column(db.String, nullable=True)

    meal_type = db.Column(db.String, nullable=False)

    price = db.Column(db.Float, nullable=False)

    timestamp = db.Column(db.DateTime, default=get_msk_time)

    is_issued = db.Column(db.Boolean, default=False)

class PurchaseRequest(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    item_name = db.Column(db.String, nullable=False)

    quantity = db.Column(db.Float, nullable=False)

    price = db.Column(db.Float, nullable=False)

    status = db.Column(db.String, default='Pending')

    chef_id = db.Column(db.Integer)

class Product(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, unique=True, nullable=False)

    quantity = db.Column(db.Float, default=0)

    price_per_unit = db.Column(db.Float, default=0.0)

    unit = db.Column(db.String(20), default='ед.')

class Feedback(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    user_role = db.Column(db.String(10))

    user_fio = db.Column(db.String(100))

    text = db.Column(db.Text, nullable=False)

    timestamp = db.Column(db.DateTime, default=get_msk_time)

RECIPES = {

    "Завтрак": {

        "Молоко": 0.2,

        "Крупа овсяная": 0.1,

        "Сахар": 0.02,

        "Яйцо": 1,

        "Сливочное масло": 0.01,

        "Соль": 0.005

    },

    "Обед": {

        "Мясо (говядина)": 0.15,

        "Картофель": 0.3,

        "Макароны": 0.1,

        "Лук": 0.03,

        "Морковь": 0.03,

        "Подсолнечное масло": 0.02,

        "Томатная паста": 0.01,

        "Соль": 0.01

    }

}

with app.app_context():

    db.create_all()

    if not Product.query.first():

        initial_products = [

            ("Молоко", 60, 80.0, "л"),

            ("Крупа овсяная", 30, 120.0, "кг"),

            ("Сахар", 15, 70.0, "кг"),

            ("Яйцо", 120, 12.0, "шт"),

            ("Сливочное масло", 10, 850.0, "кг"),

            ("Мясо (говядина)", 40, 650.0, "кг"),

            ("Картофель", 80, 45.0, "кг"),

            ("Макароны", 50, 90.0, "кг"),

            ("Лук", 20, 35.0, "кг"),

            ("Морковь", 20, 40.0, "кг"),

            ("Подсолнечное масло", 15, 110.0, "л"),

            ("Томатная паста", 10, 250.0, "кг"),

            ("Соль", 10, 25.0, "кг")

        ]

        for name, qty, price, unit in initial_products:

            db.session.add(Product(name=name, quantity=qty, price_per_unit=price, unit=unit))

        db.session.commit()

    

    if not Adm.query.filter_by(username="admin").first():

        admin_pwd = generate_password_hash("admin123")

        db.session.add(Adm(username="admin", password=admin_pwd))

        

    if not Chef.query.filter_by(username="chef").first():
        chef_pwd = generate_password_hash("chef123")
        db.session.add(Chef(username="chef", password=chef_pwd))

    if not Stud.query.filter_by(username="student").first():
        student_pwd = generate_password_hash("student123")
        db.session.add(Stud(
            username="student", 
            fio="Иванов Иван Иванович", 
            password=student_pwd, 
            classes="10А", 
            balance=1000.0,
            allergy="Лактоза",
            preferences="Люблю гречку"
        ))
        
    db.session.commit()

def calculate_possible_meals(products_list):

    stock = {p.name: p.quantity for p in products_list}

    possible = {}

    for meal_name, ingredients in RECIPES.items():

        counts = []

        for ing_name, req_qty in ingredients.items():

            if ing_name in stock:

                counts.append(int(stock[ing_name] / req_qty))

            else:

                counts.append(0)

        possible[meal_name] = min(counts) if counts else 0

    return possible

def get_current_user():

    if 'user_id' not in session or 'role' not in session:

        return None

    u_id = session['user_id']

    try:

        u_id = int(u_id)

    except:

        pass

    user = None

    if session['role'] == 'admin':

        user = Adm.query.get(u_id)

    elif session['role'] == 'chef':

        user = Chef.query.get(u_id)

    elif session['role'] == 'student':

        user = Stud.query.get(u_id)

    if user is None:

        session.clear()

        return None

    return user

@app.route('/')

def index():

    return render_template("role.html")

@app.route('/admin-login', methods=['GET', 'POST'])

def logad():

    if 'role' in session and session['role'] == 'admin':

        return redirect(url_for('admin_menu'))

    if request.method == 'POST':

        user_id_raw = (request.form.get('id') or "").strip()

        password = (request.form.get('password') or "").strip()

        admin = None

        if user_id_raw:

            if user_id_raw.isdigit():

                admin = Adm.query.get(int(user_id_raw))

            if not admin:

                admin = Adm.query.filter_by(username=user_id_raw).first()

        if admin:

            if check_password_hash(admin.password, password):

                session['user_id'] = admin.id

                session['role'] = 'admin'

                flash(f"Вход выполнен: {admin.username}", "success")

                return redirect(url_for('admin_menu'))

            else:

                flash("Неверный пароль", "error")

        else:

            flash("Пользователь не найден", "error")

        return redirect(url_for('logad'))

    return render_template("вход_админ.html")

@app.route('/chef-login', methods=['GET', 'POST'])

def logch():

    if 'role' in session and session['role'] == 'chef':

        return redirect(url_for('chef_menu'))

    if request.method == 'POST':

        user_id_raw = (request.form.get('id') or "").strip()

        password = (request.form.get('password') or "").strip()

        chef = None

        if user_id_raw:

            if user_id_raw.isdigit():

                chef = Chef.query.get(int(user_id_raw))

            if not chef:

                chef = Chef.query.filter_by(username=user_id_raw).first()

        if chef:

            if check_password_hash(chef.password, password):

                session['user_id'] = chef.id

                session['role'] = 'chef'

                flash(f"Вход выполнен: {chef.username}", "success")

                return redirect(url_for('chef_menu'))

            else:

                flash("Неверный пароль", "error")

        else:

            flash("Повар не найден", "error")

        return redirect(url_for('logch'))

    return render_template("вход_повар.html")

@app.route('/student-create', methods=['GET', 'POST'])

def regst():

    if request.method == 'POST':

        username = request.form.get('username', "").strip()

        fio = request.form.get('fio', "").strip()

        classes = request.form.get('classes', "").strip()

        password = request.form.get('password', "").strip()

        if not username:

            flash("Логин не может быть пустым", "error")

            return redirect(url_for('regst'))

        if Stud.query.filter_by(username=username).first():

            flash(f"Логин {username} ya занят", "error")

            return redirect(url_for('regst'))

        hashed_password = generate_password_hash(password)

        new_stud = Stud(username=username, fio=fio, password=hashed_password, classes=classes, balance=0.0)

        try:

            db.session.add(new_stud)

            db.session.commit()

            flash(f"Регистрация успешна! Ваш ID: {new_stud.id}. Теперь войдите.", "success")

            return redirect(url_for('logst'))

        except Exception as e:

            db.session.rollback()

            flash(f"Ошибка при регистрации", "error")

            return redirect(url_for('regst'))

    return render_template("regstud.html")

@app.route('/student-login', methods=['GET', 'POST'])

def logst():

    if 'role' in session and session['role'] == 'student':

        return redirect(url_for('student_menu'))

    if request.method == 'POST':

        login_raw = (request.form.get('id') or "").strip()

        password = (request.form.get('password') or "").strip()

        student = Stud.query.filter_by(username=login_raw).first()

        if not student and login_raw.isdigit():

            student = Stud.query.get(int(login_raw))

        if student and check_password_hash(student.password, password):

            session['user_id'] = student.id

            session['role'] = 'student'

            flash(f"Добро пожаловать, {student.fio or student.username}!", "success")

            return redirect(url_for('student_menu'))

        else:

            flash("Неверный логин или пароль", "error")

            return redirect(url_for('logst'))

    return render_template("вход.html")

@app.route('/admin-menu')

def admin_menu():

    user = get_current_user()

    if not user or session.get('role') != 'admin':

        return redirect(url_for('index'))

    return render_template("меню_админ.html", user=user)

@app.route('/chef-menu')

def chef_menu():

    user = get_current_user()

    if not user or session.get('role') != 'chef':

        return redirect(url_for('index'))

    requests = PurchaseRequest.query.filter_by(chef_id=user.id).all()

    return render_template("меню_повар.html", user=user, requests=requests)

@app.route('/student-menu')

def student_menu():

    user = get_current_user()

    if not user or session.get('role') != 'student':

        return redirect(url_for('index'))

    orders = MealOrder.query.filter_by(user_id=user.id).order_by(MealOrder.timestamp.desc()).all()

    return render_template("меню_еды_ученик.html", user=user, orders=orders)

@app.route('/purchase-meals')

def purchase_meals():

    user = get_current_user()

    if not user or session.get('role') != 'student':

        return redirect(url_for('index'))

    products = Product.query.all()

    possible = calculate_possible_meals(products)

    return render_template("покупка_блюд.html", user=user, possible=possible)

@app.route('/purchase-request')

def purchase_request():

    user = get_current_user()

    if not user or session.get('role') != 'chef':

        return redirect(url_for('index'))

    requests = PurchaseRequest.query.filter_by(chef_id=user.id).order_by(PurchaseRequest.id.desc()).all()

    products = Product.query.all()

    breakfast_ings = set(RECIPES["Завтрак"].keys())

    lunch_ings = set(RECIPES["Обед"].keys())

    cat_products = {"breakfast": [], "lunch": [], "common": [], "other": []}

    for p in products:

        is_b = p.name in breakfast_ings

        is_l = p.name in lunch_ings

        if is_b and is_l: cat_products["common"].append(p)

        elif is_b: cat_products["breakfast"].append(p)

        elif is_l: cat_products["lunch"].append(p)

        else: cat_products["other"].append(p)

    return render_template("заявка_на_закупку.html", user=user, requests=requests, products=cat_products)

@app.route('/approve-request')

def approve_request():

    user = get_current_user()

    if not user or session.get('role') != 'admin':

        return redirect(url_for('index'))

    pending_requests = PurchaseRequest.query.filter_by(status='Pending').all()

    return render_template("согласование_на_заявку.html", user=user, requests=pending_requests)

@app.route('/profile-settings')

def profile_settings():

    user = get_current_user()

    if not user:

        return redirect(url_for('index'))

    return render_template("настройки_профиля.html", user=user)

@app.route('/payment')

def payment():

    user = get_current_user()

    if not user:

        return redirect(url_for('index'))

    cards = []

    transactions = []

    if session.get('role') == 'student':

        cards = SavedCard.query.filter_by(user_id=user.id).all()

        transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).limit(10).all()

    return render_template("оплата.html", user=user, cards=cards, transactions=transactions)

@app.route('/add-card', methods=['POST'])

def add_card():

    user = get_current_user()

    if not user or session.get('role') != 'student':

        return redirect(url_for('index'))

    card_number = request.form.get('card_number', '').replace(' ', '')
    card_holder = request.form.get('card_holder', '').strip()
    expiry = request.form.get('expiry', '').strip()
    cvv = request.form.get('cvv', '').strip()

    import re
    if not re.match(r'^\d{16}$', card_number):
        flash("Ошибка: Номер карты должен содержать 16 цифр", "error")
        return redirect(url_for('payment'))
    
    if not re.match(r'^\d{2}/\d{2}$', expiry):
        flash("Ошибка: Формат срока действия должен быть ММ/ГГ", "error")
        return redirect(url_for('payment'))

    if not re.match(r'^\d{3}$', cvv):
        flash("Ошибка: CVV должен содержать 3 цифры", "error")
        return redirect(url_for('payment'))

    if not card_holder:
        flash("Ошибка: Введите имя владельца карты", "error")
        return redirect(url_for('payment'))

    
    encrypted_number = cipher_suite.encrypt(card_number.encode()).decode()
    encrypted_expiry = cipher_suite.encrypt(expiry.encode()).decode()
    
    masked_number = card_number[:4] + " **** **** " + card_number[-4:]
    last_four = card_number[-4:]

    new_card = SavedCard(
        user_id=user.id, 
        card_number=encrypted_number, 
        card_holder=card_holder.upper(), 
        expiry=encrypted_expiry,      
        last_four=last_four
    )

    db.session.add(new_card)

    db.session.commit()

    flash("Карта успешно привязана", "success")

    return redirect(url_for('payment'))

@app.route('/delete-card/<int:card_id>', methods=['POST'])

def delete_card(card_id):

    user = get_current_user()

    if not user: return redirect(url_for('index'))

    card = SavedCard.query.get(card_id)

    if card and card.user_id == user.id:

        db.session.delete(card)

        db.session.commit()

        flash("Карта удалена", "success")

    return redirect(url_for('payment'))

@app.route('/add-balance', methods=['POST'])

def add_balance():

    user = get_current_user()

    if not user: return redirect(url_for('index'))

    password = request.form.get('password')

    amount = request.form.get('amount', type=float)

    card_id = request.form.get('card_id')

    user_cards = SavedCard.query.filter_by(user_id=user.id).all()

    if not user_cards:

        flash("Для пополнения баланса необходимо сначала привязать карту", "error")

        return redirect(url_for('payment'))

    if not check_password_hash(user.password, password):

        flash("Неверный пароль", "error")

        return redirect(url_for('payment'))

    if amount and amount > 0:

        card_label = "Карта"

        if card_id:

            card = SavedCard.query.get(card_id)

            if card and card.user_id == user.id:

                card_label = f"Карта *{card.last_four}"

        new_tx = Transaction(user_id=user.id, amount=amount, type='Пополнение', card_used=card_label)

        db.session.add(new_tx)

        if user.balance is None: user.balance = 0.0

        user.balance += amount

        db.session.commit()

        flash(f"Баланс пополнен на {amount} ₽!", "success")

    return redirect(url_for('payment'))

@app.route('/buy-meal', methods=['POST'])

def buy_meal():

    user = get_current_user()

    if not user: return redirect(url_for('index'))

    meal_type = request.form.get('meal_type')

    price = request.form.get('price', type=float)

    confirm_allergy = request.form.get('confirm_allergy') == 'true'

    meal_type_lower = meal_type.lower()

    if session.get('role') == 'student' and user.allergy:

        base_type = "Завтрак" if "завтрак" in meal_type_lower else "Обед"

        meal_info = MealProduct.query.filter_by(meal_type=base_type).first()

        if meal_info:

            user_allergies = [a.strip().lower() for a in user.allergy.split(',')]

            meal_ingredients = [i.strip().lower() for i in meal_info.ingredients.split(',')]

            conflicts = [item for item in user_allergies if item in meal_ingredients]

            if conflicts and not confirm_allergy:

                conflict_str = ", ".join(conflicts)

                flash(f"Внимание! В блюде есть аллергены: {conflict_str}", "info")

    base_type = "Завтрак" if "завтрак" in meal_type_lower else "Обед"

    needed_qty = 15 if "абонемент" in meal_type_lower else 1

    recipe = RECIPES.get(base_type)

    if recipe:

        for ing_name, req_qty in recipe.items():

            prod = Product.query.filter_by(name=ing_name).first()

            if not prod or prod.quantity < (req_qty * needed_qty):

                flash(f"Недостаточно продуктов для {meal_type}", "error")

                return redirect(url_for('student_menu'))

    if (user.balance or 0.0) < price:

        flash(f"Недостаточно средств. Пополните баланс.", "error")

        return redirect(url_for('payment'))

    user.balance = (user.balance or 0.0) - price

    new_tx = Transaction(user_id=user.id, amount=price, type='Покупка', status='Выполнено', card_used='Баланс')

    db.session.add(new_tx)

    if recipe:

        for ing_name, req_qty in recipe.items():

            prod = Product.query.filter_by(name=ing_name).first()

            if prod: prod.quantity -= (req_qty * needed_qty)

    new_order = MealOrder(user_id=user.id, user_name=user.username, meal_type=meal_type, price=price)

    db.session.add(new_order)

    db.session.commit()

    flash(f"Покупка успешно совершена: {meal_type}", "success")

    return redirect(url_for('student_menu'))

@app.route('/claim-meal/<int:order_id>')

def claim_meal(order_id):

    user = get_current_user()

    if not user: return redirect(url_for('index'))

    order = MealOrder.query.get(order_id)

    if order and order.user_id == user.id:

        if order.is_issued: flash("Уже получено", "info")

        else:

            order.is_issued = True

            db.session.commit()

            flash("Приятного аппетита!", "success")

    return redirect(url_for('student_menu'))

@app.route('/submit-purchase-request', methods=['POST'])

def submit_purchase_request():

    user = get_current_user()

    if session.get('role') != 'chef': return redirect(url_for('index'))

    item_name = request.form.get('item_name')

    quantity = request.form.get('quantity', type=float)

    price = request.form.get('price', type=float)

    new_req = PurchaseRequest(item_name=item_name, quantity=quantity, price=price, chef_id=user.id)

    db.session.add(new_req)

    db.session.commit()

    flash(f"Заявка на {item_name} отправлена", "success")

    return redirect(url_for('purchase_request'))

@app.route('/approve-purchase-request/<int:req_id>')

def approve_purchase_request(req_id):

    if session.get('role') != 'admin': return redirect(url_for('index'))

    req = PurchaseRequest.query.get(req_id)

    if req:

        req.status = 'Approved'

        product = Product.query.filter_by(name=req.item_name).first()

        unit_price = req.price / req.quantity if req.quantity > 0 else 0

        if product:

            product.quantity += req.quantity

            product.price_per_unit = unit_price

        else:

            new_prod = Product(name=req.item_name, quantity=req.quantity, price_per_unit=unit_price, unit="ед.")

            db.session.add(new_prod)

        db.session.commit()

        flash(f"Заявка на {req.item_name} одобрена", "success")

    return redirect(url_for('approve_request'))

@app.route('/reject-purchase-request/<int:req_id>')

def reject_purchase_request(req_id):

    if session.get('role') != 'admin': return redirect(url_for('index'))

    req = PurchaseRequest.query.get(req_id)

    if req:

        req.status = 'Rejected'

        db.session.commit()

        flash(f"Заявка на {req.item_name} отклонена", "error")

    return redirect(url_for('approve_request'))

@app.route('/issue-meal/<int:order_id>', methods=['POST'])

def issue_meal(order_id):

    if session.get('role') != 'chef': return redirect(url_for('index'))

    order = MealOrder.query.get(order_id)

    if order:

        order.is_issued = True

        db.session.commit()

        flash(f"Выдача питания {order.meal_type} для {order.user_name} подтверждена", "success")

    return redirect(url_for('meals_accounting'))

@app.route('/reviews', methods=['GET', 'POST'])

def reviews():

    user = get_current_user()

    if request.method == 'POST':

        if not user: return redirect(url_for('index'))

        text = request.form.get('text')

        if text:

            new_fb = Feedback(user_id=user.id, user_role=session['role'], user_fio=user.username, text=text)

            db.session.add(new_fb)

            db.session.commit()

            return redirect(url_for('reviews'))

    feedbacks = Feedback.query.order_by(Feedback.timestamp.desc()).all()

    return render_template("отзывы.html", user=user, feedbacks=feedbacks)

@app.route('/support')

def support():

    user = get_current_user()

    return render_template("поддержка.html", user=user)

@app.route('/meals-accounting')

def meals_accounting():

    user = get_current_user()

    if not user or session.get('role') not in ['admin', 'chef']: return redirect(url_for('index'))

    orders = MealOrder.query.order_by(MealOrder.timestamp.desc()).all()

    students = {s.id: s for s in Stud.query.all()}

    return render_template("учет_завтраков_обедов.html", user=user, orders=orders, students=students)

@app.route('/products-accounting')

def products_accounting():

    user = get_current_user()

    if not user or session.get('role') not in ['admin', 'chef']: return redirect(url_for('index'))

    products = Product.query.all()

    possible = calculate_possible_meals(products)

    breakfast_ings = set(RECIPES["Завтрак"].keys())

    lunch_ings = set(RECIPES["Обед"].keys())

    cat_products = {"breakfast": [], "lunch": [], "common": [], "other": []}

    for p in products:

        is_b = p.name in breakfast_ings

        is_l = p.name in lunch_ings

        if is_b and is_l: cat_products["common"].append(p)

        elif is_b: cat_products["breakfast"].append(p)

        elif is_l: cat_products["lunch"].append(p)

        else: cat_products["other"].append(p)

    return render_template("учет_продуктов.html", user=user, products=cat_products, possible=possible)

@app.route('/write-off-product', methods=['POST'])

def write_off_product():

    if session.get('role') not in ['admin', 'chef']: return redirect(url_for('index'))

    prod_id = request.form.get('product_id', type=int)

    amount = request.form.get('amount', type=float)

    product = Product.query.get(prod_id)

    if product and amount > 0:

        if product.quantity >= (amount - 1e-9):

            product.quantity = max(0, product.quantity - amount)

            db.session.commit()

    return redirect(url_for('products_accounting'))

@app.route('/add-product-stock', methods=['POST'])

def add_product_stock():

    if session.get('role') not in ['admin', 'chef']: return redirect(url_for('index'))

    prod_id = request.form.get('product_id', type=int)

    amount = request.form.get('amount', type=float)

    product = Product.query.get(prod_id)

    if product and amount > 0:

        product.quantity += amount

        db.session.commit()

    return redirect(url_for('products_accounting'))

@app.route('/reports')

def reports():

    user = get_current_user()

    if not user or session.get('role') != 'admin': return redirect(url_for('index'))

    orders = MealOrder.query.all()

    purchases = PurchaseRequest.query.filter_by(status='Approved').all()

    total_revenue = sum(o.price for o in orders)

    total_costs = sum(p.price for p in purchases)

    return render_template("формирование_отчетов_по_питанию,затратам.html", user=user, orders=orders, purchases=purchases, total_revenue=total_revenue, total_costs=total_costs, profit=total_revenue - total_costs)

@app.route('/update-profile', methods=['POST'])

def update_profile():

    user = get_current_user()

    if not user: return redirect(url_for('index'))

    new_name = request.form.get('username')

    new_allergy = request.form.get('allergy')

    new_prefs = request.form.get('preferences')

    if new_name: user.username = new_name

    if session.get('role') == 'student':

        if new_allergy is not None: user.allergy = new_allergy

        if new_prefs is not None: user.preferences = new_prefs

    db.session.commit()

    return redirect(url_for('profile_settings'))

@app.route('/logout')

def logout():

    session.clear()

    return redirect(url_for('index'))

if __name__ == '__main__':

    with app.app_context():

        MealProduct.query.delete() 

        db.session.add(MealProduct(meal_type="Завтрак", ingredients="Молоко, Овсяная крупа, Глютен, Яйцо, Сахар, Сливочное масло, Лактоза"))

        db.session.add(MealProduct(meal_type="Обед", ingredients="Говядина, Картофель, Макароны, Глютен, Лук, Морковь, Подсолнечное масло, Томатная паста"))

        db.session.commit()

    app.run(debug=True, port=8000)

