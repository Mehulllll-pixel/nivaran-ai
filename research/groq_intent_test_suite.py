import os
import sys
import time
import json
import datetime
from groq import Groq

def main():
    # 1. Determine today's date
    today_date = datetime.date.today().isoformat()
    
    # 2. Define the 15 test cases
    test_cases = [
        ("TEST 1", "Bhai abhi paise nahi hain, kal pakka payment kar dunga."),
        ("TEST 2", "Sir payment maine kal hi kar diya hai, ek baar check kar lijiye."),
        ("TEST 3", "Abhi payment nahi kar sakta, salary aane ke baad karunga."),
        ("TEST 4", "Mujhe payment nahi karni, aap jo karna hai kar lo."),
        ("TEST 5", "Galat number hai sir, mujhe kisi payment ke baare mein nahi pata."),
        ("TEST 6", "Sir maine ye payment already dispute ki hui hai, main is amount ko accept nahi karta."),
        ("TEST 7", "Main 15 September ko payment kar dunga."),
        ("TEST 8", "Parso payment kar dunga."),
        ("TEST 9", "Dekhta hoon bhai, abhi kuch confirm nahi hai."),
        ("TEST 10", "₹2500 kal salary aate hi de dunga."),
        ("TEST 11", "Paise nahi hain aur main abhi payment nahi karunga."),
        ("TEST 12", "Sir thoda time de do, salary credit hote hi payment settle kar dunga."),
        ("TEST 13", "Kal dekhte hain payment ka kya karna hai."),
        ("TEST 14", "Payment complete ho chuki hai sir, transaction ID bhi hai mere paas."),
        ("TEST 15", "Kal shaantri aai ki, kal kar doonga.")
    ]
    
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

    model_name = "openai/gpt-oss-20b"
    system_prompt = (
        "You are a payment-recovery intent extraction system.\n"
        "Analyze the customer's Hinglish transcript and extract only information explicitly supported by the transcript.\n"
        f"Interpret relative dates such as 'kal', 'aaj', 'parso', and 'next week' relative to today's date (which is {today_date}).\n"
        "Never invent information.\n"
        "If the customer promises to pay tomorrow, classify it as payment_promise.\n"
        "If the customer currently cannot pay, capture the stated reason when available.\n"
        "Return the structured schema exactly."
    )

    results = []

    print("==================================================")
    print("STARTING GROQ INTENT TEST SUITE")
    print(f"Model: {model_name}")
    print(f"Today's Date: {today_date}")
    print("==================================================")

    # 5. Loop over each test case
    for test_id, transcript in test_cases:
        print(f"Running {test_id}...")
        start_time = time.time()
        
        intent = "ERROR"
        promise_date = "N/A"
        reason = "N/A"
        sentiment = "N/A"
        confidence = 0.0
        summary = "N/A"
        duration = 0.0

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
            
            intent = parsed.get("intent", "unclear")
            promise_date = parsed.get("promise_date")
            reason = parsed.get("reason")
            sentiment = parsed.get("sentiment", "neutral")
            confidence = parsed.get("confidence", 0.0)
            summary = parsed.get("summary", "")
            
        except Exception as e:
            summary = f"API Error: {str(e)}"
            duration = time.time() - start_time
            
        results.append({
            "test_id": test_id,
            "transcript": transcript,
            "intent": intent,
            "promise_date": promise_date,
            "reason": reason,
            "sentiment": sentiment,
            "confidence": confidence,
            "duration": duration,
            "summary": summary
        })
        time.sleep(0.5) # Avoid aggressive rate limiting

    print("\n" + "=" * 80)
    print("TEST SUITE SUMMARY TABLE")
    print("=" * 80)
    
    # Table header
    header_fmt = "{:<8} | {:<50} | {:<18} | {:<12} | {:<12} | {:<10} | {:<10} | {:<8}"
    row_fmt = "{:<8} | {:<50} | {:<18} | {:<12} | {:<12} | {:<10} | {:<10.2f} | {:<8.2f}"
    
    print(header_fmt.format(
        "Test #", 
        "Input Transcript (Truncated)", 
        "Intent", 
        "Promise Date", 
        "Reason", 
        "Sentiment", 
        "Conf.", 
        "Time (s)"
    ))
    print("-" * 135)
    
    for r in results:
        # Truncate transcript for clean terminal viewing if needed
        disp_transcript = r["transcript"]
        if len(disp_transcript) > 47:
            disp_transcript = disp_transcript[:47] + "..."
            
        p_date = str(r["promise_date"])
        re_reason = str(r["reason"])
        
        print(row_fmt.format(
            r["test_id"],
            disp_transcript,
            r["intent"],
            p_date,
            re_reason,
            r["sentiment"],
            r["confidence"],
            r["duration"]
        ))
        
    print("=" * 135)
    print("\nDetailed Summary Texts:")
    for r in results:
        print(f"{r['test_id']}: {r['summary']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
