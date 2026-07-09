# Edwin Drood NLP Report

Main theory: `Neville Landless` is the strongest computational suspect in this scoring model.
Confidence: medium-low. The novel is unfinished, and the scores are evidence aids rather than proof.

## Ranked Suspects
| suspect          |   motive_score |   opportunity_score |   suspicious_language_score |   suspicion_score |
|:-----------------|---------------:|--------------------:|----------------------------:|------------------:|
| Neville Landless |          0.294 |              16.923 |                       0.196 |            17.413 |
| John Jasper      |          0.088 |              15.462 |                       0.22  |            15.769 |
| Rosa Bud         |          0.133 |              14.923 |                       0.114 |            15.169 |
| Mr. Crisparkle   |          0.057 |              12.462 |                       0.143 |            12.662 |
| Helena Landless  |          0.113 |               8.154 |                       0.225 |             8.492 |
| Durdles          |          0     |               1.538 |                       0.157 |             1.696 |
| Dick Datchery    |          0     |               0.769 |                       0.129 |             0.898 |
| Princess Puffer  |          0     |               0.769 |                       0     |             0.769 |

## Important Clues
|   chapter | quote                                                                                                                                                                                                                                                                                                                                                          | characters_involved                        | why_important                           | supports_suspect   |
|----------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------|:----------------------------------------|:-------------------|
|        20 | Jasper’s self-absorption in his nephew when he was alive, and his unceasing pursuit of the inquiry how he came by his death, if he were dead, were themes so rife in the place, that no one appeared able to suspect the possibility of foul play at his hands.                                                                                                | John Jasper                                | Contains motif terms: dead, death       | John Jasper        |
|        16 | “I fear I have alarmed you?” Jasper apologised faintly, when he was helped into his easy-chair.                                                                                                                                                                                                                                                                | John Jasper                                | Contains motif terms: fear, fear        | John Jasper        |
|         8 | “You need have no fear for me, Jasper,” returns Mr.                                                                                                                                                                                                                                                                                                            | John Jasper                                | Contains motif terms: fear, fear        | John Jasper        |
|         2 | Jasper lifts his dark eyebrows inquiringly.                                                                                                                                                                                                                                                                                                                    | John Jasper                                | Contains motif terms: dark              | John Jasper        |
|        19 | She is so conscious of his looking at her with a gloating admiration of the touch of anger on her, and the fire and animation it brings with it, that even as her spirit rises, it falls again, and she struggles with a sense of shame, affront, and fear, much as she did that night at the piano.                                                           |                                            | Contains motif terms: fear, anger, fear |                    |
|         2 | “Anyhow, my dear Ned,” Jasper resumes, as he shakes his head with a grave cheerfulness, “I must subdue myself to my vocation: which is much the same thing outwardly.                                                                                                                                                                                          | John Jasper                                | Contains motif terms: grave             | John Jasper        |
|         5 | “Hold your hand,” cries Jasper, “and don’t throw while I stand so near him, or I’ll kill you!                                                                                                                                                                                                                                                                  | John Jasper                                | Contains motif terms: kill              | John Jasper        |
|        22 | Lobley mopped, and, arranging cushions, stretchers, and the like, danced the tight-rope the whole length of the boat like a man to whom shoes were a superstition and stockings slavery; and then came the sweet return among delicious odours of limes in bloom, and musical ripplings; and, all too soon, the great black city cast its shadow on the waters |                                            | Contains motif terms: dark, death       |                    |
|         8 | This insulting allusion to his dark skin infuriates Neville to that violent degree, that he flings the dregs of his wine at Edwin Drood, and is in the act of flinging the goblet after it, when his arm is caught in the nick of time by Jasper.                                                                                                              | Edwin Drood; John Jasper; Neville Landless | Contains motif terms: dark              | John Jasper        |
|         8 | When he first emerges into the night air, nothing around him is still or steady; nothing around him shows like what it is; he only knows that he stands with a bare head in the midst of a blood-red whirl, waiting to be struggled with, and to struggle to the death.                                                                                        |                                            | Contains motif terms: blood, death      |                    |
|        12 | Is that baby-devil on the watch there!” cries Jasper in a fury: so quickly roused, and so violent, that he seems an older devil himself. “I shall shed the blood of that impish wretch!                                                                                                                                                                        | John Jasper                                | Contains motif terms: blood             | John Jasper        |
|         8 | There is something of the tiger in his dark blood.”                                                                                                                                                                                                                                                                                                            |                                            | Contains motif terms: blood, dark       |                    |

## Dickens Comparison
| motif    |   drood_rate_per_1000 |   great_expectations_rate_per_1000 |
|:---------|----------------------:|-----------------------------------:|
| secrecy  |                 0.359 |                              0.386 |
| crime    |                 0.348 |                              0.67  |
| emotion  |                 1.177 |                              1.005 |
| identity |                 1.682 |                              1.589 |

## Limitations
- Alias matching can over-count common first names.
- Sentiment/theme scoring uses transparent lexicons, not a trained literary model.
- Dickens left the mystery unfinished, so the output supports a theory rather than proving one.