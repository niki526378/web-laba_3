import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_laba4'

# --- МОДЕЛЬ ДАННЫХ (In-memory DB) ---
services = [
    {"id": 1, "name": "Мужская стрижка", "category": "Топ-стилист", "duration": 40, "price": 1500, "material_cost": 200},
    {"id": 2, "name": "Окрашивание", "category": "Мастер", "duration": 120, "price": 5500, "material_cost": 1800},
    {"id": 3, "name": "Детская стрижка", "category": "Стажер", "duration": 30, "price": 800, "material_cost": 50},
]
next_id = 4

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def calculate_stats():
    # Словарь соответствия: как поле называется в данных -> как оно будет в статистике
    fields_map = {
        'duration': 'Длительность',
        'price': 'Цена услуги',
        'material_cost': 'Расходные материалы'
    }
    stats = {}
    if not services:
        return {name: {"min": 0, "max": 0, "avg": 0} for name in fields_map.values()}
    
    for english_name, russian_name in fields_map.items():
        vals = [s[english_name] for s in services]
        stats[russian_name] = {
            "min": min(vals),
            "max": max(vals),
            "avg": round(sum(vals) / len(vals), 2)
        }
    return stats

def generate_captcha():
    a, b = random.randint(1, 10), random.randint(1, 10)
    session['captcha_res'] = a + b
    return f"{a} + {b}"

# --- МАРШРУТЫ (ROUTES) ---

@app.route('/')
def index():
    # Сортировка
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    rev = (order == 'desc')
    try:
        sorted_list = sorted(services, key=lambda x: x[sort_by], reverse=rev)
    except KeyError:
        sorted_list = services

    captcha_q = generate_captcha()
    return render_template('index.html', 
                           services=sorted_list, 
                           stats=calculate_stats(),
                           captcha_q=captcha_q,
                           sort_by=sort_by,
                           order=order)

@app.route('/add', methods=['POST'])
def add():
    global next_id
    # Проверка капчи
    user_ans = request.form.get('captcha_ans', type=int)
    if user_ans != session.get('captcha_res'):
        return "Ошибка капчи! Вернитесь назад и попробуйте снова.", 400

    new_item = {
        "id": next_id,
        "name": request.form.get('name'),
        "category": request.form.get('category'),
        "duration": int(request.form.get('duration', 0)),
        "price": int(request.form.get('price', 0)),
        "material_cost": int(request.form.get('material_cost', 0))
    }
    services.append(new_item)
    next_id += 1
    return redirect(url_for('index'))

@app.route('/delete/<int:sid>')
def delete(sid):
    global services
    services = [s for s in services if s['id'] != sid]
    return redirect(url_for('index'))

@app.route('/update/<int:sid>', methods=['POST'])
def update(sid):
    for s in services:
        if s['id'] == sid:
            s['name'] = request.form.get('name')
            s['category'] = request.form.get('category')
            s['duration'] = int(request.form.get('duration'))
            s['price'] = int(request.form.get('price'))
            s['material_cost'] = int(request.form.get('material_cost'))
    return redirect(url_for('index'))

# --- API ---
@app.route('/api/services')
def get_api():
    return jsonify({"items": services, "stats": calculate_stats()})

if __name__ == '__main__':
    app.run(debug=True)
