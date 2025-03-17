from flask import Flask, render_template, request
import calendar
import datetime

app = Flask(__name__)


@app.route('/')
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
        start_date=start_date
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
