import os
import io
from datetime import datetime
from PIL import ImageGrab
import time
from dotenv import load_dotenv
from openai import OpenAI
import base64


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
INTERVAL_MINUTES = 0.1
LOG_DIR = os.getenv("LOG_DIR")

sys_prompt = """
You are an AI assistant specialized in analyzing screenshots of computer activities. Your task is to provide brief, concise descriptions of the main activity visible in each screenshot. Focus on the following aspects:

1. Identify the primary application or website open.
2. Describe the main task or content visible (e.g., writing an email, browsing a news site, coding in Python).
3. Note any other relevant details that indicate the user's current activity.

Keep your responses short and to the point, ideally in one or two sentences. Do not include any personal information or names that might be visible. Your description should give a clear idea of what the user is doing at that moment.
"""


client = OpenAI(api_key=api_key)

def take_screenshot():
    screenshot = ImageGrab.grab()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='JPEG', quality=100)
    img_byte_arr = img_byte_arr.getvalue()
    return base64.b64encode(img_byte_arr).decode('utf-8')


def analyze_image(image):
    try: 
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this screenshot and describe the main activity."},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
            )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None
    

def log_analysis(analysis):
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M:%S")
    log_entry = f"{time_str}: {analysis}\n"

    log_file_path = os.path.join(LOG_DIR, f"{date_str}_activity_log.txt")

    with open(log_file_path, "a") as log_file:
        log_file.write(log_entry)

def main():
    print(f"----------------\nLogging Started. \nInterval: {INTERVAL_MINUTES} minutes. \nLog Dir: {LOG_DIR}.\n----------------\n")
    try:
        while True:
            base64_image = take_screenshot()
            analysis = analyze_image(base64_image)
            if analysis:
                log_analysis(analysis)
                print(f"Logged activity at {datetime.now().strftime('%H:%M:%S')}")
            else:
                print(f"Logging Failed!")
        
            time.sleep(INTERVAL_MINUTES * 60)

    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()