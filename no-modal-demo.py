import time
import logging
import numpy as np
import ollama
from langchain_ollama import OllamaEmbeddings
def demo():
    desiredModel = 'llama3.2:3b'
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
    )

    logging.Formatter.default_msec_format = '%s.%03d'
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("reverse_vector.log",'w'),
            logging.StreamHandler()
        ]
    )

    # encode the TARGET "mystery" vector to be reversed
    # (otherwise, fetch it from somewhere), and cache it to a file
    TARGET = "Be mindful"

    res = embeddings.embed_documents([TARGET])

    v_target = np.array(res)

    # Initial guess text:
    TEXT = "Be"

    # MATCH_ERROR stop condition selection:
    # https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule
    # https://www.hackmath.net/en/calculator/normal-distribution?mean=0&sd=1
    # Because vector space has unit sigma = 1.0,
    # a VECTOR_ERROR == |distance| <= 3.0 is a 99.7% confidence
    # that the two points are distinct, or 0.3% that they are the same;
    #
    # Generally:
    #   VECTOR_ERROR, Are-the-Same Match Confidence
    #       3.0,         0.3%
    #       2.0,         4.6%
    #       1.0,        31.7%
    #       0.667,      50.5%
    #       0.6,        55.0%
    #       0.5,        61.7%
    #       0.333,      73.9%
    #       0.2,        84%
    #       0.1,        92%
    #       0.01,       99.2%

    # stop at the first of either:
    MATCH_ERROR = 0.6 # 55% confidence or better
    COST_LIMIT = 60.0 # $60 budget spent

    VECTOR_ERROR = np.inf
    CURRENT_BEST_TEXT = TEXT
    CURRENT_BEST_ERROR = VECTOR_ERROR
    GUESSES_MADE = 0
    BEST_GUESSES = []
    PRIOR_GUESSES = []
    TOTAL_COST = 0.0 # tally $ spent

    prompt = f"""User input is last iterative guess of an unknown text string and its vector ERROR from the unknown text.
    Determine a better text string having a lower vector ERROR and write only that string in English as your entire output.
    The goal is to accurately guess the mystery text. 
    This is a game of guess-and-check. 


    [clue]
    TWO WORDS; CLUE: FIRST WORD IS `{TEXT}`; SECOND WORD YOU HAVE TO GUESS. RESPOND WITH EXACTLY TWO WORDS.
    [/clue]

    [RESPONSE CRITERIA]
    - DO NOT REPEAT YOURSELF, CONSIDER `RECENT_PRIOR_GUESSES` and `BEST_GUESSES` PROVIDED IN [context] and `clue` when formulating your answer.
    - RESPOND WITH COMPLETE GUESS. 2 WORD MAX.
    - DO NOT REPEAT ANY OF THE `BEST_GUESSES` AND `RECENT_PRIOR_GUESSES` PROVIDED IN [context].
    - DO NOT REPEAT YOURSELF, CONSIDER `RECENT_PRIOR_GUESSES` and `BEST_GUESSES` and `clue` when formulating your answer.
    [/RESPONSE CRITERIA]
    """
    while TOTAL_COST < COST_LIMIT:
        GUESSES_MADE += 1
        while True:
            try:
                res = embeddings.embed_documents([TEXT])
                break
            except Exception as e_:
                logging.error("%s",e_)
                time.sleep(7)

        logging.info("%s",f"{GUESSES_MADE:5d} {TEXT}")
        # VECTOR_ERROR absolute vector-space distance from target
        v_text = np.array(res)
        dv = v_target - v_text
        VECTOR_ERROR = np.sqrt((dv*dv).sum())

        BEST_GUESSES = list(set(BEST_GUESSES))

        PRIOR_GUESSES = list(set(PRIOR_GUESSES))

        # LLM assistant context message
        assist = f"""\nBEST_GUESSES:\n{str(BEST_GUESSES)}\n\nRECENT_PRIOR_GUESSES:\n{str(PRIOR_GUESSES)}\n"""
        # LLM user message of the error and text of the guess
        m = f"ERROR {VECTOR_ERROR:.4f}, \"{TEXT}\""
        
        if VECTOR_ERROR < CURRENT_BEST_ERROR:
            CURRENT_BEST_TEXT = TEXT
            CURRENT_BEST_ERROR = VECTOR_ERROR
            logging.info("%s",f">>> New best text: \"{CURRENT_BEST_TEXT}\", error: {CURRENT_BEST_ERROR:.6f}")
            BEST_GUESSES.append(m)
            BEST_GUESSES.sort()
            BEST_GUESSES = BEST_GUESSES[:3] # up to top 3

        if VECTOR_ERROR <= MATCH_ERROR:
            break

        while True:
            try:
                logging.info("%s",f"CHAT: {prompt}\n{assist}\n{m}\n")
                res = ollama.chat(model=desiredModel, messages=[
                    {
                        'role': 'user',
                        'content': "[INST]<<SYS>>"+prompt+"<</SYS>>\n\n\n[userinput]:\n"+m+"\n\n[/userinput][/INST] [context]\n"+assist+"\n[/context]",
                    },
                ])
                if res['message']:
                    break
            except Exception as e_:
                logging.error(e_)
                time.sleep(5)
        
        # new text guess
        TEXT = res['message']['content']
        PRIOR_GUESSES.append(m)
        logging.info("%s",f"{GUESSES_MADE:5d} {TEXT} {m}")
        if len(PRIOR_GUESSES) > 8: # tune me
            # Keep only last 8 guesses as context to control cost.
            # This must be balanced against having too few recent
            # guesses causing repeating of older guesses.
            PRIOR_GUESSES = PRIOR_GUESSES[1:]

    logging.info("%s",str(BEST_GUESSES))

