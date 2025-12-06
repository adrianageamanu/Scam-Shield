from langchain_community.tools import DuckDuckGoSearchRun

#instantiez search engine-ul
search_engine = DuckDuckGoSearchRun()

def searching(query):
    #la mesajul initial adaug cuvinte cheie pentru a trimite mai departe la search engine
    enhanced_q = query + " scam fraud review pareri cybercrimes vulnerable"

    try:
        #fac cautarea propriu-zisa pe DuckDuckGo
        text = search_engine.run(enhanced_q)
        return text
    except Exception as err:
        return f"Eroare la cautarea pe web: {str(err)}"