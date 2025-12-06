#dictionare de cuvinte "periculoase"
urgency_keywords = ["urgent", "imediat", "acum", "blocat", "politie", "suspendat",
                    "restrictionat", "expira", "24 de ore", "arest", "mandat", "autoritati",
                    "actioneaza", "immediately", "suspended", "restricted", "blocked", 
                    "expires", "24 hours", "police", "arrest", "warrant",]

financial_keywords = ["password", "credit card", "banking", "verify account", "cvv", 
                      "pin", "social security", "crypto", "bitcoin", "wallet", "inheritance",
                      "parola", "card", "bancar", "verifica cont", "codul", 
                      "cnp", "buletin", "castigat", "mostenire", "transfer"]

def analyze_text(text: str):
    #fac tot textul in lower case pentru simplitate
    processed_text = text.lower()
    score = 0
    found_flags = []

    #caut in text cuvintele din dictionare si adaug la scorul final in functie de gravitate
    for keyword in urgency_keywords:
        if (keyword in processed_text):
            score += 20
            if keyword not in found_flags:
                found_flags.append(keyword)
    for keyword in financial_keywords:
        if (keyword in processed_text):
            score += 30
            if keyword not in found_flags:
                found_flags.append(keyword)
    
    #rezultatul il trunchiez la 100
    final = min(score, 100)
    risk_level = ""

    #in functie de scor, determin un factor de risc
    if (final < 30):
        risk_level = "LOW"
    elif (final >= 30 and final <= 65):
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
    
    rezultat = {
        "score" : final,
        "risk level" : risk_level,
        "risky words found" : found_flags
    }
    return rezultat