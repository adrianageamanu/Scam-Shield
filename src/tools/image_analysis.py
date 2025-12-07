def analyze_image(user_input: str) -> dict:
    """
    Analizează input-ul pentru a determina sursa imaginii (URL sau Upload)
    și oferă indicii despre metadata (simulat pentru hackathon).
    """
    
    # CAZUL 1: Imagine Încărcată (Base64)
    # Streamlit trimite: "Analizează vizual Base64: ..."
    if "Base64:" in user_input:
        return {
            "status": "Uploaded Image Detected",
            "source": "Direct Upload",
            # Notă: Upload-urile prin browser șterg adesea metadata, deci avertizăm AI-ul
            "metadata_heuristic": "EXIF Data stripped by upload process. Rely strictly on Visual Artifacts (Visual Inspection)."
        }

    # CAZUL 2: Link Web (URL)
    elif "http" in user_input.lower():
        # Încercăm să extragem URL-ul (ultimul cuvânt din text)
        words = user_input.split()
        image_url = next((w for w in words if "http" in w), None)
        
        if image_url:
            # Heuristică simplă: Link-urile lungi/complexe de la Google/FB sunt adesea legitime (CDN)
            # Link-urile scurte sau ciudate pot fi suspecte
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
    
    # CAZUL 3: Nimic găsit
    return {
        "status": "No image data found", 
        "url": None, 
        "metadata_heuristic": "No data available."
    }