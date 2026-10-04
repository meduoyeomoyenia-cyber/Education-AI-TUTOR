"""Phase 7 media: R2 presigned (boto3 when configured, stub dev), voice optional stubs, image-help, KB logging."""
import os, time
R2_BUCKET = os.getenv("R2_BUCKET", "edu-tutor-dev")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
KB_LOG = []

def presign(filename: str, content_type: str):
    key = f"uploads/{int(time.time())}_{filename}"
    if os.getenv("R2_ACCOUNT_ID"):
        import boto3
        s3 = boto3.client("s3", endpoint_url=R2_ENDPOINT or None)
        url = s3.generate_presigned_url("put_object", Params={"Bucket": R2_BUCKET, "Key": key, "ContentType": content_type}, ExpiresIn=600)
        return {"bucket": R2_BUCKET, "key": key, "url": url}
    return {"bucket": R2_BUCKET, "key": key, "url": f"https://r2.example/{R2_BUCKET}/{key}?presigned=1"}

def transcribe_stub(lang: str) -> str:
    return {"en": "spoken question text", "pcm": "wetin you ask?", "yo": "ìbéèrè", "ha": "tambaya", "ig": "ajụjụ"}.get(lang, "spoken question text")

def speak_stub(text: str) -> dict:
    return {"audio_url": f"https://r2.example/{R2_BUCKET}/tts/{abs(hash(text)) % 99999}.mp3", "bitrate": "48kbps", "note": "Data Saver capped"}

def image_help_stub(caption: str, topic: str | None) -> str:
    return (f"Step 1: read what is asked ({caption[:80]}). Step 2: recall {(topic or 'the topic')} method. "
            "Step 3: try first step yourself. Academic terms stay in English.")

def log_kb(session: str, kb: int, media: str):
    KB_LOG.append({"session": session, "kb": kb, "media": media})
    return {"session": session, "total_kb": sum(x["kb"] for x in KB_LOG if x["session"] == session)}
