# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import google.generativeai as genai
# import asyncio

# # Configure Gemini API Key
# genai.configure(api_key="AIzaSyCQKrvjhxju7LqUenszve7b7n8RBZ3C0dA")

# app = FastAPI()

# # Update CORS middleware with specific origins
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"
#         # "https://med-assist1.vercel.app",  # React frontend
#         # "https://medassist1.onrender.com",  # Laravel backend
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class ChatRequest(BaseModel):
#     user_input: str

# # Async function to fetch response from Gemini
# async def fetch_gemini_response(prompt: str):
#     # Using gemini-2.0-flash model for faster responses
#     model = genai.GenerativeModel("gemini-2.0-flash", generation_config={"temperature": 0.4, "max_output_tokens": 500})
#     return await asyncio.to_thread(lambda: model.generate_content(prompt).text)

# @app.post("/chat")
# async def chat(data: ChatRequest):
#     # First, check if the input is health-related using Gemini
#     validation_prompt = f"""Determine if this is a health-related query: '{data.user_input}'
#     Just respond with 'yes' if it's related to health, symptoms, wellness, or lifestyle, or 'no' if it's not."""
    
#     is_health_related = await fetch_gemini_response(validation_prompt)
    
#     if is_health_related.lower().strip() != 'yes':
#         return {"response": "Give appropriate symptoms!"}
    
#     # Updated prompt with formatting instructions hidden from response
#     prompt = f"""You are an Ayurvedic health assistant. Analyze these symptoms: {data.user_input}

#     Provide a response in this exact format, but replace the placeholders with actual advice:

#     🌿 AYURVEDIC REMEDIES
#     [Replace with three specific remedies, keeping the bullet points]

#     🥗 DIETARY ADVICE
#     [Replace with specific dietary recommendations, keeping the bullet points]

#     🌟 LIFESTYLE RECOMMENDATIONS
#     [Replace with specific lifestyle advice, keeping the bullet points]

#     [Anylzize and If and only if there are serious symptoms or high chances of seriosness in syntompos, add this section:]
#     ⚠ MEDICAL ATTENTION
#     [Replace with specific warning signs and medical advice and message to counsult to doctor]

#     IMPORTANT: Replace all placeholder text. Keep emojis and formatting. Keep responses concise, professional, and easy to read. No disclaimers or jargon. , keep responses with (=>) rather than (*) """
    
#     response = await fetch_gemini_response(prompt)
#     return {"response": response}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import asyncio
import pdfplumber
import os
from pydantic import BaseModel

genai.configure(api_key="AIzaSyCQKrvjhxju7LqUenszve7b7n8RBZ3C0dA") 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "http://localhost:5173",  # React frontend
        "http://127.0.0.1:8000",  # Laravel backend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_FOLDER = "data"

def extract_all_pdf_text(folder_path: str) -> str:
    context_text = ""
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        context_text += page_text + "\n"
    return context_text.strip()

def build_prompt(user_input: str, context: str = ""):
    pdf_context_instruction = "\n📚 If you use any information from the following reference material, start your response with '(Based on Ayurvedic PDF Reference)'\n" if context.strip() else ""
    
    return f"""
System:
Please follow the 7 instructions below for all queries:
1. You are an Ayurvedic Health Assistant with expertise in Indian herbal remedies.
2. Always provide bullet-point responses under the following sections: 🌿 AYURVEDIC REMEDIES, 🥗 DIETARY ADVICE, 🌟 LIFESTYLE RECOMMENDATIONS.
3. If symptoms seem dangerous, add ⚠ MEDICAL ATTENTION with real warning signs.
4. Never use complex medical terms or disclaimers.
5. Keep the format with emojis and structured readability.
6. If it is different medical terms like Homeopathy, Naturopathy, Allopathy, then say: "I am an Ayurvedic Health Assistant and can't provide advice on other medical systems." Then continue with Ayurvedic advice.
7. Response should be precise, accurate, with no jargon, and only from authorized sources.{pdf_context_instruction}

📝 Additional Reference (use if relevant):
{context}

User:
Analyze this user symptom query: {user_input}
"""

async def fetch_gemini_response(prompt: str):
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config={"temperature": 0.4, "max_output_tokens": 500},
    )
    return await asyncio.to_thread(lambda: model.generate_content(prompt).text)

class ChatInput(BaseModel):
    user_input: str

@app.post("/chat")
async def chat(request: ChatInput):
    context = extract_all_pdf_text(PDF_FOLDER)

    validation_prompt = f"""Determine if this is a health-related query: '{request.user_input}'
Just respond with 'yes' if it's related to health, symptoms, wellness, or lifestyle, or 'no' if it's not."""
    
    is_health_related = await fetch_gemini_response(validation_prompt)

    if is_health_related.lower().strip() != 'yes':
        return {"response": "Please provide appropriate symptoms!"}

    final_prompt = build_prompt(request.user_input, context)
    response = await fetch_gemini_response(final_prompt)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
