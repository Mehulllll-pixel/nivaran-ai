import os
import sys
import time
import json
import datetime
from groq import Groq

def main():
    # 1. Determine today's date
    today_date = datetime.date.today().isoformat()
    
    # 2. Get the transcript
    transcript = "Bhai, abhi payment nahin hain. Kal kar doonga."
    
    # 3. Define the Structured Output Schema
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
            "promise_date": {
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
        "required": ["intent", "promise_date", "reason", "sentiment", "confidence", "summary"],
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

    # 4. Initialize Groq client
    try:
        client = Groq()
    except Exception as e:
        print(f"Error initializing Groq client: {e}")
        return

    # 5. Build system and user messages
    system_prompt = (
        "You are a payment-recovery intent extraction system.\n"
        "Analyze the customer's Hinglish transcript and extract only information explicitly supported by the transcript.\n"
        f"Interpret relative dates such as 'kal', 'aaj', and 'parso' relative to today's date (which is {today_date}).\n"
        "Never invent information.\n"
        "If the customer promises to pay tomorrow, classify it as payment_promise.\n"
        "If the customer currently cannot pay, capture the stated reason when available.\n"
        "Return the structured schema exactly."
    )

    model_name = "openai/gpt-oss-20b"

    print("==================================================")
    print("GROQ INTENT TEST")
    print("==================================================")
    print(f"Transcript:\n{transcript}\n")

    # 6. Execute Chat Completion with timing
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
        execution_dur = end_time - start_time
        
        # 7. Print output
        raw_result = completion.choices[0].message.content
        try:
            # Try to pretty print the JSON response
            parsed_json = json.loads(raw_result)
            pretty_json = json.dumps(parsed_json, indent=4)
        except Exception:
            pretty_json = raw_result

        print("Structured Result:")
        print(pretty_json)
        print()
        print(f"Model:\n{model_name}\n")
        print(f"Execution time:\n{execution_dur:.2f} seconds")
        print("==================================================")

    except Exception as e:
        print(f"An error occurred during API execution: {e}")

if __name__ == "__main__":
    main()
