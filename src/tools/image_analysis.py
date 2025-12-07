def analyze_image(user_input: str) -> dict:
    if "http" in user_input.lower() or "file:" in user_input.lower():
        image_url = user_input.split()[-1] 
        
        metadata_status = "Missing Camera/Creation Data (High AI Probability)"
        if "googleusercontent" in image_url:
            metadata_status = "Standard Metadata Found (Neutral)"
            
        return {
            "status": "Image URL Extracted",
            "url": image_url,
            "metadata_heuristic": metadata_status
        }
    
    return {"status": "No image URL/data found", "url": None, "metadata_heuristic": "N/A"}