from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime

app = Flask(__name__)

# ✅ المسار إلى ملف المهام داخل مشروع creekobhur-dashboard
TASKS_CSV_PATH = "../creekobhur-dashboard/tasks.csv"  # تأكد من صحة المسار حسب موقع المجلد

# 🟢 تأكد من وجود الملف وإنشائه إن لم يكن موجودًا
if not os.path.exists(TASKS_CSV_PATH):
    with open(TASKS_CSV_PATH, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "sender", "task"])

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("✅ Received Webhook Data:", data)

    # استخراج الرسالة والمرسل
    message = data.get("text", "").strip()
    sender = data.get("waId", "unknown")

    # التحقق من وجود رسالة
    if message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 📝 إضافة المهمة إلى ملف المهام
        with open(TASKS_CSV_PATH, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, sender, message])
        
        print("📁 Task saved successfully to:", TASKS_CSV_PATH)
        return jsonify({"status": "success", "message": "Task saved"}), 200
    else:
        return jsonify({"status": "error", "message": "No text found"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)




