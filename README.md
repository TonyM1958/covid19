# covid19
Analysis of public data on the spread of covid-19

### Process
The analysis takes daily data from the European Centre for Disease Control (ECDC) and analyses this. Data is generally updated for the previous day around 11am each day.

The raw number of new cases and deaths being reported suffers from a number of data collection problems and can be very spiked. To cater for this, the processing generates a smoothed data set for cases and deaths that is the average number reported over a sliding window of days. By default, the sliding window is 9 days i.e. 4 days before and 4 days after a specific date.

Within the smoothed data, the analysis tries to identify some key dates:
* Start date: this is when 50 cases have been reported
* Peak cases: this is when the number of new cases being reported peaks
* End date: this is added symmetrically around the peak cases, mirroring start date
* Day zero: this is when 50 reported deaths have been reported
* Peak deaths: this is when the number of new deaths being reported peaks

From this data, a number of metrics are created:
* Growth: the number of days when the infection is spreading i.e. the days between start and peak cases
* Lag: the number of days between the peak number of cases and the peak number of deaths
* Spread: the infection rate, based on comparing the number of new cases reported with the number from 7 days earlier

The processing fits a simple logistical population model to the data, based on the formula A = L / (1 + exp(-rt)). This produces an S-curve when the total number of cases / deaths is viewed and a bell distribution the number of new cases / deaths is viewed. This model is then used to extrapolate from the data available to attempt to predict the expected progress of the infection.

## Charts
The main chart produced plots the number of new cases / new deaths over time. This includes the following elements:
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

The infection rate chart shows the spread based on the number of new cases being reported compared to 7 days earlier.
