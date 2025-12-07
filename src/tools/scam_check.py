import whois
from urllib.parse import urlparse
from datetime import datetime
import tldextract
import re

def get_domain_age(text_input: str):
    """
    V2.0 - Abordare Robustă (Brute Force).
    Scanează fiecare cuvânt să vadă dacă e domeniu, ignorând Regex-urile complexe.
    """
    
    # 1. CURATAREA TEXTULUI
    # Eliminăm caractere invizibile și facem split
    clean_text = text_input.replace('\u200b', ' ').replace('\xa0', ' ')
    words = clean_text.split()
    
    found_domain_obj = None
    clean_domain_str = ""

    # 2. SCANAREA CUVINTELOR (Vânătoarea)
    for word in words:
        # Curățăm punctuația din jurul cuvântului (ex: "(google.com)" -> "google.com")
        candidate = word.strip(".,()[]{}<>\"'")
        
        # Dacă e email (ex: a@b.com), luăm doar partea de după @
        if "@" in candidate:
            parts = candidate.split("@")
            candidate = parts[-1] # b.com

        # Încercăm să extragem componentele
        extracted = tldextract.extract(candidate)
        
        # CRITERIUL DE VALIDARE:
        # Un domeniu e valid dacă are Nume (domain) ȘI Extensie (suffix)
        # Ex: "google" (fara .com) -> Invalid
        # Ex: "google.com" -> Valid (domain=google, suffix=com)
        if extracted.domain and extracted.suffix:
            found_domain_obj = extracted
            clean_domain_str = f"{extracted.domain}.{extracted.suffix}"
            break # Am găsit primul domeniu, ne oprim (de obicei primul e cel important)

    # Dacă după toată scanarea nu am găsit nimic
    if not found_domain_obj:
        return "SKIP: No valid domain found in text."

    # 3. VERIFICARE TYPOSQUATTING (Brand Safety)
    suspicious_typos = {
        "gogle": "google",
        "googl": "google",
        "amaz0n": "amazon",
        "paypa1": "paypal",
        "mircosoft": "microsoft",
        "faceboook": "facebook",
        "net-flix": "netflix",
        "careers-noreply": "google" # Caz special daca tldextract ia gresit subdomeniul
    }
    
    if found_domain_obj.domain in suspicious_typos:
        real_brand = suspicious_typos[found_domain_obj.domain]
        return f"CRITICAL: IMPOSTOR DOMAIN DETECTED! '{clean_domain_str}' is trying to impersonate '{real_brand}'. BLOCK IMMEDIATELY."

    # 4. VERIFICAREA WHOIS
    try:
        domain_info = whois.whois(clean_domain_str)
    except Exception as err:
        return f"WHOIS Error: Could not verify '{clean_domain_str}'. Reason: {str(err)}"
    
    date = domain_info.creation_date

    if not date:
        return f"SAFE (Assumption): Domain '{clean_domain_str}' is established (Hidden Date)."

    # Normalizare data
    if isinstance(date, list):
        data_initiala = date[0]
    else:
        data_initiala = date
    
    now_date = datetime.now()
    if data_initiala.tzinfo:
        data_initiala = data_initiala.replace(tzinfo=None)

    delta = now_date - data_initiala
    days_active = delta.days

    # 5. VERDICT FINAL
    if days_active < 30:
        return f"HIGH RISK: Domain '{clean_domain_str}' is FRESH! Created {days_active} days ago."
    elif days_active < 365:
        return f"WARNING: Domain '{clean_domain_str}' is new ({days_active} days old)."
    else:
        return f"SAFE: Domain '{clean_domain_str}' is established ({days_active} days old)."