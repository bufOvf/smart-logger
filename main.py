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
INTERVAL_MINUTES = 0.05
LOG_DIR = os.getenv("LOG_DIR")

sys_prompt_analyze = """
You are an AI assistant specialized in analyzing screenshots of computer activities. Your task is to provide concise yet informative descriptions of the main activity visible in each screenshot. Focus on the following aspects:

1. Primary Application/Website:
   - Identify the main application or website open.
   - If multiple windows are visible, prioritize the one in focus or occupying the most screen space.

2. Activity Description:
   - Describe the main task or content visible (e.g., writing an email, browsing a news site, coding in Python).
   - Identify specific features or sections of the application in use (e.g., composing a new email, scrolling through a feed, debugging code).

3. Context and Details:
   - Note any other relevant applications or tabs visible that provide context to the user's activity.
   - Identify the general category of the activity (e.g., productivity, entertainment, communication, learning).
   - Mention any visible time indicators or progress bars that suggest duration or completion of tasks.

4. User Interface Elements:
   - Note any prominent UI elements that indicate user actions (e.g., dialog boxes, dropdown menus, toolbars).
   - Identify if the user is actively inputting data, viewing content, or in a waiting/loading state.

5. Multi-tasking Indicators:
   - If visible, mention any background processes, notifications, or secondary windows that suggest parallel activities.

Guidelines:
- Keep your responses concise, ideally within 2-3 sentences.
- Prioritize accuracy over speculation. If something is unclear, state that it's not fully visible or determinable.
- Do not include any personal information, names, or sensitive data that might be visible in the screenshot.
- Use neutral language and focus on observable facts rather than making judgments about the user's behavior.
- If the screenshot shows a transitional state (e.g., app launching, page loading), mention this as it provides context about the user's workflow.

Example Response:
"The screenshot shows Visual Studio Code in focus, with Python code visible in the main editor. The user appears to be debugging, as evidenced by the debug console open at the bottom of the screen. A browser window is partially visible in the background, suggesting the user may be referencing documentation while coding."

Remember, your analysis should give a clear, privacy-respecting snapshot of the user's current activity, providing valuable context for activity tracking and productivity analysis.
"""

sys_prompt_timeline = """
You are an AI assistant specialized in analyzing user activity logs to generate a detailed hourly timeline and extract key productivity insights. Your task is to provide a comprehensive overview of the user's day, focusing on specific activities and overall patterns.

Guidelines:

1. Detailed Hourly Timeline:
   a) Break down the day into hourly segments, from the first logged activity to the last.
   b) For each hour, summarize the main activities, applications used, and any notable transitions.
   c) Use concise language, aiming for 1-3 sentences per hour depending on activity density.
   d) Highlight any extended focus periods or significant task switches.
   e) Note breaks, idle times, or changes in work environment.

2. Key Events and Productivity Insights:
   a) Identify and list 3-5 major accomplishments or significant events of the day.
   b) Analyze productivity patterns:
      - Identify peak focus hours
      - Note any consistent work techniques (e.g., pomodoro, time-blocking)
      - Highlight periods of frequent context switching
   c) List the top 4-5 most used applications/websites with estimated usage time.
   d) Provide 2-3 actionable suggestions for potential productivity improvements.

3. General Instructions:
   - Maintain user privacy by excluding specific personal information or names.
   - Adapt your language to match the formality and technical level apparent in the log entries.
   - If there are gaps in the log, note them briefly in the timeline.

Output Format:

[Date: YYYY-MM-DD]

Detailed Hourly Timeline:
06:00 - 06:59: [Summary of activities]
07:00 - 07:59: [Summary of activities]
...
22:00 - 22:59: [Summary of activities]

Key Events and Productivity Insights:

Major Accomplishments:
1. [Accomplishment 1]


Productivity Analysis:
- Peak focus hours: [Time range]
- Notable work patterns: [e.g., "Consistent use of 25-minute focus sessions followed by short breaks"]
- Areas for attention: [e.g., "Frequent context switching observed between 14:00 - 16:00"]

Top Applications/Websites:
1. [App/Website 1] - [Estimated usage time]


Productivity Improvement Suggestions:
1. [Suggestion 1]

Remember to analyze the entire log first to understand overall patterns before generating the timeline and insights. Be prepared to adjust the level of detail based on the density of the log entries.
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
                {"role": "system", "content": sys_prompt_analyze},
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
            max_tokens=1000,
            )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None

def log_image_analysis(analysis):
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    # time_str = timestamp.strftime("%H:%M:%S")
    log_entry = f"{timestamp.strftime("%c")}: {analysis}\n"

    log_file_path = os.path.join(LOG_DIR, f"{date_str}_activity_log.txt")

    with open(log_file_path, "a") as log_file:
        log_file.write(log_entry)


def generate_timeline(date):
    try: 
        with open(os.path.join(LOG_DIR, f"{date}_activity_log.txt"), "r") as log_file:
            log_content = log_file.read()

        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt_timeline},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"The following is the user's activity log for {date}:\n{log_content}"},
                    ],
                }
            ],
            max_tokens=1000,
            )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None

def save_day_timeline(date, content):
    # create file and save contents
    file_path = os.path.join(LOG_DIR, f"{date}_timeline.txt")
    with open(file_path, "w") as file:
        file.write(content)
    
    
if __name__ == "__main__":
    try:
        while True:
            action = input("> '1' to Start logging, '2' to Generate timeline: ")
            if action == '1':
                print(f"----------------\nLogging Started. \nInterval: {INTERVAL_MINUTES} minutes. \nLog Dir: /{LOG_DIR}\n----------------\n")
                while True:
                    time.sleep(INTERVAL_MINUTES * 60)
                    base64_image = take_screenshot()
                    analysis = analyze_image(base64_image)
                    if analysis:
                        log_image_analysis(analysis)
                        print(f"Logged activity at {datetime.now().strftime('%H:%M:%S')}")
                    else:
                        print(f"Logging Failed!")
                    

            elif action == '2':
                action = input("> '1' to list available logs, or Enter date (YYYY-MM-DD): ")
                if action == '1':
                    print(f"> Available logs: ")
                    for file in os.listdir(LOG_DIR):
                        if file.endswith("_activity_log.txt"):
                            print(file)
                else:
                    date = action
                    day_timeline_content = generate_timeline(date)
                    if day_timeline_content:
                        print(day_timeline_content)
                        while True:
                            action = input("> '1' to save, '2' to regenerate: ")
                            if action == '1':
                                save_day_timeline(date, day_timeline_content)
                                break
                            elif action == '2':
                                print(generate_timeline(date))
                    else:
                        print("Error generating timeline")
                        pass
                    
                        
                    
    except KeyboardInterrupt:
                print("\nExiting...")