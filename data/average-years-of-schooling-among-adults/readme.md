# Average years of schooling among adults - Data package

This data package contains the data that powers the chart ["Average years of schooling among adults"](https://ourworldindata.org/grapher/years-of-schooling?v=1&csvType=full&useColumnShortNames=false&metric_type=average_years_schooling&level=all&sex=both) on the Our World in Data website. It was downloaded on October 26, 2026.

### Active Filters

A filtered subset of the full data was downloaded. The following filters were applied:

## CSV structure

Each row is an observation for an entity (usually a country or region) at a timepoint.

- "Entity" — the name of the entity, e.g. "United States".
- "Code" — our internal entity code. For most countries this is the [ISO alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) code, e.g. "USA"; historical and other non-standard entities get a custom code.
- "Year" or "Day" — the timepoint. Annual data has a "Year" column holding an integer year; otherwise a "Day" column holds a date string in the form "YYYY-MM-DD".
- The final column is the data column — the time series that powers the chart. Downloaded with the "full data" option it corresponds to the time series below; with "only selected data visible in the chart" it is transformed depending on the chart type, so the correspondence may be less direct.


## Metadata.json structure

The .metadata.json file contains metadata about the data package. The "charts" key contains information to recreate the chart, like the title, subtitle etc. The "columns" key contains information about each of the columns in the csv, like the unit, timespan covered, citation for the data etc.

## How we process data at Our World in Data

Our World in Data is almost never the original producer of the data - almost all of the data we use has been compiled by others. If you want to re-use data, it is your responsibility to ensure that you adhere to the sources' license and to credit them correctly. Please note that a single time series may have more than one source - e.g. when we stitch together data from different time periods by different producers or when we calculate per capita metrics using population data from a second source.

Preparing this data involves several processing steps. Depending on the data, this can include standardizing country names and world region definitions, converting units, calculating derived indicators such as per capita measures, as well as adding or adapting metadata such as the name or the description given to an indicator.
[Read about our data pipeline](https://docs.owid.io/projects/etl/).

## Detailed information about the data


### Average years of schooling – UNDP
Average number of years (excluding years spent repeating individual grades) adults over 25 years participated in formal education.
Last updated: May 7, 2025  
Next expected update: November 2026  
Date range: 1990–2023  
Unit: years  
Source: UNDP, Human Development Report (2025) – with minor processing by Our World in Data  

#### How to cite this data

UNDP, Human Development Report (2025) – with minor processing by Our World in Data

#### What you should know about this data
- This indicator shows the average number of years that adults in a country have spent in formal education.
- It reflects the overall educational attainment of the population based on what they have already completed.
- The calculation converts each person's highest completed education level into years - for example, someone who finished high school counts as having roughly 12 years of schooling, while someone who never attended school counts as 0 years.
- The data comes from censuses and surveys of adults aged 25 and older, including only formal education starting from primary school.
- This indicator captures how much schooling adults have accumulated over their lifetimes, showing the results of past investments in education systems.
- Higher values indicate a population with stronger educational foundations, but the measure does not account for education quality or informal learning.
- The data may not reflect recent progress in countries with infrequent surveys or outdated census information.
- UNDP originally obtained this indicator from: Barro and Lee (2018), Eurostat (2024), ICF Macro Demographic and Health Surveys (various years), UNESCO Institute for Statistics (2024) and UNICEF Multiple Indicator Cluster Surveys (various years).


## Sources

These are the sources behind the data in this package. Each time series above names the ones it draws on in its citation.

### UNDP, Human Development Report – Human Development Report

Artificial intelligence (AI) has broken into a dizzying gallop. While AI feats grab headlines, they privilege technology in a make-believe vacuum, obscuring what really matters: people's choices.

The choices that people have and can realize, within ever expanding freedoms, are essential to human development, whose goal is for people to live lives they value and have reason to value. A world with AI is flush with choices the exercise of which is both a matter of human development and a means to advance it.

Going forward, development depends less on what AI can do—not on how human-like it is perceived to be—and more on mobilizing people's imaginations to reshape economies and societies to make the most of it. Instead of trying vainly to predict what will happen, the 2025's Human Development Report asks what choices can be made so that new development pathways for all countries dot the horizon, helping everyone have a shot at thriving in a world with AI.

For more details, refer to https://hdr.undp.org/data-center/documentation-and-downloads

Producer: UNDP, Human Development Report  
Published: 2025-05-06  
Retrieved on: 2025-05-07  
Retrieved from: https://hdr.undp.org/  
Direct download: https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv  
License: CC BY 3.0 IGO (https://hdr.undp.org/copyright-and-terms-use)  

Citation: UNDP (United Nations Development Programme). 2025. Human Development Report 2025: A matter of choice: People and possibilities in the age of AI. New York.

    