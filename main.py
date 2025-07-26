import os
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# --- Perubahan di sini: Ganti import Gemini dengan Azure AI Inference ---
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential # Diperlukan untuk kredensial

app = Flask(__name__)

# Ambil dari environment variables Replit (Secrets)
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
# --- Perubahan di sini: Ganti GEMINI_API_KEY dengan GITHUB_TOKEN ---
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') # Ini adalah Secret baru Anda

# Inisialisasi LINE Bot API dan Webhook Handler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Perubahan di sini: Konfigurasi GitHub AI ---
github_ai_client = None # Inisialisasi klien AI sebagai None
if GITHUB_TOKEN:
    try:
        # Endpoint dan model sesuai yang Anda berikan
        github_endpoint = "https://models.github.ai/inference"
        github_model = "openai/gpt-4.1" # Model yang Anda sebutkan
        
        github_ai_client = ChatCompletionsClient(
            endpoint=github_endpoint,
            credential=AzureKeyCredential(GITHUB_TOKEN), # Menggunakan GitHub Token sebagai kredensial
        )
        print("GitHub AI client initialized.")
    except Exception as e:
        print(f"Error initializing GitHub AI client: {e}")
        # Jika ada error saat inisialisasi, pastikan klien tetap None
        github_ai_client = None
else:
    print("GITHUB_TOKEN not found. GitHub AI will not be used.")


# --- Perubahan di sini: Tambahkan 'GET' untuk verifikasi webhook LINE ---
@app.route("/callback", methods=['POST', 'GET'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        print(f"Error handling event: {e}")
        abort(500)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    Fungsi untuk menangani event pesan teks dan membalas dengan GitHub AI.
    """
    user_message = event.message.text
    reply_text = ""

    # --- Perubahan di sini: Logika pemanggilan GitHub AI ---
    if github_ai_client:
        try:
            print(f"User message: {user_message}")
            response = github_ai_client.complete(
                messages=[
                    # Anda bisa menyesuaikan SystemMessage di sini jika perlu
                    SystemMessage(content="selalu balas dengan bahasa indonesia dan singkat dan padat dan tidak menggunakan kata-kata yang tidak perlu"), 
                    UserMessage(content=user_message),
                ],
                temperature=1, # Parameter sesuai petunjuk Anda
                top_p=1,       # Parameter sesuai petunjuk Anda
                model=github_model # Menggunakan model dari konfigurasi GitHub AI
            )
            reply_text = response.choices[0].message.content
            print(f"GitHub AI response: {reply_text}")
        except Exception as e:
            print(f"Error calling GitHub AI: {e}")
            reply_text = "Maaf, saya tidak bisa memproses permintaan Anda saat ini karena masalah dengan AI. Silakan coba lagi nanti."
    else:
        reply_text = "Bot ini belum terhubung dengan AI (GitHub). Silakan hubungi admin."

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

