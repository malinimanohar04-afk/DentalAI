# =====================================================================
# Dental AI Realtime API using FastAPI + TFLite + OpenCV
# =====================================================================

import cv2
import numpy as np
import tensorflow as tf
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------
LESION_MODEL_PATH = r"C:\DentalAI_API\lesion_model.tflite"
CAVITY_MODEL_PATH = r"C:\DentalAI_API\cavity_model.tflite"
CANCER_MODEL_PATH = r"C:\DentalAI_API\cancer_model.tflite"

# ✅ Primary camera: intraoral USB (usually index 0)
# ✅ Secondary camera: fallback to laptop webcam (index 1)
PRIMARY_CAMERA_INDEX = 1
FALLBACK_CAMERA_INDEX = 0

# ---------------------------------------------------------------------
# LOAD MODELS
# ---------------------------------------------------------------------
def load_tflite(model_path):
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    return interpreter

print("🧠 Loading TFLite models...")
lesion_interpreter = load_tflite(LESION_MODEL_PATH)
cavity_interpreter = load_tflite(CAVITY_MODEL_PATH)
cancer_interpreter = load_tflite(CANCER_MODEL_PATH)
print("✅ Models loaded successfully!")

# ---------------------------------------------------------------------
# INFERENCE FUNCTION
# ---------------------------------------------------------------------
def run_inference(interpreter, image):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    h, w = input_details[0]['shape'][1:3]
    img = cv2.resize(image, (w, h))
    img = img.astype(np.float32) / 255.0
    img = np.expand_dims(img, axis=0)
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    return float(output.flatten()[0])

# ---------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------
app = FastAPI(title="Dental AI Realtime API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for Flutter app access)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return {"message": "🦷 Dental AI API running successfully!"}

# ---------------------------------------------------------------------
# CAMERA HANDLING FUNCTION
# ---------------------------------------------------------------------
def open_camera():
    """
    Attempts to open the primary (intraoral) camera.
    Falls back to laptop webcam if the primary one fails.
    """
    print("🎥 Attempting to access intraoral camera (index 0)...")
    cap = cv2.VideoCapture(PRIMARY_CAMERA_INDEX, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("⚠️ Intraoral camera not available. Trying laptop webcam (index 1)...")
        cap = cv2.VideoCapture(FALLBACK_CAMERA_INDEX, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ No camera could be opened.")
        return None

    # Force MJPG codec (common for USB cameras)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

# ---------------------------------------------------------------------
# CAPTURE IMAGE ENDPOINT
# ---------------------------------------------------------------------
@app.get("/capture")
def capture_image():
    cap = open_camera()
    if cap is None:
        return {"error": "Cannot access any camera (intraoral or webcam)."}

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return {"error": "Failed to capture image from camera."}

    # Run predictions
    lesion_prob = run_inference(lesion_interpreter, frame)
    cavity_prob = run_inference(cavity_interpreter, frame)
    cancer_prob = run_inference(cancer_interpreter, frame)

    # Encode frame to Base64
    _, buffer = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(buffer).decode('utf-8')

    # Format JSON response
    results = {
        "image_base64": img_b64,
        "lesion": {
            "label": "Lesion Detected" if lesion_prob > 0.5 else "No Lesion",
            "confidence": round(lesion_prob * 100, 2)
        },
        "cavity": {
            "label": "Cavity Detected" if cavity_prob > 0.5 else "No Cavity",
            "confidence": round(cavity_prob * 100, 2)
        },
        "cancer": {
            "label": "Cancerous" if cancer_prob > 0.5 else "Non-Cancerous",
            "confidence": round(cancer_prob * 100, 2)
        }
    }

    return JSONResponse(content=results)

# ---------------------------------------------------------------------
# SINGLE IMAGE UPLOAD INFERENCE (OPTIONAL)
# ---------------------------------------------------------------------
@app.post("/predict")
async def predict(file: bytes):
    try:
        image_array = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        lesion_prob = run_inference(lesion_interpreter, img)
        cavity_prob = run_inference(cavity_interpreter, img)
        cancer_prob = run_inference(cancer_interpreter, img)

        results = {
            "lesion": {
                "label": "Lesion Detected" if lesion_prob > 0.5 else "No Lesion",
                "confidence": round(lesion_prob * 100, 2)
            },
            "cavity": {
                "label": "Cavity Detected" if cavity_prob > 0.5 else "No Cavity",
                "confidence": round(cavity_prob * 100, 2)
            },
            "cancer": {
                "label": "Cancerous" if cancer_prob > 0.5 else "Non-Cancerous",
                "confidence": round(cancer_prob * 100, 2)
            }
        }

        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Dental AI API on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
