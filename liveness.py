@app.post("/liveness_check")
async def liveness_check(file: UploadFile = File(...)):
    data = await file.read()
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img_np = np.array(img)

        # --- Option A: Use InsightFace SCRFD + FaceQuality ---
        face_app = get_face_app()
        faces = face_app.get(img_np)

        if not faces:
            raise HTTPException(status_code=400, detail="No face detected")

        # Simple heuristic (can be replaced with deep anti-spoofing model)
        face = faces[0]
        liveness_score = face.det_score  # detection confidence
        quality_score = face.det_score   # you can also check face.pose / bbox

        is_live = liveness_score > 0.5  # threshold tuning required

        return {
            "live": bool(is_live),
            "liveness_score": float(liveness_score),
            "quality_score": float(quality_score)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Liveness check failed: {e}")
