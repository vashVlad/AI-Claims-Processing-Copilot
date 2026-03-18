import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from prompts import TRIAGE_PROMPT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_claim(claim_text):
    prompt = TRIAGE_PROMPT.format(claim_text=claim_text)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content
    return json.loads(raw)

if __name__ == "__main__":
    test_claim = "My car was rear-ended at a stoplight yesterday. The bumper and trunk are damaged but no one was injured."
    result = analyze_claim(test_claim)
    print(json.dumps(result, indent=2))

    from scoring import calculate_priority

if __name__ == "__main__":
    test_claim = "My car was rear-ended at a stoplight yesterday. The bumper and trunk are damaged but no one was injured."
    result = analyze_claim(test_claim)
    scoring = calculate_priority(result)
    result.update(scoring)
    print(json.dumps(result, indent=2))
    