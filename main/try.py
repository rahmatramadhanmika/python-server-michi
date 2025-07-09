from flask import Flask, request, jsonify, send_file
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from rapidfuzz import fuzz
import paho.mqtt.client as mqtt
import json
import threading
import time
import mysql.connector
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
SERVER_AUDIO_FOLDER = 'server_audio'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SERVER_AUDIO_FOLDER, exist_ok=True)

# Load environment variables
load_dotenv(find_dotenv(), override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MQTT Configuration
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_TOPIC_PUBLISH = "testtopic/mwtt"
MQTT_TOPIC_SUBSCRIBE = "testtopic/mwtt"

WAKE_WORDS = ["michi", "hai michi", "halo michi", "robot michi", "halo"]
SLEEP_WORDS = ["sleep", "tidur", "istirahat", "berhenti"]
SAD_WORDS = ["jelek", "bosan", "sedih", "murung"]
HAPPY_WORDS = ["keren", "bagus", "senang", "hebat"]
MAD_WORDS = ["ribut", "berantem", "marah", "kesal"]
DANCE_WORDS = ["menari", "dansa", "dance", "nari"]  # Added dance words

# MQTT Client Setup
mqtt_client = mqtt.Client()
audio_response_ready = False

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code "+str(rc))
    client.subscribe(MQTT_TOPIC_SUBSCRIBE)

def on_message(client, userdata, msg):
    global audio_response_ready
    payload = msg.payload.decode()
    print(f"Received MQTT message: {payload}")
    try:
        data = json.loads(payload)
        if data.get("response") == "talk":
            audio_response_ready = True
    except json.JSONDecodeError:
        pass

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

def detect_wake_word_fuzzy(text, threshold=85):
    text = text.lower()
    for wake in WAKE_WORDS:
        if fuzz.partial_ratio(wake, text) >= threshold:
            return True
    return False

def detect_sleep_word_fuzzy(text, threshold=85):
    text = text.lower()
    for sleep_word in SLEEP_WORDS:
        if fuzz.partial_ratio(sleep_word, text) >= threshold:
            return True
    return False

def detect_sad_word_fuzzy(text, threshold=85):
    text = text.lower()
    for sad_word in SAD_WORDS:
        if fuzz.partial_ratio(sad_word, text) >= threshold:
            return True
    return False

def detect_happy_word_fuzzy(text, threshold=85):
    text = text.lower()
    for happy_word in HAPPY_WORDS:
        if fuzz.partial_ratio(happy_word, text) >= threshold:
            return True
    return False

def detect_mad_word_fuzzy(text, threshold=85):
    text = text.lower()
    for mad_word in MAD_WORDS:
        if fuzz.partial_ratio(mad_word, text) >= threshold:
            return True
    return False

def detect_dance_word_fuzzy(text, threshold=85):  # Added dance word detection
    text = text.lower()
    for dance_word in DANCE_WORDS:
        if fuzz.partial_ratio(dance_word, text) >= threshold:
            return True
    return False

def send_mqtt_talk_command():
    message = {"response": "talk"}
    mqtt_client.publish(MQTT_TOPIC_PUBLISH, json.dumps(message))
    print("Sent MQTT talk command")

def send_mqtt_sleep_command():
    message = {"response": "sleep"}
    mqtt_client.publish(MQTT_TOPIC_PUBLISH, json.dumps(message))
    print("Sent MQTT sleep command")

def send_mqtt_sad_command():
    message = {"response": "sad"}
    mqtt_client.publish(MQTT_TOPIC_PUBLISH, json.dumps(message))
    print("Sent MQTT sad command")

def send_mqtt_happy_command():
    message = {"response": "happy"}
    mqtt_client.publish(MQTT_TOPIC_PUBLISH, json.dumps(message))
    print("Sent MQTT happy command")

def send_mqtt_mad_command():
    message = {"response": "mad"}
    mqtt_client.publish(MQTT_TOPIC_PUBLISH, json.dumps(message))
    print("Sent MQTT mad command")

def send_mqtt_dance_command():  # Added dance command
    message = {"response": "dance"}
    mqtt_client.publish(MQTT_TOPIC_PUBLISH, json.dumps(message))
    print("Sent MQTT dance command")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="michi_robot",
        port=3310
    )

@app.route('/detect_wakeword', methods=['POST'])
def detect_wakeword():
    wav_path = os.path.join(UPLOAD_FOLDER, 'wakeword_check.wav')

    with open(wav_path, 'wb') as f:
        f.write(request.data)

    try:
        with open(wav_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="id"
            )
        
        text = transcript.text
        print("Hasil transkripsi:", text)

        if detect_wake_word_fuzzy(text):
            return jsonify({"wakeword_detected": True})
        else:
            return jsonify({"wakeword_detected": False})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/process_input', methods=['POST'])
def upload():
    global audio_response_ready
    audio_response_ready = False

    wav_path = os.path.join(UPLOAD_FOLDER, 'received.wav')

    try:
        # Save the uploaded file
        with open(wav_path, 'wb') as f:
            f.write(request.data)

        # Transcribe audio
        with open(wav_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="id"
            )

        print("Transcription:", transcript.text)

        # Store transcript in MySQL with timestamp
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_query = "INSERT INTO transcripts (transcript, created_at) VALUES (%s, %s)"
        cursor.execute(insert_query, (transcript.text, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()

        # Check for sleep command
        if detect_sleep_word_fuzzy(transcript.text):
            send_mqtt_sleep_command()
            return jsonify({
                "status": "success",
                "transcription": transcript.text,
                "action": "sleep_command_sent"
            })

        # Check for sad command
        if detect_sad_word_fuzzy(transcript.text):
            send_mqtt_sad_command()
            return jsonify({
                "status": "success",
                "transcription": transcript.text,
                "action": "sad_command_sent"
            })

        # Check for happy command
        if detect_happy_word_fuzzy(transcript.text):
            send_mqtt_happy_command()
            return jsonify({
                "status": "success",
                "transcription": transcript.text,
                "action": "happy_command_sent"
            })

        # Check for mad command
        if detect_mad_word_fuzzy(transcript.text):
            send_mqtt_mad_command()
            return jsonify({
                "status": "success",
                "transcription": transcript.text,
                "action": "mad_command_sent"
            })

        # Check for dance command
        if detect_dance_word_fuzzy(transcript.text):  # Added dance command check
            send_mqtt_dance_command()
            return jsonify({
                "status": "success",
                "transcription": transcript.text,
                "action": "dance_command_sent"
            })

        # Generate response (simplified example)
        response_text = "Ini adalah respon dari Michi"
        response_audio_path = os.path.join(SERVER_AUDIO_FOLDER, "response.mp3")

        # Generate audio file (using TTS or pre-recorded)
        if not os.path.exists(response_audio_path):
            pass

        # Send talk command
        send_mqtt_talk_command()

        # Return immediate response with audio URL
        return jsonify({
            "status": "success",
            "transcription": transcript.text,
            "audio_url": "http://172.20.10.2:5000/audio_response"
        })

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/audio_response')
def audio_response():
    audio_path = os.path.join(SERVER_AUDIO_FOLDER, "conversation.mp3")
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/mpeg')
    else:
        return "Audio response not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)