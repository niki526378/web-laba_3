import os
import base64
import io
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, session
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = 'youronin' # Нужно для сессий (капча)

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

def add_watermark(image, text="Web-Laba 3"):
    """Накладывает водяной знак с черным фоном и увеличенным текстом"""
    wm_image = image.copy()
    draw = ImageDraw.Draw(wm_image)
    
    width, height = wm_image.size
    try:
        font = ImageFont.truetype("arial.ttf", 40) 
    except:
        font = ImageFont.load_default()

    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top

    margin = 20
    x = width - text_width - margin - 10 
    y = height - text_height - margin - 10

    rect_coords = [x - 5, y - 5, width - margin + 5, height - margin + 5]
    draw.rectangle(rect_coords, fill=(0, 0, 0))
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    
    return wm_image
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

                    use_watermark = request.form.get('use_watermark') == 'on'

                    # Обработка (изменение интенсивности)
                    # Формула: I_new = I_old * factor
                    r, g, b = image.split()
                    r = r.point(lambda i: i * r_factor)
                    g = g.point(lambda i: i * g_factor)
                    b = b.point(lambda i: i * b_factor)
                    processed_image = Image.merge('RGB', (r, g, b))

                    if use_watermark:
                        processed_image = add_watermark(processed_image)

                    # Генерация данных для отображения
                    original_img_data = image_to_base64(image)
                    processed_img_data = image_to_base64(processed_image)
                    
                    orig_hist = generate_histogram(image)
                    proc_hist = generate_histogram(processed_image)

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
