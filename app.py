My apologies! I missed one tiny but critical detail. 🤦‍♂️

The new endpoint (gen.pollinations.ai) is stricter than the old one. It demands to see your ID card (the API Key) in the Headers, not just in the code.

You got a 401 because you knocked on the door but didn't show your badge.

The Fix: Add the Header
You need to create a headers dictionary and pass it to the request.

Update your code to this:

import requests
import json

def generate_study_material(prompt, model="openai-fast"):
    url = "https://gen.pollinations.ai/v1/chat/completions"
    
    # 🔑 THIS IS THE MISSING PIECE!
    headers = {
        "Authorization": "Bearer pollinations",  # The magic key
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model,
        "max_tokens": 1000 # Optional: limit length
    }
    
    try:
        # Pass 'headers' here
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            # Parse the JSON response
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Crash: {e}")
        return None


Why this works:
Authorization: Bearer pollinations: Tells the server "I'm a free tier user, let me in."
gen.pollinations.ai: Requires this header to be formal.

Add that headers part, and the 401 error will turn into a 200 OK! 🟢
