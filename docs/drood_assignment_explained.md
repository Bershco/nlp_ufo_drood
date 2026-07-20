# Edwin Drood Assignment: Requirements and Implementation

## Purpose

The assignment asks whether NLP can support a data-based theory about Dickens's unfinished mystery: who is most likely responsible for Edwin Drood's disappearance, whether Edwin was murdered, and which textual clues support competing explanations. It explicitly requires an evidence-based theory rather than certainty.

## What the assignment requires

1. Prepare the Gutenberg text by removing boilerplate and splitting it into chapters, paragraphs, and sentences.
2. Track nine main characters and analyze mentions, chapter presence, co-occurrence, nearby words, and positive, negative, dark, suspicious, emotional, or violent language.
3. Rank suspects using motive, opportunity, and suspicious language.
4. Use NLP to retrieve and cluster scenes, then present at least 8–10 important clues with chapter, quotation, characters, explanation, and supported theory.
5. Compare *Drood* with earlier Dickens novels across plot progression, character roles, themes, language patterns, and character-network structure, and explain whether the comparison supports a theory.
6. State a main theory, confidence, strongest clues, alternatives, and limitations.
7. Submit a Colab notebook, a 2–4 page report, at least three visualizations, ranked suspects, a clue table, and a Dickens comparison.

## How this repository answers it

- `drood_sentences.csv` contains the structured chapter/paragraph/sentence table and character mentions.
- Character frequency, chapter presence, paragraph co-occurrence, contextual words, sentiment, and suspicious-language outputs cover character analysis.
- `drood_suspect_scores.csv` reports every raw feature and four normalized score components. The model deliberately separates its numeric ranking from the final literary interpretation.
- Clues are retrieved using sentence embeddings across six theory queries. TF-IDF/K-means supplies scene clusters and diversity. The final 12-row table is audited against the source text so generic keyword matches are not treated as clues.
- The Dickens comparison includes all six works listed in the assignment: *Oliver Twist*, *Bleak House*, *David Copperfield*, *Great Expectations*, *Our Mutual Friend*, and *A Tale of Two Cities*. Outputs cover motif rates, ten-part sentiment arcs, opening/middle/ending motif progression, character-role patterns, and comparable co-occurrence-network statistics.
- The final interpretation distinguishes Neville's high surface-language score from Jasper's stronger cross-scene evidence chain.

## Main result

Neville Landless ranks first computationally because he is explicitly surrounded by jealousy, conflict, threat, proximity, and blood evidence. John Jasper ranks second, but the audited evidence points more coherently to Jasper: a secret opium life and imagined strangulation, advance crypt exploration and key access, obsessive love for Rosa, deception toward Edwin, rapid control of the murder narrative, and later reticence and isolation. The preferred theory therefore names Jasper as the strongest suspect and Neville as a likely false suspect. Confidence is medium. Jasper probably attempted to kill Edwin, while survival and a Datchery-related disguise remain plausible because the novel contains no body, confession, or ending.

## What the analysis cannot prove

The score measures textual association, not guilt. Embeddings retrieve semantically related passages but do not understand authorial intention. Cross-novel measures are proxies across works of different lengths and structures. Most importantly, Dickens died before writing the resolution.
