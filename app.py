from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import calendar
import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Message
from config import Config
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Неверное имя пользователя или пароль', 'danger')
            return render_template('login.html')

        user.last_login = datetime.datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)

        session.permanent = True

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')

        flash('Вы успешно вошли в систему!', 'success')
        return redirect(next_page)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return render_template('register.html')

        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Имя пользователя уже занято', 'danger')
            return render_template('register.html')

        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            flash('Email уже используется', 'danger')
            return render_template('register.html')

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    start_date = datetime.date(2025, 3, 17)
    today = datetime.date.today()

    selected_month = request.args.get('month', type=int)
    selected_year = request.args.get('year', type=int)

    if not selected_month or not selected_year:
        selected_month = today.month
        selected_year = today.year

    current_year = today.year
    years = list(range(current_year - 2, current_year + 5))
    months = [
        (1, 'Январь'), (2, 'Февраль'), (3, 'Март'), (4, 'Апрель'),
        (5, 'Май'), (6, 'Июнь'), (7, 'Июль'), (8, 'Август'),
        (9, 'Сентябрь'), (10, 'Октябрь'), (11, 'Ноябрь'), (12, 'Декабрь')
    ]

    calendar_data = []

    for i in range(3):
        month = (selected_month + i - 1) % 12 + 1
        year = selected_year + (selected_month + i - 1) // 12

        cal = calendar.monthcalendar(year, month)

        month_data = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({"day": "", "status": "empty"})
                else:
                    current_date = datetime.date(year, month, day)
                    days_diff = (current_date - start_date).days
                    cycle_position = days_diff % 4

                    if cycle_position < 2:
                        status = "work"
                    else:
                        status = "off"

                    is_today = (current_date == today)

                    week_data.append({
                        "day": day,
                        "status": status,
                        "today": is_today
                    })
            month_data.append(week_data)

        month_name = calendar.month_name[month]
        calendar_data.append({"month": month_name, "year": year, "weeks": month_data})

    return render_template(
        'calendar.html',
        calendar_data=calendar_data,
        selected_month=selected_month,
        selected_year=selected_year,
        months=months,
        years=years,
        start_date=start_date,
        now=datetime.datetime.now(),
        user=current_user
    )


@app.route('/chat')
@login_required
def chat():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('chat.html', users=users)


@app.route('/send_mur', methods=['POST'])
@login_required
def send_mur():
    recipient_id = request.form.get('recipient_id')
    if not recipient_id:
        return jsonify({'error': 'Получатель не выбран'}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'error': 'Получатель не найден'}), 404

    message = Message(sender_id=current_user.id, recipient_id=recipient.id)
    db.session.add(message)
    db.session.commit()

    return jsonify({
        'success': True,
        'sender': current_user.username,
        'timestamp': message.timestamp.strftime('%H:%M:%S')
    })


@app.route('/get_messages/<int:user_id>')
@login_required
def get_messages(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.desc()).limit(50).all()

    return jsonify([{
        'sender': message.sender.username,
        'timestamp': message.timestamp.strftime('%H:%M:%S')
    } for message in messages])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
