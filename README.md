# covid19
Analysis of public data on the spread of covid-19: [github viewer](covid.ipynb) / 
[nbviewer](https://nbviewer.jupyter.org/github/TonyM1958/covid19/blob/master/covid.ipynb?flush_cache=true)

## Process
The analysis takes daily data from the [European Centre for Disease Prevention and Control (ECDC)](https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide), which is generally updated for the previous day around 11am UK time.

The raw number of new cases and deaths reported each day can be vary considerably, making it difficult to detect the peak correctly. To allow for this, the analysis generates a smoothed data set that is the average reported over a sliding window. By default, the window is 9 day wides i.e. average of 4 days before, the current day and 4 days after a specific date.

Within the smoothed data, the analysis attempts to identify key dates:
* Start date: when 50 cases have been reported
* Peak cases: when the number of new cases being reported peaks
* End date: added symmetrically around the peak cases, mirroring start date
* Day zero: when 50 reported deaths have been reported
* Peak deaths: when the number of new deaths being reported peaks

From this, a number of metrics are created:
* Growth: the number of days the infection is spreading i.e. the days between start and peak cases
* Lag: the number of days between the peak number of cases and deaths
* Spread: the infection rate, based on comparing the number of new cases reported with the number from 7 days earlier

The processing fits a [sigmoid curve / logistic function](https://en.wikipedia.org/wiki/Logistic_function) A = L / (1 + exp(-rt)) to the available data. This produces an S-curve for the cumulative number of cases / deaths and a bell distribution for the new cases / deaths. These curves are used to extrapolate the potential progress of the infection.

## Charts
The analysis plots the number of new cases / new deaths over time, on a logarithmic scale. This includes the following elements:
* Raw number of new cases: the green dotted line
* Smoothed number of new cases: the solid blue line
* Raw number of new deaths: the dotted orange line
* Smoothed number of new deaths: the solid red line
* Modelled number of new cases: the upper grey dotted line (tracking blue)
* Modelled number of new deaths: the lower grey dotted line (tracking red)

A number of date markers are also added:
* Green dotted line: the latest date when data is available
* Grey dotted lines: the Start, peak cases and end dates, left to right
* Brown lines: Day Zero and peak deaths

A second chart separately shows the infection rate based on the smoothed number of new cases being reported compared to 7 days earlier. The infection rate of 1 is shown as a green horizontal line.

## Observations
Peak dates need to be used with care: the analysis assumes a minimum growth period and a lag if the peak is found at the end of the smoothed data. Where these periods have already elapsed, the latest smoothed data is assumed to be the peak but this can mean that the peak moves forward each day if the number of new cases or deaths continues to increase. The analysis reports the actual growth and lag periods derrived from the smoothed data.

Following the peak in new cases / peak deaths, there is a tendency for the numbers to remain high i.e. flatten off rather than drop off. This results in the predictions being lower than the actual data. To cater for this, the sigmoid function includes an option to reduce the drop off of the curve to improve tracking of the data (dilation).

As new data is added daily, the modelling is re-fitted and the predictions are updated.
