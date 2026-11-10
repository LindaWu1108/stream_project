from flask import render_template, Blueprint
from flask_login import login_required, current_user
from api.sql import Analysis

analysis = Blueprint('analysis', __name__, template_folder='../templates')


@analysis.route('/dashboard')
@login_required
def dashboard():
    user = current_user.email

    revenue = [0] * 12
    dataa = [0] * 12

    for month_num, total_amount, total_count in Analysis.monthly_summary():
        idx = int(month_num) - 1
        if 0 <= idx < 12:
            revenue[idx] = int(total_amount)
            dataa[idx] = int(total_count)

    row = Analysis.category_sale()
    datab = []
    for i in row:
        datab.append({
            'value': int(i[0]),
            'name': i[1]
        })

    row = Analysis.member_sale()
    datac = []
    nameList = []
    counter = 0

    for i in row:
        counter += 1
        datac.append(int(i[0]))
        nameList.append(i[2])

    counter = max(counter - 1, 0)

    row = Analysis.member_sale_count()
    countList = [int(i[0]) for i in row]

    return render_template(
        'dashboard.html',
        user=user,
        counter=counter,
        revenue=revenue,
        dataa=dataa,
        datab=datab,
        datac=datac,
        nameList=nameList,
        countList=countList
    )