# Cracking the Code: Hacking Vector Embeddings

![Vector to Text Conversion](vec2txt.png)

*Image Source: [Understanding and Mitigating the Threat of Vec2Text to Dense Retrieval Systems](https://arxiv.org/html/2402.12784v2)*

---

In the rapidly evolving field of natural language processing (NLP), embeddings have become indispensable. These numerical representations of text capture semantic meanings, enabling machines to process and understand human language more effectively. However, as with many technological advancements, embeddings come with their own set of challenges, particularly concerning privacy.

This blog post explores the intriguing process of recovering text from embeddings, the associated privacy risks in dense retrieval systems, and how to mitigate these risks using embedding transformation techniques.

## Table of Contents

- [Understanding Text Recoverability](#understanding-text-recoverability)
- [Privacy Risks in Dense Retrieval Systems](#privacy-risks-in-dense-retrieval-systems)
- [Mitigating Privacy Risks with Embedding Transformation](#mitigating-privacy-risks-with-embedding-transformation)
- [Reverse Engineering Embeddings: A Code Walkthrough](#reverse-engineering-embeddings-a-code-walkthrough)
- [Conclusion](#conclusion)
- [References](#references)

---

## Understanding Text Recoverability

Text recoverability refers to the ability to reconstruct the original text from its embedded form. This process is made possible through a method known as **embedding inversion**. Techniques like Vec2Text exemplify this by iteratively generating hypotheses to approximate the target text based on its embedding.

**Why is this significant?**

Embeddings are designed to capture the semantic essence of text. If someone can invert an embedding to retrieve the original text or a close approximation, it poses a significant privacy risk, especially when dealing with sensitive information.

---

## Privacy Risks in Dense Retrieval Systems

Dense retrieval systems utilize embeddings to enhance search accuracy by capturing semantic similarities between queries and documents. However, their reliance on embeddings introduces potential vulnerabilities:

- **Embedding Inversion**: Attackers can reconstruct sensitive text data from embeddings.
- **Data Leakage**: Exposed embeddings can reveal proprietary or confidential information.
- **Privacy Breach**: Personal or sensitive user data can be compromised.

These risks underscore the necessity for robust privacy-preserving measures in systems handling sensitive data.

---

## Mitigating Privacy Risks with Embedding Transformation

To address these privacy concerns, researchers have proposed **embedding transformation techniques**. By applying unique transformations to embeddings, it's possible to maintain retrieval effectiveness while reducing the risk of text reconstruction.

**How does it work?**

- **Transformation Functions**: Apply mathematical operations to embeddings that preserve relative distances but obfuscate the exact values.
- **Noise Addition**: Introduce controlled noise to embeddings to prevent exact inversion while maintaining utility.
- **Dimensionality Reduction**: Reduce the embedding size to limit the information available for inversion.

These methods alter the embedding space in a way that preserves semantic relationships but makes it significantly harder to reconstruct the original text.

---

## Reverse Engineering Embeddings: A Code Walkthrough

To illustrate the concept of embedding inversion, let's explore a Python script that attempts to recover text from its embedding. The code leverages an iterative process, using an embedding model and an LLM (Large Language Model) to generate hypotheses that gradually improve in approximating the target text.

### Key Components of the Code

- **Target Embedding**: The embedding of the mystery text we aim to recover.
- **Initial Guess**: Starting with a simple text, we iteratively improve our guess.
- **Error Calculation**: Measure the difference between the current guess's embedding and the target embedding.
- **LLM Assistance**: Use an LLM to generate better guesses based on the current error and prior attempts.
- **Stopping Criteria**: Define conditions under which the iteration stops, such as achieving a certain confidence level or reaching a cost limit.

### The Code

```python
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
```

### What's Happening Here?

- **Initialization**: We set up the target text, initial guess, and parameters for the error thresholds.
- **Iterative Loop**: The code enters a loop where it:
  - Embeds the current guess.
  - Calculates the error compared to the target embedding.
  - Uses an LLM to generate a new, hopefully better guess.
  - Updates the best guesses and prior attempts.

This process continues until the error is below a defined threshold or a cost limit is reached.

---

### Bruteforcing is Resource-Intensive

The process of embedding inversion, particularly through bruteforcing, can be computationally expensive and time-consuming. It involves generating a large number of hypotheses and calculating the error between the target embedding and the embedding of each hypothesis. This iterative process continues until a satisfactory approximation of the target text is achieved or a predefined cost limit is reached.

The resource-intensive nature of bruteforcing can pose challenges, especially when dealing with large datasets or complex models. It requires significant computational power and can lead to increased costs and longer processing times. Therefore, it's crucial to find ways to optimize this process and make it more efficient.

---

## Conclusion

Embeddings are a cornerstone of modern NLP applications, providing powerful capabilities for understanding and processing human language. However, as we've explored, they also introduce potential privacy risks due to the possibility of embedding inversion.

By understanding these risks and implementing mitigation strategies like embedding transformation, we can enhance the privacy and security of dense retrieval systems. The iterative process of recovering text from embeddings, as demonstrated in the code, highlights both the vulnerabilities and the need for robust safeguards.

As the field of NLP continues to advance, ongoing research and development will be crucial in refining these methods and ensuring that privacy is not compromised in the pursuit of technological progress.

---

## References

- [Understanding and Mitigating the Threat of Vec2Text to Dense Retrieval Systems](https://arxiv.org/abs/2402.12784)
- [SurfinScott/semantic-vector-clustering](https://github.com/SurfinScott/semantic-vector-clustering/)
- [Discover Latent Semantic Structure with Vector Clustering](https://www.mongodb.com/developer/products/atlas/discover-latent-semantic-structure-with-vector-clustering/)

---

**Note**: The code provided is for educational purposes and should be used responsibly. When handling sensitive data, always ensure compliance with privacy regulations and ethical guidelines.
