from flask import render_template, Blueprint, redirect, request, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from link import *
from api.sql import *

api = Blueprint('api', __name__, template_folder='./templates')

login_manager = LoginManager(api)
login_manager.login_view = 'api.login'
login_manager.login_message = "請先登入"


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(userid):
    account_data = Account.get_by_id(userid)
    if not account_data:
        return None

    user = User()
    user.id = account_data[0]       # accountId (例如 'A001')
    user.email = account_data[1]    # email
    # 預設 admin@gmail.com 為後台管理員，其餘為一般會員
    user.role = 'manager' if account_data[1].startswith('admin') else 'user'

    # 讀取目前選擇的 Profile（若尚未選擇則預設第一個）
    profile_no = session.get('profile_no')
    profile = Profile.get_one(user.id, profile_no) if profile_no else None
    if not profile:
        profiles = Profile.get_by_account(user.id)
        if profiles:
            profile = profiles[0]
            session['profile_no'] = profile[1]
            session['profile_name'] = profile[2]
            session['is_kid'] = bool(profile[3])

    if profile:
        user.profile_no = profile[1]
        user.profile_name = profile[2]
        user.is_kid = bool(profile[3])
        kid_badge = " (兒童模式)" if user.is_kid else ""
        user.name = f"{profile[2]}{kid_badge}"
    else:
        user.profile_no = 1
        user.profile_name = account_data[1].split('@')[0]
        user.is_kid = False
        user.name = user.profile_name

    return user


@api.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['account'].strip()
        password = request.form['password']
        data = Account.get_by_email(email)

        if not data:
            flash('*沒有此帳號（請輸入 Email，例如 user@gmail.com）')
            return redirect(url_for('api.login'))

        account_id = data[0]
        db_password = data[2]

        if db_password == password:
            user = User()
            user.id = account_id
            login_user(user)
            session.pop('profile_no', None)

            if email.startswith('admin'):
                return redirect(url_for('manager.productManager'))
            else:
                return redirect(url_for('api.profiles'))
        else:
            flash('*密碼錯誤，請再試一次')
            return redirect(url_for('api.login'))

    return render_template('login.html')


@api.route('/register', methods=['POST', 'GET'])
def register():
    plans = Plan.get_all()
    if request.method == 'POST':
        email = request.form['account'].strip()
        password = request.form['password']
        profile_name = request.form.get('username', '主使用者').strip() or '主使用者'
        plan_id = request.form.get('plan_id', 'P01')

        exist_emails = [row[0] for row in Account.get_all_emails()]
        if email in exist_emails:
            flash('*此 Email 已經註冊過了！')
            return redirect(url_for('api.register'))

        # 1. 建立 Account
        new_account_id = Account.next_account_id()
        Account.create_account(new_account_id, email, password)

        # 2. 建立 Subscription（訂閱紀錄）
        Subscription.create_subscription(new_account_id, plan_id)

        # 3. 建立第一個 Profile（弱實體）
        Profile.create_profile(new_account_id, profile_name, is_kid=False)

        flash('註冊成功！請使用剛才的 Email 登入')
        return redirect(url_for('api.login'))

    return render_template('register.html', plans=plans)


@api.route('/profiles', methods=['GET', 'POST'])
@login_required
def profiles():
    profile_list = Profile.get_by_account(current_user.id)
    subs = Subscription.get_by_account(current_user.id)
    current_sub = subs[0] if subs else None
    max_screens = current_sub[8] if current_sub else 1
    plan_name = current_sub[6] if current_sub else '基本'

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'select':
            profile_no = int(request.form.get('profile_no', 1))
            profile = Profile.get_one(current_user.id, profile_no)
            if profile:
                session['profile_no'] = profile[1]
                session['profile_name'] = profile[2]
                session['is_kid'] = bool(profile[3])
            return redirect(url_for('bookstore.bookstore'))

        elif action == 'add':
            if len(profile_list) >= max_screens:
                if max_screens >= 4:
                    flash(f'⚠️ 無法新增：您目前的【{plan_name}】已是最高等級方案（上限 {max_screens} 位使用者），目前已達人數上限！')
                else:
                    flash(f'⚠️ 無法新增：您目前的【{plan_name}】方案上限為 {max_screens} 位使用者，目前已達上限（{len(profile_list)}/{max_screens}）！如需新增請先升級訂閱方案。')
                return redirect(url_for('api.profiles'))

            new_name = request.form.get('profile_name', '').strip()
            is_kid = (request.form.get('is_kid') == '1')
            if new_name:
                Profile.create_profile(current_user.id, new_name, is_kid)
                flash(f'✅ 已成功新增使用者「{new_name}」！')
            return redirect(url_for('api.profiles'))

        elif action == 'delete':
            profile_no = int(request.form.get('profile_no', 0))
            if profile_no > 1:
                Profile.delete_profile(current_user.id, profile_no)
                if session.get('profile_no') == profile_no:
                    session.pop('profile_no', None)
                flash('🗑️ 已刪除該子使用者！')
            return redirect(url_for('api.profiles'))

    return render_template(
        'profiles.html',
        profiles=profile_list,
        subscription=current_sub,
        max_screens=max_screens,
        email=current_user.email
    )


@api.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('index'))