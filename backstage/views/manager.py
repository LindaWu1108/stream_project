from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required, current_user
from api.sql import Movie, Genre, Subscription, Watch

manager = Blueprint('manager', __name__, template_folder='../templates')


@manager.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return redirect(url_for('manager.productManager'))


@manager.route('/productManager', methods=['GET', 'POST'])
@login_required
def productManager():
    if request.method == 'GET':
        if current_user.role == 'user':
            flash('No permission')
            return redirect(url_for('bookstore.bookstore'))

    if 'delete' in request.values:
        movie_id = request.values.get('delete')
        Movie.delete_movie(movie_id)
        flash(f'已刪除影片 {movie_id}')
        return redirect(url_for('manager.productManager'))

    elif 'edit' in request.values:
        movie_id = request.values.get('edit')
        return redirect(url_for('manager.edit', pid=movie_id))

    movies_raw = Movie.get_all(is_kid=False)
    book_data = []
    for m in movies_raw:
        book_data.append({
            'movieId': m[0],
            'title': m[1],
            'duration': m[2],
            'rating': m[3],
            'genres': m[4],
            'avg_rating': m[5] if m[5] is not None else '尚無評分'
        })

    genres = Genre.get_all()
    return render_template('productManager.html', book_data=book_data, genres=genres, user=current_user.email)


@manager.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        title = request.values.get('pname', '').strip()
        duration = request.values.get('price', '120').strip()
        rating = request.values.get('category', '普遍級').strip()
        genre_ids = request.form.getlist('genre_ids')

        if not title or not duration:
            flash('影片片名與片長不可為空。')
            return redirect(url_for('manager.productManager'))

        new_movie_id = Movie.next_movie_id()
        Movie.add_movie(new_movie_id, title, duration, rating, genre_ids)
        flash(f'成功新增影片：《{title}》({new_movie_id})')
        return redirect(url_for('manager.productManager'))

    return redirect(url_for('manager.productManager'))


@manager.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if current_user.role == 'user':
        flash('No permission')
        return redirect(url_for('bookstore.bookstore'))

    if request.method == 'POST':
        movie_id = request.values.get('pid')
        title = request.values.get('pname', '').strip()
        duration = request.values.get('price', '120').strip()
        rating = request.values.get('category', '普遍級').strip()
        genre_ids = request.form.getlist('genre_ids')

        Movie.update_movie(movie_id, title, duration, rating, genre_ids)
        flash(f'已更新影片《{title}》')
        return redirect(url_for('manager.productManager'))

    movie_id = request.args.get('pid')
    row = Movie.get_by_id(movie_id)
    selected_genres = Movie.get_movie_genre_ids(movie_id)
    all_genres = Genre.get_all()

    product = {
        'movieId': row[0],
        'title': row[1],
        'duration': row[2],
        'rating': row[3]
    }
    return render_template('edit.html', data=product, genres=all_genres, selected_genres=selected_genres, user=current_user.email)


@manager.route('/orderManager', methods=['GET', 'POST'])
@login_required
def orderManager():
    subs_raw = Subscription.get_all_subscriptions()
    order_data = []
    for s in subs_raw:
        order_data.append({
            'subId': s[0],
            'email': s[1],
            'planName': s[2],
            'amount': s[3],
            'payDate': s[4],
            'endDate': s[5],
            'status': s[6]
        })

    watch_raw = Watch.get_all_watch_logs()
    watch_logs = []
    for w in watch_raw:
        watch_logs.append({
            'email': w[0],
            'profileName': w[1],
            'title': w[2],
            'progress': w[3],
            'rating': w[4] if w[4] else '未評分',
            'total_minutes': w[5]
        })

    return render_template('orderManager.html', orderData=order_data, watchLogs=watch_logs, user=current_user.email)