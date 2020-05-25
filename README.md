# covid19
Analysis of public data on the spread of covid-19:
* [View Europe results using github viewer](eu.ipynb)
* [View World results using github viewer](world.ipynb)

## Process
The analysis takes daily data from the [European Centre for Disease Prevention and Control (ECDC)](https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide), updated for the previous day around 11 am UK time. A further update to UK data is made after daily figures are published on [www.gov.uk](https://www.gov.uk/guidance/coronavirus-covid-19-information-for-the-public).

The raw number of new cases and deaths reported each day can be erratic, making it difficult to detect the peak correctly. To allow for this, the analysis generates a smoothed data set using the daily central moving average. The average is calculated over 7 days with 3 days before, the current day and 3 days after.

Within the smoothed data, the analysis tries to identify key dates:
* Start date: when 50 cases have been reported
* Peak cases: when the number of new cases being reported peaks
* End date: mirrors the time between start date and peak cases, extended for dilation
* Day zero: when 50 deaths have been reported
* Peak deaths: when the number of new deaths being reported peaks

From this, key metrics are created:
* Growth: the number of days the infection is spreading i.e. days between start and peak cases
* Lag: the number of days between the peak number of cases and deaths
* Spread: the infection rate, based on comparing the number of new cases with the number 7 days earlier

The processing fits a [sigmoid curve / logistic distribution](https://en.wikipedia.org/wiki/Logistic_distribution) to the data. This produces a bell distribution for the new cases / deaths and an S-curve for the cumulative number of cases / deaths. These curves are used to extrapolate the potential progress of the infection. The parameters / characteristics of the models are:
* X = the sigmoid curve scale factor i.e. the maximum value of the function f(t) = X/(1 + exp(-rt/d))
* r = the exponential factor for the sigmoid curve and bell distribution e.g. exp(-rt/d)
* L = the bell distribution scale factor f(t) = L * exp(-rt/d) / (1 + exp(-rt/d)) ^ 2
* c = consistency between the smoothed data and bell distribution, 100% would be a perfect fit

The 'end day' is a notional date when the majority of cases / deaths from the current outbreak might be expected. The outcome includes a % of the maximum value of the functions at the end date, typically, 95% to 99% i.e. 95% of the total number of cases / deaths for an outbreak are expected to have occured by the end date.

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

The infection rate chart is based on the smoothed number of new cases being reported compared to 7 days earlier. An infection rate of 1 is shown as a green horizontal line for reference. The dotted line shows the predicted infection rate derrived from the bell distribution of new cases.

## Observations
Peak dates need to be used with care: the analysis assumes a minimum growth period and a lag if the peak is found at the end of the smoothed data. Where these minumum periods have elapsed, the latest smoothed data point will be assumed to be the peak. However, this can mean that the peak moves forward each day where the number of new cases or deaths continues to increase. The analysis reports the growth and lag periods observed in the smoothed data.

Following the peak in new cases / deaths, there is a trend for the numbers to flatten rather than drop off (could this be an effect of lock down constraining but not stopping the infection?). This can result in the predictions being lower than the actual data. To allow for this, the prediction has a 'dilation' parameter that adjusts the symmetry of the distribution curve, exp(-rt/d). When > 1, this stretches the distribution model time axis following the peak, slowing the drop off. Conversely, if < 1, it compresses the time axis following the peak, accelerating the drop off. Dilation is set to adjust the trajectory of the prediction where raw data has been reported but has not fed through into the smoothed data.

As new data is added daily, the modelling is re-fitted and the predictions are updated.

There seem to be lots of conspiracy theories about who is being affected. Might there just be a simple corelation between deaths per million population, general health and population density? Data for [life expectancy](https://data.worldbank.org/indicator/SP.DYN.LE00.IN) (as a proxy for general health) and [population density](https://www.worldometers.info/population/countries-in-europe-by-population/) is:

* Belgium: life expectancy = 82 years, density = 383 people / km2
* UK:      life expectancy = 81 years, density = 281 people / km2
* Germany: life expectancy = 81 years, density = 240 people / km2
* Italy:   life expectancy = 83 years, density = 206 people / km2
* France:  life expectancy = 83 years, density = 119 people / km2
* Spain:   life expectancy = 83 years, density =  94 people / km2
* Ireland: life expectancy = 83 years, density =  72 people / km2
* USA:     life expectancy = 79 years, density =  20 people / km2

Given these factors, you could expect the death rate in the UK and Belgium to be higher other than European countries.
