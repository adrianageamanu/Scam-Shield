def analyze_image(user_input: str) -> dict:
    
    if "Base64:" in user_input:
        return {
            "status": "Uploaded Image Detected",
            "source": "Direct Upload",
            "metadata_heuristic": "EXIF Data stripped by upload process. Rely strictly on Visual Artifacts (Visual Inspection)."
        }

    elif "http" in user_input.lower():
        words = user_input.split()
        image_url = next((w for w in words if "http" in w), None)
        
        if image_url:
            metadata_status = "Unknown Source. Check for compression artifacts."
            
            if "googleusercontent" in image_url or "fbcdn" in image_url:
                metadata_status = "Hosted on Trusted CDN (Neutral Metadata)."
            elif ".ru/" in image_url or ".xyz/" in image_url:
                metadata_status = "High Risk Hosting Detected."

            return {
                "status": "Image URL Extracted",
                "url": image_url,
                "metadata_heuristic": metadata_status
            }
    
    return {
        "status": "No image data found", 
        "url": None, 
        "metadata_heuristic": "No data available."
    }