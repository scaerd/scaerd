import cv2
import sqlite3
import time
from ultralytics import YOLO

# 1. Загружаем самую лёгкую и быструю модель нейросети YOLOv8.
# При первом запуске она сама скачается из сети (около 6 МБ).
print("Загрузка нейросети YOLOv8...")
model = YOLO("yolov8n.pt")

# 2. Включаем камеру. 0 — это стандартная веб-камера твоего ноутбука/ПК.
# (В школе сюда вместо 0 вставляется ссылка на школьную камеру).
cap = cv2.VideoCapture(0)

print("Нейросеть запущена! Нажмите 'q' в окне видео, чтобы выйти.")

# Время последней отправки данных в базу (чтобы не спамить каждую миллисекунду)
last_update_time = time.time()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Не удалось получить изображение с камеры.")
        break

    # 3. Запускаем распознавание объектов. classes=[0] означает искать ТОЛЬКО людей.
    # verbose=False отключает лишний спам текстом в терминал.
    results = model(frame, classes=[0], verbose=False)

    # Считаем, сколько людей нейросеть нашла на этом кадре
    people_count = len(results[0].boxes)
    
    # Считаем примерное время ожидания (1 человек = 1 минута)
    wait_time = people_count * 1

    # Рисуем рамки вокруг обнаруженных людей прямо на видео
    annotated_frame = results[0].plot()

    # Пишем текст с количеством людей на самом видео для наглядности
    cv2.putText(annotated_frame, f"People in queue: {people_count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # 4. Оптимизация: обновляем базу данных раз в 3 секунды, чтобы не перегружать ПК
    current_time = time.time()
    if current_time - last_update_time > 3:
        try:
            # Подключаемся к нашей базе данных сайта
            conn = sqlite3.connect("canteen.db")
            cursor = conn.cursor()
            
            # Записываем количество людей и время в таблицу queue (строка с id=1)
            cursor.execute("""
                UPDATE queue 
                SET people_count=?, wait_time=? 
                WHERE id=1
            """, (people_count, wait_time))
            
            conn.commit()
            conn.close()
            last_update_time = current_time
            print(f"[ИИ Обновление] Людей в очереди: {people_count}. Время: ~{wait_time} мин.")
        except Exception as e:
            # Если сайт ещё не запущен и базы нет, программа просто пропустит этот шаг
            pass

    # Показываем окно с видеопотоком и рамками ИИ
    cv2.imshow("Камера Столовой (Тест ИИ)", annotated_frame)

    # Если нажать клавишу 'q' на английской раскладке — программа закроется
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Освобождаем ресурсы камеры и закрываем окна
cap.release()
cv2.destroyAllWindows()
