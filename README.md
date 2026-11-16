# SpaceApps_AstroRatas
AstroRatas | Dancing with the SARs
NASA Space Apps Challenge · Río Quito, Chocó, Colombia

How can we use satellite radar to identify areas where deforestation has occurred? AstroRatas explores this question using observations from the NISAR mission and an interactive prototype to present the results.

View the app on Streamlit

Study area
The analysis focuses on Río Quito in the Colombian department of Chocó. Frequent cloud cover makes it difficult to monitor the area with optical imagery. Radar observations allow us to compare the land surface through clouds and investigate changes near the river channel and in vegetation cover.

Data and methodology
We used NISAR GCOV scenes acquired on different dates in HH and HV polarizations.
We processed the data with Python and GDAL and worked with GeoTIFF layers.
We compared the radar signal across acquisition dates and looked for persistent decreases in HV backscatter.
We grouped the detected pixels into patches and estimated the area for each change class. When interpreting the patches, we considered the potential influence of the river channel, flooding, and moisture.
Preliminary results
The analysis produced maps comparing multiple dates, a map of detected patches, and a summary of area by change class. A persistent decrease in HV backscatter can be consistent with changes in vegetation structure. Mining is one possible explanation in some areas. Testing that hypothesis requires independent imagery, activity records, or field observations. We report the detected extent as area showing signs of change.

Application status
The Streamlit app includes an interactive map, a panel with information by sector, and a before-and-after comparison tool. The published version uses illustrative images and figures. The data team has produced the Río Quito maps, and integration of the NISAR scenes and calculated metrics into the app is pending.

Use of artificial intelligence
We used generative AI to help structure the documentation and communicate our methodology and results. We generated the maps and area estimates by processing the NISAR observations. The team is responsible for reviewing and validating the interpretation presented here.

Credits
Developed by AstroRatas for the Dancing with the SARs challenge at the NASA Space Apps Challenge. Data come from NISAR, a mission developed by NASA and ISRO.