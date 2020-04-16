# covid19
Analysis of public data on the spread of covid-19.
* [jump to on-line notebook viewer](https://nbviewer.jupyter.org/github/TonyM1958/covid19/blob/master/covid.ipynb)

## Process
The analysis takes daily data from the [European Centre for Disease Control (ECDC)](https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide), which is generally updated for the previous day around 11am UK time.

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

The processing fits a simple logistical population model to the data, based on the formula A = L / (1 + exp(-rt)). This produces an S-curve when the cumulative number of cases / deaths is viewed and a bell distribution when the number of new cases / deaths is viewed. This model is used to extrapolate from the data to predict the expected progress of the infection, total number of cases and deaths reported by the 'end date'.

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
The data for China benchmarks how well the modelling works. It is also clear from the data that there was the potential for a second wave of infection, highlighting the potential risks associated with reducing the lock down too early.

Peak dates should be used with care. The analysis assumes a minimum growth period of 38 days and a lag of 4 days that will be applied (if not over-ridden) if the peak is found in the latest smoothed data. Where this happens, the latest smoothed data is assumed to represent the peak but this can mean that the peak moves forward each day if the number of new cases or deaths continues to increase. The report shows the actual growth and lag derrived from analysis of the smoothed data.

Following the peak in new cases / peak deaths, there is a tendency for the modelling to over-estimate the numbers. However, there is also a clear tendency for the actual numbers not to fall off as quickly as the model. These two effects broadly offset each other. As new data is added, the modelling is updated and re-fitted against the latest smoothed data.
