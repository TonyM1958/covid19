##################################################################################################
"""
Module:   Covid data analysis
Date:     06 April 2020
Author:   Tony Matthews
"""
##################################################################################################

##################################################################################################
# Model Parameters
# geoId:       2 letter code for the region. Default UK
# smooth:      number of raw data points to use for each smoothed data point, to cater for data
#              reporting issues. Default is 9 days with typical values between 5 and 11 days.
# growth_days: Expected number of days between start and peak (when new cases are increasing).
#              Default is 38 days with typical values between 30 and 40. Higher values are seen
#              for larger terrortories where spread is slower. Over-ridden after peak cases occurs.
# lag:         Expected number of days lag between peak cases and peak deaths. Default is 6 with
#              typical values between 0 and 12. Over-ridden after peak deaths occurs.
# r_cases:     Growth factor for cases sigmoid function 1 / (1 + exp(-rt)) used to fit the S
#              curve to the observed data. t starts at -1 and ends at +1 as time goes from start to
#              end day. Default is 7 with typically values between 6 and 9
# r_deaths:    Growth factor for deaths sigmoid function, offset by lag. See above
# contagious:  The number of days where a person may infect others. Default is 7 with typical values
#              between 5 and 15
# figwidth:    sets the size of the charts. Deault is 10 with typical values between 7 and 12.
##################################################################################################

import json
import datetime
import math
import matplotlib.pyplot as plt

json_data = None        # string containing json data downloaded from web site
region_codes = ['UK', 'FR', 'IT', 'DE', 'ES', 'US', 'CN', 'KR', 'JP', 'NZ']

def average(lst): 
    """
    calculate average value for a list of numbers
    """
    return sum(lst) / len(lst) 

def num(x, width=8): 
    """
    format a number for display
    """
    if x is None : return width * ' '
    s = width * ' ' + f"{int(x):,}"
    return s[-width:] 

def load(geoId='UK') :
    """
    load data from download file, decorate and return 
    """
    global json_data
    # clean up any problems in the download file and load string into buffer
    if json_data is None :
        n=0
        s = ''
        f = open('download.json', 'r' )
        while True :
            line = f.readline()
            if line == '' : break   # end of file
            n += 1
            # ignore BOM if there is one and remove invalid lines
            if n==1 : line ="{"
            if line[0].isdigit() or line[0:7] == 'dateRep' : continue
            s += line
        f.close()
        json_data = s
    # print(f"{n} lines read from download file")
    # get the records for the region
    data = [r for r in json.loads(json_data).get('records') if r.get('geoId') == geoId]
    # convert data for each record
    for r in data :
        r['dateRep'] = datetime.datetime.strptime(r.get('dateRep'), "%d/%m/%Y") + datetime.timedelta(-1)
        r['cases'] = int(r.get('cases'))
        r['deaths'] = int(r.get('deaths'))
        r['popData2018'] = int(r.get('popData2018'))
    # sort records into ascending date order
    data = sorted(data, key = lambda r: r.get('dateRep'))
    cases_to_date = 0
    deaths_to_date = 0
    for r in data :
        cases_to_date += r.get('cases')
        deaths_to_date += r.get('deaths')
        r['cases_to_date'] = cases_to_date
        r['deaths_to_date'] = deaths_to_date
    return(data)

