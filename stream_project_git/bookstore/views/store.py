from flask import Blueprint, request, url_for, redirect, flash, render_template
from flask_login import login_required, current_user
from api.sql import Account, Plan, Subscription, Profile, Movie, Genre, Watch

store = Blueprint('bookstore', __name__, template_folder='../templates')


@store.route('/', methods=['GET', 'POST'])
@login_required
def bookstore():
    if current_user.role == 'manager':
        return redirect(url_for('manager.productManager'))

    # 點進單部影片頁面（觀看與評分）
    if 'pid' in request.args:
        movie_id = request.args['pid']
        row = Movie.get_by_id(movie_id)
        if not row:
            flash('找不到該影片')
            return redirect(url_for('bookstore.bookstore'))

        watch_info = Watch.get_one(current_user.id, current_user.profile_no, movie_id)
        watch_times = Watch.get_watch_times(current_user.id, current_user.profile_no, movie_id)

        movie_data = {
            'movieId': row[0],
            'title': row[1],
            'duration': row[2],
            'rating': row[3],
            'genres': row[4],
            'avg_rating': row[5] if row[5] is not None else '尚無評分',
            'my_progress': watch_info[0] if watch_info else 0,
            'my_rating': watch_info[1] if (watch_info and watch_info[1]) else 5,
            'watch_times': watch_times
        }
        return render_template('product.html', data=movie_data, user=current_user.name, is_kid=current_user.is_kid)

    # 影片瀏覽大廳（支援關鍵字搜尋、類別篩選、兒童模式自動過濾）
    genre_id = request.args.get('genre_id')
    keyword = request.args.get('keyword', '').strip()

    movies_raw = Movie.get_all(
        is_kid=current_user.is_kid,
        genre_id=genre_id if genre_id else None,
        keyword=keyword if keyword else None
    )
    genres = Genre.get_all()

    # 取得目前 Profile 的觀看進度對照表
    my_watches = {w[0]: {'progress': w[4], 'rating': w[5]} for w in Watch.get_by_profile(current_user.id, current_user.profile_no)}

    book_data = []
    for m in movies_raw:
        w_info = my_watches.get(m[0])
        book_data.append({
            'movieId': m[0],
            'title': m[1],
            'duration': m[2],
            'rating': m[3],
            'genres': m[4],
            'avg_rating': m[5] if m[5] is not None else '暫無',
            'my_progress': w_info['progress'] if w_info else None,
            'my_rating': w_info['rating'] if w_info else None
        })

    return render_template(
        'bookstore.html',
        book_data=book_data,
        genres=genres,
        current_genre=genre_id,
        keyword=keyword,
        user=current_user.name,
        is_kid=current_user.is_kid
    )


# 觀看紀錄與評分管理 (對應 Watch & Watch_Time)
@store.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if current_user.role == 'manager':
        return redirect(url_for('manager.productManager'))

    if request.method == 'POST':
        if 'delete' in request.form:
            movie_id = request.form.get('delete')
            Watch.delete_watch(current_user.id, current_user.profile_no, movie_id)
            flash('已移除觀看紀錄')
            return redirect(url_for('bookstore.cart'))

        elif 'movie_id' in request.form:
            movie_id = request.form.get('movie_id')
            progress = request.form.get('progress', 100)
            rating = request.form.get('rating', 5)
            Watch.record_watch(
                current_user.id,
                current_user.profile_no,
                movie_id,
                progress,
                rating
            )
            flash('✅ 已儲存觀看進度與評分，並自動記錄本次觀看時間點 (Watch_Time)！')
            return redirect(url_for('bookstore.cart'))

    watch_rows = Watch.get_by_profile(current_user.id, current_user.profile_no)
    watch_list = []
    for r in watch_rows:
        watch_list.append({
            'movieId': r[0],
            'title': r[1],
            'duration': r[2],
            'age_rating': r[3],
            'progress': r[4],
            'user_rating': r[5] if r[5] else '未評分',
            'watch_times': r[6],
            'watch_count': r[7]
        })

    return render_template('cart.html', data=watch_list, user=current_user.name)


# 訂閱方案與歷史帳單紀錄 (對應 Subscription & Plan)
@store.route('/orderlist', methods=['GET', 'POST'])
@login_required
def orderlist():
    profile_count = len(Profile.get_by_account(current_user.id))

    if request.method == 'POST':
        plan_id = request.form.get('plan_id')
        if plan_id:
            target_plan = Plan.get_by_id(plan_id)
            if target_plan and profile_count > target_plan[3]:
                flash(f'⚠️ 無法切換至【{target_plan[1]}】方案（上限 {target_plan[3]} 人）：您目前已建立 {profile_count} 位使用者，請先至「切換使用者」頁面移除多餘成員！')
                return redirect(url_for('bookstore.orderlist'))

            Subscription.create_subscription(current_user.id, plan_id)
            flash(f'✅ 已成功訂閱／變更為【{target_plan[1]}】方案（上限 {target_plan[3]} 人）！')
            return redirect(url_for('bookstore.orderlist'))

    subs_raw = Subscription.get_by_account(current_user.id)
    subs = []
    for s in subs_raw:
        subs.append({
            'subId': s[0],
            'payDate': s[1],
            'amount': s[2],
            'endDate': s[3],
            'status': s[4],
            'planId': s[5],
            'planName': s[6],
            'price': s[7],
            'maxScreens': s[8]
        })

    current_sub = subs[0] if subs else None
    plans = Plan.get_all()
    return render_template(
        'orderlist.html',
        data=subs,
        current_sub=current_sub,
        profile_count=profile_count,
        plans=plans,
        user=current_user.name,
        email=current_user.email
    )