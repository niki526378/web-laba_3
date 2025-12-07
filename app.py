import os
import base64
import io
import random
import numpy as np
import matplotlib
matplotlib.use('Agg') # Для работы без GUI на сервере
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, session
from PIL import Image

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Нужно для сессий (капча)

def generate_histogram(image):
    """Создает график распределения цветов и возвращает его как base64 строку"""
    img_array = np.array(image)
    
    fig, ax = plt.subplots(figsize=(5, 3))
    colors = ['red', 'green', 'blue']
    
    if len(img_array.shape) == 3: # Цветное изображение
        for i, color in enumerate(colors):
            hist, bins = np.histogram(img_array[:, :, i], bins=256, range=(0, 256))
            ax.plot(bins[:-1], hist, color=color, alpha=0.7)
    else: # Ч/Б
        hist, bins = np.histogram(img_array, bins=256, range=(0, 256))
        ax.plot(bins[:-1], hist, color='black')

    ax.set_title('Распределение цветов')
    ax.set_xlabel('Интенсивность')
    ax.set_ylabel('Количество пикселей')
    
    img_io = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    plt.close(fig)
    return base64.b64encode(img_io.getvalue()).decode('utf-8')

def image_to_base64(image):
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode('utf-8')

# Функция для классификации (ML)
def classify_image(image):
    # Для работы требуется TensorFlow.
    # model = MobileNetV2(weights='imagenet')
    # img = image.resize((224, 224))
    # x = img_to_array(img)
    # x = np.expand_dims(x, axis=0)
    # x = preprocess_input(x)
    # preds = model.predict(x)
    # return decode_predictions(preds, top=1)[0][0][1]
    return "ML модуль отключен (экономия памяти)"

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    original_img_data = None
    processed_img_data = None
    orig_hist = None
    proc_hist = None
    classification_result = None

    # Генерация простой капчи (числа сохраняем в сессию)
    if 'captcha_num1' not in session:
        session['captcha_num1'] = random.randint(1, 10)
        session['captcha_num2'] = random.randint(1, 10)

    if request.method == 'POST':
        # 1. Проверка Капчи
        user_answer = request.form.get('captcha_answer', type=int)
        real_answer = session.get('captcha_num1') + session.get('captcha_num2')
        
        # Обновляем капчу для следующего раза
        session['captcha_num1'] = random.randint(1, 10)
        session['captcha_num2'] = random.randint(1, 10)

        if user_answer != real_answer:
            error = "Неверная капча!"
        elif 'file' not in request.files:
            error = "Нет файла"
        else:
            file = request.files['file']
            if file.filename == '':
                error = "Файл не выбран"
            else:
                try:
                    # Загрузка изображения
                    image = Image.open(file).convert('RGB')
                    
                    # Получение коэффициентов из формы
                    r_factor = float(request.form.get('r_factor', 1))
                    g_factor = float(request.form.get('g_factor', 1))
                    b_factor = float(request.form.get('b_factor', 1))

                    # Обработка (изменение интенсивности)
                    # Формула: I_new = I_old * factor
                    r, g, b = image.split()
                    r = r.point(lambda i: i * r_factor)
                    g = g.point(lambda i: i * g_factor)
                    b = b.point(lambda i: i * b_factor)
                    processed_image = Image.merge('RGB', (r, g, b))

                    # Генерация данных для отображения
                    original_img_data = image_to_base64(image)
                    processed_img_data = image_to_base64(processed_image)
                    
                    orig_hist = generate_histogram(image)
                    proc_hist = generate_histogram(processed_image)
                    
                    # ML Классификация (по возможности)
                    # classification_result = classify_image(processed_image)

                except Exception as e:
                    error = f"Ошибка обработки: {str(e)}"

    return render_template('index.html', 
                           captcha_q=f"{session.get('captcha_num1')} + {session.get('captcha_num2')}",
                           error=error,
                           original_img=original_img_data,
                           processed_img=processed_img_data,
                           orig_hist=orig_hist,
                           proc_hist=proc_hist,
                           cls_res=classification_result)

if __name__ == '__main__':
    app.run(debug=True)