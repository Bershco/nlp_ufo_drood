# UFO Top 20 Manual Review Helper

Use this after the automated scoring changes are finalized. The CSV version contains the full fields plus review prompts.

Checklist for each pair:

- Confirm whether both dates are event dates, not release or administrative dates.
- Compare location specificity and treat broad official locations cautiously.
- Compare shape, color, motion, witness type, aircraft/base/radar terms, and number of objects.
- Decide whether the PURSUE snippet is a single incident or a broad document collection.
- Edit `manual_label` and `manual_notes` in `ufo_manual_validation_completed.csv` if your judgment differs.

## Top 20

### Rank 1: Kaggle 1317 vs PURSUE 18_6369445_General_1948_Vol_1

- Automated label: `likely same event`
- Final score: `0.4982`
- Dates: Kaggle `nan` vs PURSUE `1948-06-15`
- Locations: Kaggle `white hall, ar, us [34.2739, -92.0908]` vs PURSUE `nan`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/18_6369445_general_1948_vol_1.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/18_6369445_General_1948_Vol_1.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; entity/keyword overlap is meaningful; score percentile 1.000; official date is missing or only inferred; official location was not usable

### Rank 2: Kaggle 69241 vs PURSUE 38_143685_box_Incident_Summaries_101-172

- Automated label: `likely same event`
- Final score: `0.4971`
- Dates: Kaggle `2003-08-24` vs PURSUE `nan`
- Locations: Kaggle `watchung, nj, us [40.6378, -74.4514]` vs PURSUE `nan`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/38_143685_box7_incident_summaries_101-172.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/38_143685_box7_Incident_Summaries_101-172.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; score percentile 0.998; official date is missing or only inferred; official location was not usable

### Rank 3: Kaggle 10290 vs PURSUE Western US Event

- Automated label: `likely same event`
- Final score: `0.4905`
- Dates: Kaggle `2012-11-17` vs PURSUE `2023`
- Locations: Kaggle `santa cruz, ca, us [36.9742, -122.0297]` vs PURSUE `Western United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/western_us_event_slides_5.08.2026.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Western_US_Event_Slides_5.08.2026.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.996; date support is weak

### Rank 4: Kaggle 61526 vs PURSUE Western US Event

- Automated label: `likely same event`
- Final score: `0.4834`
- Dates: Kaggle `2013-07-03` vs PURSUE `2023`
- Locations: Kaggle `walla walla, wa, us [46.0647, -118.3419]` vs PURSUE `Western United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/western_us_event_slides_5.08.2026.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Western_US_Event_Slides_5.08.2026.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.994; date support is weak

### Rank 5: Kaggle 39456 vs PURSUE Western US Event

- Automated label: `likely same event`
- Final score: `0.4808`
- Dates: Kaggle `2014-04-27` vs PURSUE `2023`
- Locations: Kaggle `deer park, wa, us [47.9544, -117.4758]` vs PURSUE `Western United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/western_us_event_slides_5.08.2026.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Western_US_Event_Slides_5.08.2026.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.992; date support is weak

### Rank 6: Kaggle 34137 vs PURSUE 38_143685_box_Incident_Summaries_101-172

- Automated label: `likely same event`
- Final score: `0.4769`
- Dates: Kaggle `1999-03-30` vs PURSUE `nan`
- Locations: Kaggle `pittsburgh, pa, us [40.4406, -79.9961]` vs PURSUE `nan`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/38_143685_box7_incident_summaries_101-172.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/38_143685_box7_Incident_Summaries_101-172.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; score percentile 0.990; official date is missing or only inferred; official location was not usable

### Rank 7: Kaggle 17562 vs PURSUE Western US Event

- Automated label: `likely same event`
- Final score: `0.4744`
- Dates: Kaggle `2011-01-21` vs PURSUE `2023`
- Locations: Kaggle `midland, tx, us [31.9972, -102.0775]` vs PURSUE `Western United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/western_us_event_slides_5.08.2026.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Western_US_Event_Slides_5.08.2026.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.988; date support is weak

### Rank 8: Kaggle 26533 vs PURSUE Western US Event

- Automated label: `likely same event`
- Final score: `0.4742`
- Dates: Kaggle `2014-02-14` vs PURSUE `2023`
- Locations: Kaggle `tucson, az, us [32.2217, -110.9258]` vs PURSUE `Western United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/western_us_event_slides_5.08.2026.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Western_US_Event_Slides_5.08.2026.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.986; date support is weak

### Rank 9: Kaggle 2771 vs PURSUE USPER Statement about UAP Sighting

- Automated label: `likely same event`
- Final score: `0.474`
- Dates: Kaggle `2005-10-18` vs PURSUE `nan`
- Locations: Kaggle `hillsboro, ky, us [38.2933, -83.6589]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/usper-statement-redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/USPER-Statement-Redacted.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location has broad geographic support; score percentile 0.984; official date is missing or only inferred

### Rank 10: Kaggle 18767 vs PURSUE FBI September 2023 Sighting - Serial 3

