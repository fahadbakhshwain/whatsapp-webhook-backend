# 📬 WhatsApp Webhook Backend

A backend service built to receive WhatsApp messages from managers, extract task details, and update the live `tasks.csv` file used by the [Creek Obhur Smart Management Dashboard](https://github.com/fahadbakhshwain/creekobhur-dashboard).

---

## 🔗 Overview

This backend receives WhatsApp messages (via a Business API provider like Twilio/WATI), processes the content, and saves structured task information into `tasks.csv`.

The updated CSV is read directly by the Creek Obhur Streamlit dashboard, allowing supervisors to see live updates without any manual input.

---

## ⚙️ How It Works

1. **Webhook Endpoint (`/webhook`)**  
   Accepts POST requests from your WhatsApp Business API provider.

2. **Message Processing**  
   (Optional NLP processing planned):
   - Extract task description, location, team, and priority from raw WhatsApp message.

3. **CSV Update**  
   Saves structured task into `tasks.csv`, which is used directly by the frontend dashboard.

---

## 🧪 Project Structure

| File | Description |
|------|-------------|
| `app_backend.py` | Flask app to handle webhook and update CSV |
| `tasks.csv` | Main task database (read by Creek Obhur dashboard) |
| `start.sh` | Startup script for deployment |
| `requirements.txt` | Python dependencies |
| `ngrok` | Tunnel for local webhook testing |

---

## 🚀 How to Run Locally

```bash
pip install -r requirements.txt
python app_backend.py
To expose local server for testing:

bash
Copy
Edit
./ngrok http 5000
Copy the HTTPS link and paste it into your WhatsApp Business Webhook settings.

🧠 NLP Module (Planned)
Future updates will include:

Named Entity Recognition to extract task info from free text.

Intent classification (task vs note vs reminder).

Automatic user tagging and section routing.

📎 Related Projects
🔗 Creek Obhur Dashboard: Smart dashboard that reads from tasks.csv and shows tasks for toilets, beaches, and staff.

📝 Example Message from Manager
"تنظيف الجلسات تحت المظلات في الشاطئ رقم ٢ اليوم الساعة ٥ العصر - ضروري جدًا قبل قدوم الزوار."

Output CSV row:

Task	Location	Time	Priority
تنظيف الجلسات	الشاطئ رقم ٢	5:00 PM	عالي

👤 Author
Fahad Bakhshwain
LinkedIn • Email

yaml
Copy
Edit

---