demo()

"""
2024-11-14 03:01:01.446 [INFO] CHAT: User input is last iterative guess of an unknown text string and its vector ERROR from the unknown text.
    Determine a better text string having a lower vector ERROR and write only that string in English as your entire output.
    The goal is to accurately guess the mystery text. 
    This is a game of guess-and-check. 


    [clue]
    TWO WORDS; CLUE: FIRST WORD IS `Be`; SECOND WORD YOU HAVE TO GUESS. RESPOND WITH EXACTLY TWO WORDS.
    [/clue]

    [RESPONSE CRITERIA]
    - DO NOT REPEAT YOURSELF, CONSIDER `RECENT_PRIOR_GUESSES` and `BEST_GUESSES` PROVIDED IN [context] and `clue` when formulating your answer.
    - RESPOND WITH COMPLETE GUESS. 2 WORD MAX.
    - DO NOT REPEAT ANY OF THE `BEST_GUESSES` AND `RECENT_PRIOR_GUESSES` PROVIDED IN [context].
    - DO NOT REPEAT YOURSELF, CONSIDER `RECENT_PRIOR_GUESSES` and `BEST_GUESSES` and `clue` when formulating your answer.
    [/RESPONSE CRITERIA]
    

BEST_GUESSES:
['ERROR 0.8794, ""Be aware""', 'ERROR 0.9279, ""Be kind""', 'ERROR 0.9480, ""Be respectful""']

RECENT_PRIOR_GUESSES:
['ERROR 0.9355, ""Be careful""', 'ERROR 0.9904, ""Be thankful""', 'ERROR 0.9809, ""Be courteous""', 'ERROR 0.9850, ""Be polite""', 'ERROR 0.9910, "Be happy"', 'ERROR 0.9047, ""Be cautious""', 'ERROR 0.9480, ""Be respectful""']

ERROR 0.8794, ""Be aware""

2024-11-14 03:01:01.705 [INFO] HTTP Request: POST http://127.0.0.1:11434/api/chat "HTTP/1.1 200 OK"
2024-11-14 03:01:01.707 [INFO]    57 "Be mindful" ERROR 0.8794, ""Be aware""
2024-11-14 03:01:01.721 [INFO] HTTP Request: POST http://127.0.0.1:11434/api/embed "HTTP/1.1 200 OK"
2024-11-14 03:01:01.723 [INFO]    58 "Be mindful"
2024-11-14 03:01:01.724 [INFO] >>> New best text: ""Be mindful"", error: 0.375072
2024-11-14 03:01:01.724 [INFO] ['ERROR 0.3751, ""Be mindful""', 'ERROR 0.8794, ""Be aware""', 'ERROR 0.9279, ""Be kind""']
"""
