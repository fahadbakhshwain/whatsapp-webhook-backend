from flask import Flask, request, jsonify
import os
import pandas as pd
import datetime
import json

app = Flask(__name__)

TASKS_FILE = "tasks.csv"

def load_tasks_from_csv():
    expected_cols = ["التاريخ", "المشرف", "المهمة", "الملاحظات"]
    try:
        df = pd.read_csv(TASKS_FILE)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""
        return df[expected_cols]
    except FileNotFoundError:
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(TASKS_FILE, index=False)
        return df
    except Exception as e:
        if isinstance(e, pd.errors.EmptyDataError):
            return pd.DataFrame(columns=expected_cols)
        print(f"Unexpected error reading {TASKS_FILE}: {e}")
        return pd.DataFrame(columns=expected_cols)

def save_tasks_to_csv(df):
    df.to_csv(TASKS_FILE, index=False)

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
                if 'text' in msg and isinstance(msg['text'], dict) and 'body' in msg['text']:
                    message_text = msg['text']['body']
                elif 'type' in msg and msg['type'] == 'text' and isinstance(msg.get('text'), str):
                    message_text = msg['text']

                if isinstance(data.get('sender'), dict) and 'wa_id' in data['sender']:
                    sender_number = data['sender']['wa_id']
                elif isinstance(msg, dict) and 'from' in msg:
                    sender_number = msg['from']
                elif 'waId' in data:
                    sender_number = data['waId']

            elif 'text' in data and isinstance(data['text'], str):
                message_text = data['text']
                sender_number = data.get('waId', 'غير معروف')

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
            print("Task saved to tasks.csv successfully on Render!")
        except Exception as e:
            print(f"Error saving task to CSV on Render: {e}")

        return jsonify({"status": "success", "message": "Webhook received and processed"}), 200

    return jsonify({"status": "error", "message": "Method not allowed"}), 405

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)



