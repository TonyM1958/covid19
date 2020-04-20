# covid19
Analysis of public data on the spread of covid-19: [view results using github viewer](covid.ipynb)

## Process
The analysis takes daily data from the [European Centre for Disease Prevention and Control (ECDC)](https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide), which is generally updated for the previous day around 11am UK time.

The raw number of new cases and deaths reported each day can vary considerably, making it difficult to detect the peak correctly. To allow for this, the analysis generates a smoothed data set that is the average reported over a sliding window. By default, the window is 9 days wide i.e. average of 4 days before, the current day and 4 days after a specific date.

Within the smoothed data, the analysis tries to identify key dates:
* Start date: when 50 cases have been reported
* Peak cases: when the number of new cases being reported peaks
* End date: added symmetrically around the peak cases, mirroring start date
* Day zero: when 50 deaths have been reported
* Peak deaths: when the number of new deaths being reported peaks

From this, a number of metrics are created:
* Growth: the number of days the infection is spreading i.e. the days between start and peak cases
* Lag: the number of days between the peak number of cases and deaths
* Spread: the infection rate, based on comparing the number of new cases reported with 7 days earlier

The processing fits a [sigmoid curve / logistic distribution](https://en.wikipedia.org/wiki/Logistic_distribution) to the data. This produces a bell distribution for the new cases / deaths and an S-curve for the cumulative number of cases / deaths. These curves are used to extrapolate the potential progress of the infection.

## Charts
The analysis plots the number of new cases / new deaths over time. This includes the following elements:
* Raw number of new cases: the green dotted line
* Smoothed number of new cases: the solid blue line
* Raw number of new deaths: the dotted orange line
* Smoothed number of new deaths: the solid red line
* Modelled number of new cases: the upper grey dotted line (tracking blue)
* Modelled number of new deaths: the lower grey dotted line (tracking red)

A number of date markers are also added:
* Green dotted line: the latest date when data is available
* Grey dotted lines: the Start, peak cases and end dates, left to right
* Brown dotted lines: Day Zero and peak deaths

A second chart shows the infection rate based on the smoothed number of new cases being reported compared to 7 days earlier. An infection rate of 1 is shown as a green horizontal line for reference.

## Observations
Peak dates need to be used with care: the analysis assumes a minimum growth period and a lag if the peak is found at the end of the smoothed data. Where these minumum periods have elapsed, the latest smoothed data point will be assumed to be the peak. However, this can mean that the peak moves forward each day where the number of new cases or deaths continues to increase. The analysis reports the growth and lag periods observed in the smoothed data.

Following the peak in new cases / deaths, there is a trend for the numbers to flatten rather than drop off (could this be an effect of the lock down constraining but not stopping the infection?). This can result in the predictions being lower than the actual data. To allow for this, the prediction has a 'dilation' parameter that sets the symmetry of the distribution curve. When > 1, this stretches the distribution model time axis following the peak, slowing the drop off. Conversely, if < 1, it compresses the time axis following the peak, accelerating the drop off. Dilation is set to adjust the trajectory of the prediction where raw data has been reported but has not fed through into the smoothed data.

As new data is added daily, the modelling is re-fitted and the predictions are updated.