- Automated label: `likely same event`
- Final score: `0.4701`
- Dates: Kaggle `2013-12-17` vs PURSUE `2023-09-01`
- Locations: Kaggle `woodstock, ga, us [34.1014, -84.5194]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/serial 5 redacted_redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Serial 5 Redacted_Redacted.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location has broad geographic support; entity/keyword overlap is meaningful; score percentile 0.982; date support is weak

### Rank 11: Kaggle 31687 vs PURSUE 38_143685_box_Incident_Summaries_101-172

- Automated label: `likely same event`
- Final score: `0.4698`
- Dates: Kaggle `2006-03-15` vs PURSUE `nan`
- Locations: Kaggle `new britain, ct, us [41.6611, -72.7800]` vs PURSUE `nan`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/38_143685_box7_incident_summaries_101-172.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/38_143685_box7_Incident_Summaries_101-172.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; score percentile 0.980; official date is missing or only inferred; official location was not usable

### Rank 12: Kaggle 69389 vs PURSUE Western US Event

- Automated label: `likely same event`
- Final score: `0.4697`
- Dates: Kaggle `2013-08-24` vs PURSUE `2023`
- Locations: Kaggle `silverdale, wa, us [47.6447, -122.6936]` vs PURSUE `Western United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/western_us_event_slides_5.08.2026.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Western_US_Event_Slides_5.08.2026.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location is geographically compatible; score percentile 0.978; date support is weak

### Rank 13: Kaggle 19771 vs PURSUE USPER Statement about UAP Sighting

- Automated label: `likely same event`
- Final score: `0.4655`
- Dates: Kaggle `2012-01-22` vs PURSUE `nan`
- Locations: Kaggle `ocala, fl, us [29.1869, -82.1403]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/usper-statement-redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/USPER-Statement-Redacted.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location has broad geographic support; score percentile 0.976; official date is missing or only inferred

### Rank 14: Kaggle 55397 vs PURSUE FBI September 2023 Sighting - Serial 3

- Automated label: `likely same event`
- Final score: `0.4651`
- Dates: Kaggle `1999-07-01` vs PURSUE `2023-09-01`
- Locations: Kaggle `clover, sc, us [35.1111, -81.2267]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/serial 5 redacted_redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Serial 5 Redacted_Redacted.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; location has broad geographic support; entity/keyword overlap is meaningful; score percentile 0.974; date support is weak

### Rank 15: Kaggle 68270 vs PURSUE 38_143685_box_Incident_Summaries_101-172

- Automated label: `likely same event`
- Final score: `0.465`
- Dates: Kaggle `2000-08-21` vs PURSUE `nan`
- Locations: Kaggle `eatontown, nj, us [40.2961, -74.0514]` vs PURSUE `nan`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/38_143685_box7_incident_summaries_101-172.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/38_143685_box7_Incident_Summaries_101-172.pdf.txt`
- Automated reason: top 3% of exported candidates by final score; uses extracted official document text; score percentile 0.972; official date is missing or only inferred; official location was not usable

### Rank 16: Kaggle 78573 vs PURSUE FBI September 2023 Sighting - Serial 3

- Automated label: `possibly same event`
- Final score: `0.4645`
- Dates: Kaggle `1946-09-30` vs PURSUE `2023-09-01`
- Locations: Kaggle `dome, az, us [32.7553, -114.3614]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/serial 5 redacted_redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Serial 5 Redacted_Redacted.pdf.txt`
- Automated reason: next 32% of exported candidates by final score; uses extracted official document text; location has broad geographic support; entity/keyword overlap is meaningful; score percentile 0.970; date support is weak

### Rank 17: Kaggle 61511 vs PURSUE FBI September 2023 Sighting - Serial 3

- Automated label: `possibly same event`
- Final score: `0.4644`
- Dates: Kaggle `2013-07-03` vs PURSUE `2023-09-01`
- Locations: Kaggle `tumwater, wa, us [47.0075, -122.9081]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/serial 5 redacted_redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/Serial 5 Redacted_Redacted.pdf.txt`
- Automated reason: next 32% of exported candidates by final score; uses extracted official document text; location has broad geographic support; entity/keyword overlap is meaningful; score percentile 0.968; date support is weak

### Rank 18: Kaggle 31250 vs PURSUE USPER Statement about UAP Sighting

- Automated label: `possibly same event`
- Final score: `0.464`
- Dates: Kaggle `2013-03-13` vs PURSUE `nan`
- Locations: Kaggle `ellington, ct, us [41.9039, -72.4703]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/usper-statement-redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/USPER-Statement-Redacted.pdf.txt`
- Automated reason: next 32% of exported candidates by final score; uses extracted official document text; location has broad geographic support; score percentile 0.966; official date is missing or only inferred

### Rank 19: Kaggle 28128 vs PURSUE USPER Statement about UAP Sighting

- Automated label: `possibly same event`
- Final score: `0.4638`
- Dates: Kaggle `2014-02-22` vs PURSUE `nan`
- Locations: Kaggle `washington&#44 d.c., dc [38.9072, -77.0365]` vs PURSUE `United States`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/usper-statement-redacted.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/USPER-Statement-Redacted.pdf.txt`
- Automated reason: next 32% of exported candidates by final score; uses extracted official document text; location has broad geographic support; score percentile 0.964; official date is missing or only inferred

### Rank 20: Kaggle 45243 vs PURSUE 38_143685_box_Incident_Summaries_101-172

- Automated label: `possibly same event`
- Final score: `0.4635`
- Dates: Kaggle `2010-05-31` vs PURSUE `nan`
- Locations: Kaggle `thousand oaks, ca, us [34.1706, -118.8367]` vs PURSUE `nan`
- Source link/file: `https://www.war.gov/medialink/ufo/release_1/38_143685_box7_incident_summaries_101-172.pdf`
- Extracted text path: `data/manual_text/Release_1/Release_1/38_143685_box7_Incident_Summaries_101-172.pdf.txt`
- Automated reason: next 32% of exported candidates by final score; uses extracted official document text; score percentile 0.962; official date is missing or only inferred; official location was not usable