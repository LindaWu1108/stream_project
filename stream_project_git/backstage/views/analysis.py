from flask import render_template, Blueprint
from flask_login import login_required, current_user
from api.sql import Analysis

analysis = Blueprint('analysis', __name__, template_folder='../templates')


@analysis.route('/dashboard')
@login_required
def dashboard():
    user = current_user.email

    revenue = []
    dataa = []

    for i in range(1, 13):
        row = Analysis.month_price(i)
        if not row:
            revenue.append(0)
        else:
            for j in row:
                revenue.append(int(j[1]))

        row = Analysis.month_count(i)
        if not row:
            dataa.append(0)
        else:
            for k in row:
                dataa.append(int(k[1]))

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