class Region :
    """
    Holds the data about a region
    """    
    def __init__(self, geoId='UK', smooth=9, growth_days=38, lag=4, spread=7, trend_days=0, step=0.1, r_cases=0, r_deaths=0, figwidth=12, dilation=2.5, debug=0) :
        # check parameters
        self.debug = debug
        if geoId not in region_codes :
            print(f"Region Codes: {region_codes}\n")
        if smooth % 2 == 0 : smooth += 1
        self.smooth = smooth                  # number of raw data points to average over to reduce anomalies
        self.growth_days = growth_days        # predicted number of days from start to peak cases
        self.lag = lag                        # predicted number of days lag between peak cases and peak deaths
        self.r_cases = r_cases                # sigmoid range for cases e.g 1 + exp(-rt) for t = -1 to +1 
        self.r_deaths = r_deaths              # sigmoid range for deaths e.g 1 + exp(-rt) for t = -1 to +1
        self.spread = spread                  # number of days a person may infect others
        self.trend_days = trend_days          # number of days to look back when predicting cases and deaths
        self.step = step                      # step change in r to use when working out best fit
        self.dilation = dilation              # dilutes the drop off after peak
        self.figsize = (figwidth, figwidth * 9 / 16)     # size of charts
        # load dat
        self.data = load(geoId)
        # check we have some data to work on
        if len(self.data) == 0 : return
        self.count = len(self.data)
        self.geoId = self.data[-1].get('geoId')                                             # 2 letter ISO country code
        self.latest = self.data[-1].get('dateRep')                                          # date when last data was provided
        self.total_cases = self.data[-1].get('cases_to_date')                               # total number of cases reported
        self.total_deaths = self.data[-1].get('deaths_to_date')                             # total number of deaths reported
        self.population = self.data[-1].get('popData2018')                                  # region population
        self.case_rate = int(round(self.total_cases * 1000000.0 / self.population, 0))      # cases per million population
        self.death_rate = int(round(self.total_deaths * 1000000.0 / self.population, 0))    # deaths per million population
        # scan through data to calculate attributes and smoothed data
        # note: day index values are negative as they are relative to the latest report date
        self.start_days = None         # when there are 50 or more cases
        self.start = None              # start date
        self.day0_days = None          # when there are 50 or more cases
        self.day0 = None               # date of day zero
        self.s_total_cases = 0         # total number of cases in smoothed data
        self.s_total_deaths = 0        # total number of deaths in smoothed data
        self.s_latest_days = None       # index for last day in smoothed data
        self.s_latest = None            # latest date in smoothed data
        for i in range(0, len(self.data)) :
            # find start day
            if self.start_days is None and self.data[i].get('cases_to_date') >= 50 :
                self.start = self.data[i].get('dateRep')
                self.start_days = i - self.count
            # find day zero
            if self.day0_days is None and self.data[i].get('deaths_to_date') >= 50 :
                self.day0 = self.data[i].get('dateRep')
                self.day0_days = i - self.count
            # calculate smoothed data points
            s_cases = 0
            s_deaths = 0
            valid = 1
            self.data[i]['s_cases'] = None
            self.data[i]['s_deaths'] = None
            for j in range(0, self.smooth) :
                k = i + j - int(self.smooth/2)
                # start and end averages are biased towards first / last data point
                if k < 0 : valid = 0
                if k >= len(self.data) : valid = 0
                if valid == 1 :
                    s_cases += self.data[k].get('cases') / self.smooth
                    s_deaths += self.data[k].get('deaths') / self.smooth
            if valid == 1 :
                self.s_latest_days = i - self.count
                self.s_latest = self.data[i].get('dateRep')
                self.data[i]['s_cases'] = s_cases
                self.data[i]['s_deaths'] = s_deaths
                self.s_total_cases += s_cases
                self.s_total_deaths += s_deaths
        # rescale smoothed data to match actual totals and calculate parameters
        case_rescale = self.data[self.s_latest_days].get('cases_to_date') / self.s_total_cases
        death_rescale = self.data[self.s_latest_days].get('deaths_to_date') / self.s_total_deaths
        self.s_total_cases = 0          # total of smoothed cases
        self.s_total_deaths = 0         # total of smoothed deaths
        self.s_start_days = None        # index for start day in smoothed data
        self.s_start = None             # start date in smoothed data
        self.s_day0_days = None         # index for start day in smoothed data
        self.s_day0 = None              # start date in smoothed data
        self.s_peak_case_days = None    # index for peak cases in smoothed data (if reached)
        self.s_peak_cases = None        # date for peak cases in smoothed data
        self.s_peak_death_days = None   # index for peak deaths in smoothed data (if reached)
        self.s_peak_deaths = None       # date for peak deaths in smoothed data
        self.s_end_days = None          # index for end of epidemic in smoothed data (if reached)
        self.s_end = None               # date for end of epidemic in smoothed data
        self.s_r0_peak = 0              # peak value for R0
        self.s_r0_peak_date = None      # date when R0 peaks
        self.s_r0_peak_days = None      # index for day when R0 peaks
        self.s_r0_latest = 0            # latest value for R0
        self.s_r0_latest_date = None    # date of latest R0
        self.s_r0_latest_days = None    # index for latest R0
        peak = 0
        for i in range(0,len(self.data)) :
            self.data[i]['s_cases_to_date'] = None
            self.data[i]['s_deaths_to_date'] = None
            self.data[i]['s_r0'] = None
            if self.data[i].get('s_cases') is None : continue
            # rescale smoothed data and update
            self.data[i]['s_cases'] *= case_rescale
            self.data[i]['s_deaths'] *= death_rescale
            self.s_total_cases += self.data[i]['s_cases']
            self.s_total_deaths += self.data[i]['s_deaths']
            self.data[i]['s_cases_to_date'] = self.s_total_cases
            self.data[i]['s_deaths_to_date'] = self.s_total_deaths
            if (i - self.spread) > 0 and self.data[i].get('s_cases') is not None and self.data[i - self.spread].get('s_cases') is not None and self.s_total_cases >= 500 and self.data[i - self.spread].get('s_cases') != 0:
                # calculate infection rate
                self.data[i]['s_r0'] = round(self.data[i].get('s_cases') / self.data[i - self.spread].get('s_cases'),1)
                self.s_r0_latest = self.data[i].get('s_r0')
                self.s_r0_latest_days = i - self.count
                self.s_r0_latest_date = self.data[i].get('dateRep')
                if self.data[i].get('s_r0') > self.s_r0_peak :
                    self.s_r0_peak = self.data[i].get('s_r0')
                    self.s_r0_peak_days = i - self.count
                    self.s_r0_peak_date = self.data[i].get('dateRep')
            # find smoothed start day
            if self.s_start_days is None and self.s_total_cases >= 50 :
                self.s_start = self.data[i].get('dateRep')
                self.s_start_days = i - self.count
            # find smoothed day zero
            if self.s_day0_days is None and self.s_total_deaths >= 50 :
                self.s_day0 = self.data[i].get('dateRep')
                self.s_day0_days = i - self.count
            # find smoothed peak cases day
            if self.data[i].get('s_cases') > peak :
                peak = self.data[i].get('s_cases')
                self.s_peak_cases = self.data[i].get('dateRep')
                self.s_peak_case_days = i - self.count
        # check if peak cases was found. Predict using growth days if not
        if self.s_peak_case_days >= self.s_latest_days and self.s_peak_case_days - self.s_start_days < self.growth_days:
            self.s_peak_case_days = self.s_start_days + self.growth_days
            self.s_peak_cases = self.s_start + datetime.timedelta(self.growth_days)
        else :
            # update growth days with actual
            self.growth_days = self.s_peak_case_days - self.s_start_days
        if self.debug > 0 :
            print(f"> peak cases: {int(peak):,} on {self.s_peak_cases:%Y-%m-%d} {self.s_peak_case_days+1} days")
        # calculate cycle and end from time between start and peak (i.e. symmetrical)
        self.cycle = 2 * (self.s_peak_case_days - self.s_start_days)
        self.s_end_days = self.s_start_days + self.cycle
        self.s_end = self.latest + datetime.timedelta(self.s_end_days)
        peak = 0
        for i in range(self.s_peak_case_days, self.s_end_days) :
            # find smoothed peak deaths day
            if self.data[i].get('s_deaths') is None : continue
            if self.data[i].get('s_deaths') > peak :
                peak = self.data[i].get('s_deaths')
                self.s_peak_deaths = self.data[i].get('dateRep')
                self.s_peak_death_days = i
        # check if peak deaths was found. Predict using lag if not
        if self.s_peak_death_days >= self.s_peak_case_days and self.s_peak_death_days >= self.s_latest_days and self.s_peak_death_days - self.s_peak_case_days < self.lag:
            self.s_peak_death_days = self.s_peak_case_days + self.lag
            self.s_peak_deaths = self.s_peak_cases + datetime.timedelta(self.lag)
        else :
            # update lag with actual
            self.lag = self.s_peak_death_days - self.s_peak_case_days
        if self.debug > 0 :
            print(f"> peak deaths: {int(peak):,} on {self.s_peak_deaths:%Y-%m-%d} {self.s_peak_death_days+1} days")
        # build predictions using sigmoid population curves
        self.build_sigmoid()
        return

    def report(self) :
        """
        report key statistics from the data to date
        """
        print(f"{self.geoId} confirmed data up to end of {self.latest:%Y-%m-%d}:")
        print(f"  {self.total_cases:,} confirmed cases, {self.total_deaths:,} deaths")
        print(f"  {self.case_rate:,} cases per million, {self.death_rate:,} deaths per million (population = {self.population:,})")
        print()
        print(f"Timeline: (-ve days are past, +ve days are predicted)")
        # Add 1 to display the actual number of days as these are zero based indexes
        print(f"  Start:       {self.s_start:%Y-%m-%d} ({self.s_start_days+1:3} days, when 50 or more cases were reported)")
        print(f"  Peak Cases:  {self.s_peak_cases:%Y-%m-%d} ({self.s_peak_case_days+1:3} days)")
        print(f"  End:         {self.s_end:%Y-%m-%d} ({self.s_end_days+1:3} days, {self.growth_days} days after peak cases)")
        if self.s_total_deaths >= 50 :
            print(f"  Day Zero:    {self.s_day0:%Y-%m-%d} ({self.s_day0_days+1:3} days, when 50 or more deaths were reported)")
            print(f"  Peak Deaths: {self.s_peak_deaths:%Y-%m-%d} ({self.s_peak_death_days+1:3} days)")
        print()
        print(f"Parameters:")
        print(f"  Totals:      {self.data[self.s_latest_days].get('cases_to_date'):,} cases and {self.data[self.s_latest_days].get('deaths_to_date'):,} deaths at end of {self.s_latest:%Y-%m-%d}")
        print(f"  Smoothed:    {int(self.s_total_cases):,} cases and {int(self.s_total_deaths):,} deaths at end of {self.s_latest:%Y-%m-%d} ({self.smooth} adjacent points)")
        print(f"  Spread:      Peak infection rate {self.s_r0_peak} ({self.s_r0_peak_date:%Y-%m-%d}, compared to {self.spread} days earlier)")
        print(f"               Latest infection rate {self.s_r0_latest} ({self.s_r0_latest_date:%Y-%m-%d}, compared to {self.spread} days earlier)")
        print(f"  Growth:      {self.growth_days} days (Start -> Peak Cases) ")
        if self.s_total_deaths >= 50 :
            print(f"  Lag:         {self.lag} days (Peak Cases -> Peak Deaths) ")
            print(f"  Prediction:  Cases L = {int(self.L_cases):,} r = {round(self.r_cases,2)} (over {self.trend_days} days)")
            print(f"               Deaths L = {int(self.L_deaths):,} r = {round(self.r_deaths,2)} (over {self.trend_days} days)")
            print()
            if self.s_end_days < 0 :
                d = self.s_end_days
                cases = int(self.data[d].get('cases_to_date'))
                cases_rate = int(round(cases * 1000000 / self.population, 0))
                deaths = int(self.data[d].get('deaths_to_date'))
                death_rate = int(round(deaths * 1000000 / self.population, 0))
                print(f"Outcome: {cases:,} cases, {deaths:,} deaths at end of {self.data[d].get('dateRep'):%Y-%m-%d}")
                print(f"  {cases_rate:,} cases per million, {death_rate:,} deaths per million (population = {self.population:,})")
            else :
                cases = int(self.sigmoid_cases_to_date[-1])
                cases_rate = int(round(cases * 1000000 / self.population, 0))
                deaths = int(self.sigmoid_deaths_to_date[-1])
                death_rate = int(round(deaths * 1000000 / self.population, 0))
                print(f"Outcome: {cases:,} cases, {deaths:,} deaths at end of {self.s_end:%Y-%m-%d}")
                print(f"  {cases_rate:,} cases per million, {death_rate:,} deaths per million (population = {self.population:,})")
        print()
        return
    
    def show(self, days=7) :
        """
        show records for last number of days
        """
        days = -days
        print()
        print(f"              Raw ----------     Total --------     Smoothed ------   Total ---------")
        print(f"Date          Cases   Deaths     Cases   Deaths     Cases   Deaths     Cases   Deaths")
        for r in self.data[days:] :
            print(f"{r.get('dateRep'):%Y-%m-%d} {num(r.get('cases'))} {num(r.get('deaths'))} " + \
                  f" {num(r.get('cases_to_date'))} {num(r.get('deaths_to_date'))} " + \
                  f" {num(r.get('s_cases'))} {num(r.get('s_deaths'))} " + \
                  f" {num(r.get('s_cases_to_date'))} {num(r.get('s_deaths_to_date'))} ")
        print()
        return

    def plot(self, days=0, ylog=1, daily=1, infection=1, totals=0, clip=12) :
        """
        plot the graph of a property against the day reported
        """
        if days == 0 : days = self.s_start_days
        else : days = -days
        dates = [r.get('dateRep') for r in self.data[days:]]
        date_range = [self.s_start + datetime.timedelta(d) for d in range(0, max(len(self.data[self.s_start_days:]), len(self.sigmoid_cases)),7)]
        # plot daily data
        if daily == 1 :
            plt.figure(figsize=self.figsize)
            plt.title(f"{self.geoId}\nNew Cases (green=raw, blue=smoothed)\nNew Deaths (orange=raw, red=smoothed)")
            plt.plot(dates, [r.get('s_cases') for r in self.data[days:]], color='blue', linestyle='solid')
            plt.plot(dates, [r.get('s_deaths') for r in self.data[days:]], color='red', linestyle='solid')
            plt.plot(dates, [r.get('cases') for r in self.data[days:]], color='green', linestyle='dotted')
            plt.plot(dates, [r.get('deaths') for r in self.data[days:]], color='orange', linestyle='dotted')
            plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
            if self.s_total_deaths >= 50 : 
                plt.axvline(self.s_day0, color='tan', linestyle='dashed', linewidth=2, label='day0')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_cases))], self.sigmoid_cases, color='grey', linestyle='dashed')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_deaths))], self.sigmoid_deaths, color='grey', linestyle='dashed')
                plt.axvline(self.s_peak_deaths, color='tan', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_peak_cases, color='grey', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_end, color='grey', linestyle='dashed', linewidth=2, label='end')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            if ylog==1 : plt.yscale('log')
            plt.grid()
            plt.xticks(date_range, rotation=90)
            plt.show()
            print()
        # plot infection rate
        if infection == 1 :
            plt.figure(figsize=self.figsize)
            plt.title(f"{self.geoId}\nInfection Rate, based on number of new cases compared to {self.spread} days earlier")
            plt.plot(dates, [r.get('s_r0') for r in self.data[days:]], color='brown', linestyle='solid')
            plt.axhline(y=1, color='green', linestyle='dashed', linewidth=2, label='1')
            if self.s_r0_peak > clip : plt.ylim([0, clip])
            else : plt.ylim([0, 4 * (int(self.s_r0_peak / 4) + 1)])
            if self.s_total_deaths >= 50 : 
                plt.xticks([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_cases),7)], rotation=90)
                plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
                plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
                plt.axvline(self.s_day0, color='tan', linestyle='dashed', linewidth=2, label='day0')
                plt.axvline(self.s_peak_deaths, color='tan', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_peak_cases, color='grey', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_end, color='grey', linestyle='dashed', linewidth=2, label='end')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.grid()
            plt.xticks(date_range, rotation=90)
            plt.show()
            print()
        # plot totals
        if totals == 1 :
            plt.figure(figsize=self.figsize)
            plt.title(f"{self.geoId}\nTotal Cases (green=raw, blue=smoothed)\nTotal Deaths (orange=raw, red=smoothed)")
            plt.plot(dates, [r.get('s_cases_to_date') for r in self.data[days:]], color='blue', linestyle='solid')
            plt.plot(dates, [r.get('s_deaths_to_date') for r in self.data[days:]], color='red', linestyle='solid')
            plt.plot(dates, [r.get('cases_to_date') for r in self.data[days:]], color='green', linestyle='dotted')
            plt.plot(dates, [r.get('deaths_to_date') for r in self.data[days:]], color='orange', linestyle='dotted')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
            if self.s_total_deaths >= 50 : 
                plt.axvline(self.s_day0, color='tan', linestyle='dashed', linewidth=2, label='day0')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_cases_to_date))], self.sigmoid_cases_to_date, color='grey', linestyle='dashed')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_deaths_to_date))], self.sigmoid_deaths_to_date, color='grey', linestyle='dashed')
                plt.xticks([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_cases),7)], rotation=90)
                plt.axvline(self.s_peak_deaths, color='tan', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_peak_cases, color='grey', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_end, color='grey', linestyle='dashed', linewidth=2, label='end')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            if ylog==1 : plt.yscale('log')
            plt.grid()
            plt.xticks(date_range, rotation=90)
            plt.show()
            print()
        return

    def t (self, day, offset) :
        """
        return the scaled time in a cycle for a day. Start t = -1 to End t = +1
        dilation is applied after the peak to extend the decay time
        """
        lag = self.lag if offset == 1 else 0
        x = 2 * (day - self.s_start_days - lag) - self.cycle
        if x > 0 : x /= self.dilation
        return x / self.cycle

    def bell_A(self, L, r, d, offset) :
        """
        return the value of the sigmoid function 
        """
        x = self.t(d, offset)
        A = L * math.exp(r * x) / (1 + math.exp(r * x)) ** 2
        return A

    def sigmoid_A(self, L, r, d, offset) :
        """
        return the value of the sigmoid function 
        """
        x = self.t(d, offset)
        A = L / (1 + math.exp( -1 * r * x))
        return A

    def sigmoid_L(self, A, r, d, offset) :
        """
        given a result, return the sigmoid parameter L
        """
        x = self.t(d, offset)
        L = A * (1 + math.exp( -1 * r * x))
        return L

    def sigmoid_r(self, L, A, d, offset) :
        """
        given a result, return the sigmoid parameter r
        """
        x = self.t(d, offset)
        r = -1 * math.log(L/A - 1) / x
        return r

    def rms_error(self, day1, day2, L, r, offset) :
        """
        calculate root mean square error between the smoothed data and sigmoid function:
        """
        name = 's_cases_to_date' if offset == 0 else 's_deaths_to_date'
        n = 0
        result = 0
        d = day1
        while d <= day2 :
            if self.data[d].get(name) is not None :
                result += (self.data[d].get(name) - self.sigmoid_A(L, r, d, offset)) ** 2
                n += 1
            d += 1
        if n == 0 : return None
        else : return result ** 0.5 / n

    def adjust_r(self, day1, day2, L, r, offset, tries=0) :
        """
        adjust r for lowest rms error to smoothed data
        """
        cases = 'Cases' if offset == 0 else 'Deaths'
        x = self.rms_error(day1, day2, L, r, offset)
        if self.debug > 0 : print(f"> {cases} {tries}: L = {int(L):,}, r = {round(r, 2)}, error = {x}")
        best_r = r
        error = x
        trend = -1
        while True :
            r += self.step
            x = self.rms_error(day1, day2, L, r, offset)
            if x < error :
                if self.debug > 0 : print(f"> {cases} {tries}: L = {int(L):,}, r = {round(r, 2)}, error = {x}")
                error = x
                best_r = r
                trend = 1
            else : break
        while trend == -1 :
            r -= self.step
            x = self.rms_error(day1, day2, L, r, offset)
            if x < error :
                if self.debug > 0 : print(f"> {cases} {tries}: L = {int(L):,}, r = {round(r, 2)}, error = {x}")
                error = x
                best_r = r
            else : break
        return best_r

    def fit_cases(self, day1, day2) :
        # fit L_cases and r_cases to smoothed data
        previous_L = 0.0
        previous_r = 0.0
        tries = 0
        if self.r_cases == 0 : self.r_cases = 6
        while tries < 20 :
            self.L_cases = self.sigmoid_L(self.data[day2].get('s_cases_to_date'), self.r_cases, day2, 0)
            self.r_cases = self.sigmoid_r(self.L_cases, self.data[day1].get('s_cases_to_date'), day1, 0)
            self.r_cases = self.adjust_r(day1, day2, self.L_cases, self.r_cases, 0, tries)
            if int(self.L_cases) == previous_L and round(self.r_cases, 2) == previous_r : break
            previous_L = int(self.L_cases)
            previous_r = round(self.r_cases,2)
            tries += 1
        if tries >= 20 : print(f"** fit_cases did not converge")
        return
        
    def fit_deaths(self, day1, day2) :
        # fit L_deaths and r_deaths to smoothed data
        previous_L = 0.0
        previous_r = 0.0
        tries = 0
        if self.r_deaths == 0 : self.r_deaths = 8
        while tries < 20 :
            self.L_deaths = self.sigmoid_L(self.data[day2].get('s_deaths_to_date'), self.r_deaths, day2, 1)
            self.r_deaths = self.sigmoid_r(self.L_deaths, self.data[day1].get('s_deaths_to_date'), day1, 1)
            self.r_deaths = self.adjust_r(day1, day2, self.L_deaths, self.r_deaths, 1, tries)
            if int(self.L_deaths) == previous_L and round(self.r_deaths, 2) == previous_r : break
            previous_L = int(self.L_deaths)
            previous_r = round(self.r_deaths, 2)
            tries += 1
        if tries >= 20 : print(f"** fit_deaths did not converge")
        return

    def build_sigmoid(self) :
        """
        use a sigmoid population function to model the smoothed total number of cases / deaths.
        The function is y = L / (1 + exp(-rt)) where t = -1 at the start and +1 at the end. This produces
        an S curve that starts at 0 and tends to L at the end. The differential of the S curve is a bell
        curve that describes the daily changes in cases / deaths. Both curves are held from start day.
        """
        self.sigmoid_cases = []
        self.sigmoid_cases_to_date = []
        self.sigmoid_deaths = []
        self.sigmoid_deaths_to_date = []
        self.L_cases = None
        self.L_deaths = None
        if self.s_total_deaths < 50 :
            return
        day2 = self.s_end_days if self.s_end_days < self.s_latest_days else self.s_latest_days
        if self.trend_days == 0 :
            day1 = self.s_day0_days
            self.trend_days = day2 - day1
        else : day1 = day2 - self.trend_days
        self.fit_cases(day1, day2)
        self.fit_deaths(day1, day2)
        self.trend = day2 - day1
        # generate data points, starting with point -1 so we can get a delta for new cases / deaths
        cases = []
        cases_to_date = 0
        deaths = []
        deaths_to_date = 0
        for d in range(0, self.cycle) :
            cases.append(self.bell_A(self.L_cases, self.r_cases, self.s_start_days + d, 0))
            deaths.append(self.bell_A(self.L_deaths, self.r_deaths, self.s_start_days + d, 1))
            if self.s_start_days + d <= self.s_latest_days :
                cases_to_date += cases[-1]
                deaths_to_date += deaths[-1]
        self.sigmoid_cases = []
        self.sigmoid_cases_to_date = []
        self.sigmoid_deaths = []
        self.sigmoid_deaths_to_date = []
        cases_rescale = self.data[self.s_latest_days].get('s_cases_to_date') / cases_to_date
        deaths_rescale = self.data[self.s_latest_days]. get('s_deaths_to_date') / deaths_to_date
        cases_to_date = 0
        deaths_to_date = 0
        for d in range(0, self.cycle) :
            self.sigmoid_cases.append(cases[d] * cases_rescale)
            self.sigmoid_deaths.append(deaths[d] * deaths_rescale)
            cases_to_date += self.sigmoid_cases[-1]
            deaths_to_date += self.sigmoid_deaths[-1]
            self.sigmoid_cases_to_date.append(cases_to_date)
            self.sigmoid_deaths_to_date.append(deaths_to_date)
        return

    def prediction(self, days=0, start=0) :
        """
        use the sigmoid curves to predict future cases / deaths
        """
        if self.s_total_deaths < 50 : return
        if days == 0 : days = self.s_end_days
        if days < 1 : return
        if self.s_end_days < 1 : return
        print()
        print(f"              Prediction ---    Total -------")
        print(f"Date          Cases   Deaths    Cases  Deaths")
        for d in range(start, days) :
            i = self.s_latest_days - self.s_start_days + d
            if i >= len(self.sigmoid_cases) : break
            print(f"{self.s_latest + datetime.timedelta(d):%Y-%m-%d}" + \
                  f" {num(self.sigmoid_cases[i])} {num(self.sigmoid_deaths[i])}" + \
                  f" {num(self.sigmoid_cases_to_date[i])} {num(self.sigmoid_deaths_to_date[i])}")
        print()
        return

    def analyse(self, days=14, predict=14, ylog=1, daily=1, infection=1, totals=0) :
        self.report()
        self.plot(ylog=ylog, daily=daily, infection=infection, totals=totals)
        self.show(days=days)
        self.prediction(days=predict)
        return
