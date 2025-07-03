from flask import Flask, request, jsonify
import os
import pandas as pd
import datetime
import json
import subprocess
import time

app = Flask(__name__)

# --- مسار ملف المهام اليومية (tasks.csv) ---
# لضمان أن Render يحفظ في مكان يمكن الوصول إليه وقراءته
# سنحدد مساراً نسبياً في مجلد العمل الحالي
TASKS_FILE = "tasks.csv" 


# دالة لتحميل المهام (نسخة من دالة Streamlit)
def load_tasks_from_csv():
    expected_cols = ["التاريخ", "المشرف", "المهمة", "الملاحظات"]
    if os.path.exists(TASKS_FILE):
        try:
            df = pd.read_csv(TASKS_FILE)
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
                return df[expected_cols]
            except pd.errors.EmptyDataError:
                return pd.DataFrame(columns=expected_cols)
        return pd.DataFrame(columns=expected_cols)
    return pd.DataFrame(columns=expected_cols) # إذا لم يكن الملف موجوداً، نُرجع DataFrame فارغاً بالأعمدة المتوقعة

# دالة لحفظ المهام (نسخة من دالة Streamlit)
def save_tasks_to_csv(df):
    df.to_csv(TASKS_FILE, index=False)


# --- مسار الـ Webhook الذي سيتلقى الرسائل من WATI ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json() 

        print("Received Webhook Data:", json.dumps(data, indent=2, ensure_ascii=False))

        message_text = "لا يمكن استخلاص نص الرسالة"
        sender_number = "غير معروف"

        try:
            if 'messages' in data and len(data['messages']) > 0:
                msg = data['messages'][0]
                if 'text' in msg and 'body' in msg['text']:
                    message_text = msg['text']['body']
                elif 'type' in msg and msg['type'] == 'text' and 'text' in msg:
                    message_text = msg['text']['body']
                
                if 'sender' in data and 'wa_id' in data['sender']:
                    sender_number = data['sender']['wa_id']
                elif 'from' in msg:
                    sender_number = msg['from']
                        
            elif 'data' in data and 'message' in data['data'] and 'text' in data['data']['message']:
                message_text = data['data']['message']['text']
                sender_number = data['data']['message'].get('from', 'غير معروف')

            elif 'SmsMessageSid' in data: 
                message_text = data.get('Body', 'رسالة SMS')
                sender_number = data.get('From', 'رقم SMS')
            
        except Exception as e:
            print(f"Error extracting message from webhook: {e}")
            print(f"Full data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            message_text = f"خطأ في استخلاص الرسالة: {e}"

        print(f"Message from {sender_number}: {message_text}")
        
        extracted_supervisor = "لم يتم التحديد"
        extracted_task = message_text
        extracted_notes = f"رسالة من واتساب (رقم: {sender_number})"

        message_lower = message_text.lower()
        if "المشرف الاول" in message_lower:
            extracted_supervisor = "المشرف الأول"
        elif "المشرف الثاني" in message_lower:
            extracted_supervisor = "المشرف الثاني"
        elif "المشرف الثالث" in message_lower:
            extracted_supervisor = "المشرف الثالث"
        elif "عماله" in message_lower or "عمال" in message_lower:
            extracted_supervisor = "العمالة العامة"
        elif "صيانه" in message_lower or "فني" in message_lower:
            extracted_supervisor = "فريق الصيانة"
        elif "امين" in message_lower or "امن" in message_lower:
            extracted_supervisor = "أمن"
        elif "المديره" in message_lower:
            extracted_supervisor = "المديرة"
        elif "سائق" in message_lower or "سائقون" in message_lower:
            extracted_supervisor = "السائقون"
        elif "زراعه" in message_lower or "زراعي" in message_lower:
            extracted_supervisor = "الزراعة"
        elif "نظافه" in message_lower or "منظف" in message_lower:
            extracted_supervisor = "عمال النظافة"
        
        try:
            tasks_df = load_tasks_from_csv()
            new_task = pd.DataFrame([{
                "التاريخ": datetime.date.today().isoformat(),
                "المشرف": extracted_supervisor,
                "المهمة": extracted_task,
                "الملاحظات": extracted_notes
            }])
            updated_tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
            save_tasks_to_csv(updated_tasks_df)
            print("Task saved to tasks.csv successfully on Render!") # <--- رسالة تأكيد معدلة
        except Exception as e:
            print(f"Error saving task to CSV on Render: {e}") # <--- رسالة خطأ معدلة

        return jsonify({"status": "success", "message": "Webhook received and processed"}), 200

    return jsonify({"status": "error", "message": "Method not allowed"}), 405


# --- تشغيل Flask على المنفذ الصحيح لـ Render ---
if __name__ == '__main__':
    NGROK_AUTH_TOKEN = "2zM3ArKoDRYpS8Ef4cENoV7WSzD_84t58AQCMkTUFWAjfji1X" 
    NGROK_EXECUTABLE_PATH = "/Users/fahadahmed/Desktop/whatsapp_webhook_backend/ngrok" 

    if not NGROK_AUTH_TOKEN:
        print("\n=== NGROK AUTH TOKEN REQUIRED ===")
        print("Please get your Ngrok Auth Token from https://dashboard.ngrok.com/get-started/your-authtoken")
        print("and replace 'YOUR_NGROK_AUTH_TOKEN' in app_backend.py with your actual token.")
        print("==============================\n")
        exit()

    try:
        subprocess.run([NGROK_EXECUTABLE_PATH, 'authtoken', NGROK_AUTH_TOKEN], check=True)
        print("Ngrok authentication token set.")

        print("Starting ngrok tunnel...")
        ngrok_process = subprocess.Popen([NGROK_EXECUTABLE_PATH, 'http', '5000', '--log=stdout'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        public_url = None
        time.sleep(5) 

        while True:
            line = ngrok_process.stdout.readline()
            if not line:
                break
            print(f"Ngrok output: {line.strip()}")
            if "url=" in line:
                parts = line.split("url=")
                if len(parts) > 1:
                    url_part = parts[1].split()[0]
                    if url_part.startswith("https://"):
                        public_url = url_part
                        break 
            if "failed to start" in line.lower() or "error" in line.lower():
                print("Ngrok reported an error during startup. Please check Ngrok's documentation or logs.")
                break

        if public_url:
            print(f"\n* Flask app exposed to the internet at: {public_url}")
            print(f"* Use this URL + /webhook as your WATI Webhook URL: {public_url}/webhook")
            print("* Press Ctrl+C to disconnect Ngrok and stop Flask.")
        else:
            print("Failed to get public URL from ngrok output. Attempting to get URL from ngrok API...")
            try:
                import requests
                response = requests.get("http://localhost:4040/api/tunnels")
                tunnels_data = response.json()
                for tunnel in tunnels_data.get("tunnels", []):
                    if tunnel["proto"] == "https":
                        public_url = tunnel["public_url"]
                        print(f"\n* Flask app exposed to the internet at (from API): {public_url}")
                        print(f"* Use this URL + /webhook as your WATI Webhook URL: {public_url}/webhook")
                        break
                if not public_url:
                    print("Failed to get public URL from ngrok API. Ensure ngrok is running correctly and its API is accessible.")
            except Exception as api_e:
                print(f"Error accessing ngrok API: {api_e}")
            
            if not public_url:
                print("Could not obtain a public URL from Ngrok. Please check your Ngrok installation and Auth Token.")
                exit()

    except FileNotFoundError:
        print("\n--- NGROK EXECUTABLE NOT FOUND ---")
        print("Please ensure ngrok executable is at the path specified in NGROK_EXECUTABLE_PATH.")
        print("You can download ngrok from https://ngrok.com/download and place it in your project folder.")
        print("===============================\n")
        exit()
    except subprocess.CalledProcessError as e:
        print(f"\n--- NGROK COMMAND ERROR ---")
        print(f"Error running ngrok command: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        print("===============================\n")
        exit()
    except Exception as e:
        print(f"\n--- UNEXPECTED ERROR STARTING NGROK ---")
        print(f"An unexpected error occurred: {e}")
        print("===============================\n")
        exit()
    
    app.run(port=5000, debug=True)
     
