import os
import sys
import time
import json
import datetime
from groq import Groq

def resolve_time_reference(time_reference, explicit_date, today_date_obj):
    """
    Deterministic Python date resolution logic.
    """
    if time_reference == "today":
        return today_date_obj.isoformat()
    elif time_reference == "yesterday":
        return (today_date_obj - datetime.timedelta(days=1)).isoformat()
    elif time_reference == "tomorrow":
        return (today_date_obj + datetime.timedelta(days=1)).isoformat()
    elif time_reference == "day_before_yesterday":
        return (today_date_obj - datetime.timedelta(days=2)).isoformat()
    elif time_reference == "day_after_tomorrow":
        return (today_date_obj + datetime.timedelta(days=2)).isoformat()
    elif time_reference == "explicit_date":
        return explicit_date  # Should be formatted as YYYY-MM-DD from LLM
    elif time_reference == "next_week":
        return None
    elif time_reference == "no_date":
        return None
    else:
        return None

def main():
    # Set the static date for this test run as specified
    today_str = "2026-08-22"
    today_date_obj = datetime.date(2026, 8, 22)
    
    # Define the 15 test cases
    test_cases = [
        ("TEST 1", "Kal payment kar dunga."),
        ("TEST 2", "Kal payment kar diya tha."),
        ("TEST 3", "Parso payment kar dunga."),
        ("TEST 4", "Parso hi payment kar diya tha."),
        ("TEST 5", "Aaj payment kar dunga."),
        ("TEST 6", "Aaj payment kar diya."),
        ("TEST 7", "Kal payment nahi karunga."),
        ("TEST 8", "Kal dekhte hain payment ka kya karna hai."),
        ("TEST 9", "15 September ko payment kar dunga."),
        ("TEST 10", "15 September ko payment kar diya tha."),
        ("TEST 11", "Salary aate hi payment kar dunga."),
        ("TEST 12", "Agale hafte payment kar dunga."),
        ("TEST 13", "Main payment already kar chuka hoon."),
        ("TEST 14", "Abhi paise nahi hain, kal pakka payment kar dunga."),
        ("TEST 15", "Parso salary aayegi, uske baad payment kar dunga.")
    ]
    
    # Structured outputs json schema
    schema = {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [
                    "payment_promise",
                    "payment_completed",
                    "payment_delay",
                    "payment_refusal",
                    "unable_to_pay",
                    "wrong_number",
                    "dispute",
                    "unclear"
                ]
            },
            "time_reference": {
                "type": "string",
                "enum": [
                    "today",
                    "yesterday",
                    "tomorrow",
                    "day_before_yesterday",
                    "day_after_tomorrow",
                    "explicit_date",
                    "next_week",
                    "no_date"
                ]
            },
            "explicit_date": {
                "type": ["string", "null"]
            },
            "reason": {
                "type": ["string", "null"]
            },
            "sentiment": {
                "type": "string",
                "enum": [
                    "positive",
                    "neutral",
                    "negative"
                ]
            },
            "confidence": {
                "type": "number"
            },
            "summary": {
                "type": "string"
            }
        },
        "required": ["intent", "time_reference", "explicit_date", "reason", "sentiment", "confidence", "summary"],
        "additionalProperties": False
    }

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "payment_intent",
            "strict": True,
            "schema": schema
        }
    }

    # Initialize client
    try:
        client = Groq()
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return

    model_name = "openai/gpt-oss-20b"
    system_prompt = (
        "You are a payment-recovery intent extraction system.\n\n"
        "Understand the meaning of the customer's Hinglish statement using the full sentence and context.\n"
        "Pay special attention to verb tense and temporal context.\n"
        "The same word can refer to different temporal directions depending on context.\n\n"
        "For example:\n"
        "'Parso payment kar dunga.' means a future payment commitment.\n"
        "'Parso hi payment kar diya tha.' means a payment completed in the past.\n\n"
        "Do not determine temporal meaning using keywords alone.\n"
        "Do not perform calendar arithmetic.\n"
        "Return the appropriate semantic time_reference category.\n"
        "If no payment-related date is stated, return no_date.\n"
        "If the customer explicitly states a calendar date, use explicit_date and provide the date in YYYY-MM-DD format.\n"
        "Never invent a date or promise."
    )

    print("==================================================")
    print("STARTING GROQ TEMPORAL TEST SUITE")
    print(f"Model: {model_name}")
    print(f"Fixed Today's Date Context: {today_str}")
    print("==================================================")

    for test_name, transcript in test_cases:
        print(f"\n==================================================")
        print(f"{test_name}")
        print(f"==================================================")
        print(f"Transcript:\n{transcript}\n")
        
        start_time = time.time()
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript}
                ],
                response_format=response_format,
                temperature=0.0
            )
            end_time = time.time()
            duration = end_time - start_time
            
            raw_result = completion.choices[0].message.content
            parsed = json.loads(raw_result)
            
            # Print parsed LLM JSON
            print("LLM Result:")
            print(json.dumps(parsed, indent=4))
            print()
            
            # Resolve using Python
            time_ref = parsed.get("time_reference", "no_date")
            exp_date = parsed.get("explicit_date")
            resolved_date = resolve_time_reference(time_ref, exp_date, today_date_obj)
            
            print(f"Python Resolved Date:\n{resolved_date}\n")
            print(f"Execution Time:\n{duration:.2f} seconds")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            
        print("==================================================")
        time.sleep(0.5)

if __name__ == "__main__":
    main()
