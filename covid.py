##################################################################################################
"""
Module:   Covid data analysis
Date:     28 April 2020
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
# spread:     The number of days to use when working out infection rate. Default is 7 with typical
#              values between 5 and 15
# dilation:    Controls the symmetry of the bell distribution. Default is 2 with typical values
#              between 0.1 and 10. A value of 1 produces a symmetric distribution.
# figwidth:    sets the size of the charts. Deault is 12 with typical values between 7 and 12.
##################################################################################################

import json
import datetime
import math
import matplotlib.pyplot as plt

def average(lst): 
    """
    calculate average for a list of numbers
    """
    return sum(lst) / len(lst) 

def num(x, width=8): 
    """
    format a number for display
    """
    if x is None : return width * ' '
    n = int(round(x,0))
    if n == 0 and x > 0 :
        s = width * ' ' + '< 0.5'
    else :
        s = width * ' ' + f"{n:,}"
    return s[-width:] 

json_data = None        # string with json data downloaded from web site
region_name = {}        # dictionary of geoIds available in the data

# global settings
ylog_setting = 1        # global default Y axis setting
days_setting = 14       # number of days data to show
predict_setting = 10    # number of days prediction to show
ylog_setting = 1        # log or linear Y axis
daily_setting = 1       # plot daily new cases / new deaths
infection_setting = 1   # plot infection rate
totals_setting = 0      # plot cumulative cases / deaths
smooth_setting = 9      # number of days to use when smoothing data
growth_setting = 40     # number of days when virus spread before peak
lag_setting = 4         # days lag between peak cases and peak deaths
spread_setting = 7      # number of days to use look back when calculating infection rate
dilation_setting = 2    # dilation to apply to deaths
d_cases_setting = 0     # dilation to apply to cases
figwidth_setting = 12   # width for plots
debug_setting = 0       # debug setting

def data_load(days=None, predict=None, ylog=None, daily=None, infection=None, totals=None, smooth=None, growth_days=None, lag=None
    , spread=None, dilation=None, d_cases=None, figwidth=None, find=None, debug=0) :
    """
    load json data file and build dictionary of region names 
    """
    # configure any global settings
    global days_setting, predict_setting, ylog_setting, daily_setting, infection_setting, totals_setting
    global smooth_setting, growth_setting, lag_setting, spread_setting, dilation_setting, d_cases_setting
    global figwidth_setting, debug_setting
    if days is not None : days_setting = days
    if predict is not None : predict_setting = predict
    if ylog is not None : ylog_setting = ylog
    if daily is not None : daily_setting = daily
    if infection is not None : infection_setting = infection
    if totals is not None : totals_setting = totals
    if smooth is not None : smooth_setting = smooth
    if growth_days is not None : growth_setting = growth_days
    if lag is not None : lag_setting = lag
    if spread is not None : spread_setting = spread
    if dilation is not None : dilation_setting = dilation
    if d_cases is not None : d_cases_setting = d_cases
    if figwidth is not None : figwidth_setting = figwidth
    if debug is not None : debug_setting = debug
    # clean up any problems in the download file and load string into buffer
    global json_data
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
    if debug > 0 : print(f"{n:,} lines read from download.json")
    # build dictionary of the regions available
    for r in json.loads(json_data).get('records') :
        id = r.get('geoId')
        if id not in region_name.keys() :
            region_name[id] = r.get('countriesAndTerritories').replace('_', ' ')
    print(f"{len(region_name.keys())} region(s) found")
    # find region?
    if find is not None :
        n = 0
        if debug > 0 : print()
        for id in region_name.keys() : 
            if find.lower() in region_name[id].lower() :
                print(f"{id} : {region_name[id]}")
                n += 1
        print(f"\n{n} region(s) containing '{find}' found in download.json")
    return

def load(geoId='UK') :
    """
    load data and return 
    """
    global json_data
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
    Load the data about a region
    """    
    def __init__(self, geoId='UK', smooth=None, growth_days=None, lag=None, spread=None, dilation=None, d_cases=0, figwidth=None, debug=None) :
        # process parameters
        global smooth_setting, growth_setting, lag_setting, spread_setting, dilation_setting, d_cases_setting, figwidth_setting, debug_setting
        self.debug = debug if debug is not None else debug_setting
        global region_name
        if region_name.get(geoId) is None :
            print(f"Region not recognised: {geoId}\n")
            return
        self.geoId = geoId
        self.name = region_name.get(geoId)
        if self.debug > 0 : print(f"Region {self.geoId} = {self.name}")
        self.smooth = smooth if smooth is not None else smooth_setting
        if self.smooth % 2 == 0 : self.smooth += 1      # make sure the average is balanced around the centre point
        self.growth_days = growth_days if growth_days is not None else growth_setting
        self.lag = lag if lag is not None else lag_setting
        self.spread = spread if spread is not None else spread_setting
        self.dilation_deaths = dilation if dilation is not None else dilation_setting
        self.dilation_cases = d_cases if d_cases != 0 else dilation
        if self.dilation_cases is None :
            self.dilation_cases = d_cases_setting if d_cases_setting != 0 else dilation_setting
        self.figwidth = figwidth if figwidth is not None else figwidth_setting
        self.figsize = (self.figwidth, self.figwidth * 9 / 16)     # size of charts
        # load data
        self.data = load(geoId)
        # check we have some data to work on
        if len(self.data) == 0 :
            print(f"no records available for geoId {self.geoId}")
            return
        self.count = len(self.data)
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
        if self.s_peak_case_days is None :
            self.s_peak_case_days = self.s_start_days + self.growth_days
            self.s_peak_cases = self.s_start + datetime.timedelta(self.growth_days)
        elif self.s_peak_case_days >= self.s_latest_days and self.s_peak_case_days - self.s_start_days < self.growth_days:
            self.s_peak_case_days = self.s_start_days + self.growth_days
            self.s_peak_cases = self.s_start + datetime.timedelta(self.growth_days)
        else :
            # update growth days with actual
            self.growth_days = self.s_peak_case_days - self.s_start_days
        if self.debug > 0 :
            print(f"> peak cases: {int(peak):,} on {self.s_peak_cases:%Y-%m-%d} {self.s_peak_case_days+1} days")
        # calculate symmetrical cycle time as start to peak time
        self.cycle = 2 * (self.s_peak_case_days - self.s_start_days)
        # calculate notional end day from cycle time, factored for dilation effect
        t_decay = 1
        if self.dilation_cases > 1 :
            if self.dilation_cases < 2 : t_decay = self.dilation_cases
            else : t_decay = 2
        self.s_end_days = self.s_start_days + int(self.cycle * (1 + t_decay) / 2)
        self.s_end = self.latest + datetime.timedelta(self.s_end_days)
        # find peak deaths, starting just before peak cases to avoid early false peaks
        peak = 0
        for i in range(self.s_peak_case_days - self.lag, self.s_latest_days) :
            if i > self.s_end_days : break      # avoid false reporting / second peaks  i.e. china
            if self.data[i].get('s_deaths') is None : continue
            if self.data[i].get('s_deaths') > peak :
                peak = self.data[i].get('s_deaths')
                self.s_peak_deaths = self.data[i].get('dateRep')
                self.s_peak_death_days = i
        # check if peak deaths was found. Estimate day using lag if not
        if self.s_peak_death_days is None :
            # not found, use lag
            self.s_peak_death_days = self.s_peak_case_days + self.lag
            self.s_peak_deaths = self.s_peak_cases + datetime.timedelta(self.lag)
        elif self.s_peak_death_days >= self.s_peak_case_days and self.s_peak_death_days >= self.s_latest_days and self.s_peak_death_days - self.s_peak_case_days < self.lag:
            # avoid false peak when it is the latest data point and falls inside the estimated lag. Push out to lag
            self.s_peak_death_days = self.s_peak_case_days + self.lag
            self.s_peak_deaths = self.s_peak_cases + datetime.timedelta(self.lag)
        else :
            # found peak, update lag with actual
            self.lag = self.s_peak_death_days - self.s_peak_case_days
        if self.debug > 0 :
            print(f"> peak deaths: {int(peak):,} on {self.s_peak_deaths:%Y-%m-%d} {self.s_peak_death_days+1} days")
        # build prediction curves using bell distribution / sigmoid population curves
        self.build_curves()
        return

    def report(self) :
        """
        report key statistics from the data to date
        """
        print(f"{self.name} data to end of {self.latest:%Y-%m-%d}:")
        print(f"  {self.total_cases:,} cases, {self.total_deaths:,} deaths")
        print(f"  {self.case_rate:,} cases per million, {self.death_rate:,} deaths per million (2018 population = {self.population:,})")
        print()
        print(f"Timeline: (-ve days are past, +ve days are predicted)")
        # Add 1 to zero based indexes
        print(f"  Start:       {self.s_start:%Y-%m-%d} ({self.s_start_days+1:3} days, when 50 or more cases were reported)")
        print(f"  Peak Cases:  {self.s_peak_cases:%Y-%m-%d} ({self.s_peak_case_days+1:3} days)")
        print(f"  End:         {self.s_end:%Y-%m-%d} ({self.s_end_days+1:3} days, {self.s_end_days - self.s_peak_case_days} days after peak cases)")
        if self.s_total_deaths >= 50 :
            print(f"  Day Zero:    {self.s_day0:%Y-%m-%d} ({self.s_day0_days+1:3} days, when 50 or more deaths were reported)")
            print(f"  Peak Deaths: {self.s_peak_deaths:%Y-%m-%d} ({self.s_peak_death_days+1:3} days)")
        print()
        print(f"Parameters:")
        print(f"  Totals:      {self.data[self.s_latest_days].get('cases_to_date'):,} cases and {self.data[self.s_latest_days].get('deaths_to_date'):,} deaths at end of {self.s_latest:%Y-%m-%d}")
        print(f"  Smoothed:    {int(self.s_total_cases):,} cases and {int(self.s_total_deaths):,} deaths at end of {self.s_latest:%Y-%m-%d} ({self.smooth} points)")
        print(f"  Spread:      Peak infection rate {self.s_r0_peak} ({self.s_r0_peak_date:%Y-%m-%d}, compared to {self.spread} days earlier)")
        print(f"               Latest infection rate {self.s_r0_latest} ({self.s_r0_latest_date:%Y-%m-%d}, compared to {self.spread} days earlier)")
        print(f"  Growth:      {self.growth_days} days (Start -> Peak Cases) ")
        print(f"               L = {int(self.L_cases):,}, r = {round(self.r_cases,2)}, dilation = {self.dilation_cases} for cases")
        if self.s_total_deaths >= 50 :
            print(f"  Lag:         {self.lag} days (Peak Cases -> Peak Deaths) ")
            print(f"               L = {int(self.L_deaths):,}, r = {round(self.r_deaths,2)}, dilation = {self.dilation_deaths} for deaths")
        print()
        if self.s_end_days < 0 :
            d = self.s_end_days
            cases = int(self.data[d].get('cases_to_date'))
            cases_rate = int(round(cases * 1000000 / self.population, 0))
            deaths = int(self.data[d].get('deaths_to_date'))
            death_rate = int(round(deaths * 1000000 / self.population, 0))
            print(f"Outcome: {cases:,} cases, {deaths:,} deaths at end of {self.data[d].get('dateRep'):%Y-%m-%d}")
            print(f"  {cases_rate:,} cases per million, {death_rate:,} deaths per million (2018 population = {self.population:,})")
        else :
            cases = int(self.sigmoid_cases[-1])
            cases_rate = int(round(cases * 1000000 / self.population, 0))
            deaths = int(self.sigmoid_deaths[-1])
            death_rate = int(round(deaths * 1000000 / self.population, 0))
            print(f"Outcome: {cases:,} cases, {deaths:,} deaths at end of {self.s_end:%Y-%m-%d}")
            print(f"  {cases_rate:,} cases per million, {death_rate:,} deaths per million (2018 population = {self.population:,})")
        print()
        return
    
    def show(self, days=days_setting) :
        """
        show records for last number of days
        """
        print()
        print(f"              Raw ----------     Total --------     Smoothed ------   Total ---------")
        print(f"Date          Cases   Deaths     Cases   Deaths     Cases   Deaths     Cases   Deaths")
        for r in self.data[-1 * days:] :
            print(f"{r.get('dateRep'):%Y-%m-%d} {num(r.get('cases'))} {num(r.get('deaths'))} " + \
                  f" {num(r.get('cases_to_date'))} {num(r.get('deaths_to_date'))} " + \
                  f" {num(r.get('s_cases'))} {num(r.get('s_deaths'))} " + \
                  f" {num(r.get('s_cases_to_date'))} {num(r.get('s_deaths_to_date'))} ")
        print()
        return

    def plot(self, ylog=ylog_setting, daily=daily_setting, infection=infection_setting, totals=totals_setting, clip=12) :
        """
        plot the graph of a property against the day reported
        """
        days = self.s_start_days
        dates = [r.get('dateRep') for r in self.data[days:]]
        date_range = [self.s_start + datetime.timedelta(d) for d in range(0, max(len(self.data[days:]), len(self.bell_cases)),7)]
        # plot daily data
        if daily == 1 :
            plt.figure(figsize=self.figsize)
            if ylog==1 :
                plt.yscale('log')
                plt.title(f"{self.name} (log Y axis)\nNew Cases (green=raw, blue=smoothed)\nNew Deaths (orange=raw, red=smoothed)")
            else :
                plt.title(f"{self.name}\nNew Cases (green=raw, blue=smoothed)\nNew Deaths (orange=raw, red=smoothed)")
            plt.plot(dates, [r.get('s_cases') for r in self.data[days:]], color='blue', linestyle='solid')
            plt.plot(dates, [r.get('s_deaths') for r in self.data[days:]], color='red', linestyle='solid')
            plt.plot(dates, [r.get('cases') for r in self.data[days:]], color='green', linestyle='dotted')
            plt.plot(dates, [r.get('deaths') for r in self.data[days:]], color='orange', linestyle='dotted')
            plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
            plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.bell_cases))], self.bell_cases, color='grey', linestyle='dashed')
            if self.s_total_deaths >= 50 : 
                plt.axvline(self.s_day0, color='tan', linestyle='dashed', linewidth=2, label='day0')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.bell_deaths))], self.bell_deaths, color='grey', linestyle='dashed')
                plt.axvline(self.s_peak_deaths, color='tan', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_peak_cases, color='grey', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_end, color='grey', linestyle='dashed', linewidth=2, label='end')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.grid()
            plt.xticks(date_range, rotation=90)
            plt.show()
            print()
        # plot infection rate
        if infection == 1 :
            plt.figure(figsize=self.figsize)
            plt.title(f"{self.name} \nInfection Rate, based on number of new cases compared to {self.spread} days earlier")
            plt.plot(dates, [r.get('s_r0') for r in self.data[days:]], color='brown', linestyle='solid')
            plt.axhline(y=1, color='green', linestyle='dashed', linewidth=2, label='1')
            if self.s_r0_peak > clip : plt.ylim([0, clip])
            else : plt.ylim([0, 4 * (int(self.s_r0_peak / 4) + 1)])
            plt.xticks([self.s_start + datetime.timedelta(d) for d in range(0, len(self.bell_cases),7)], rotation=90)
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
            if self.s_total_deaths >= 50 : 
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
            if ylog==1 :
                plt.yscale('log')
                plt.title(f"{self.name} (log Y axis)\nTotal Cases (green=raw, blue=smoothed)\nTotal Deaths (orange=raw, red=smoothed)")
            else :
                plt.title(f"{self.geoId}\nTotal Cases (green=raw, blue=smoothed)\nTotal Deaths (orange=raw, red=smoothed)")
            plt.plot(dates, [r.get('s_cases_to_date') for r in self.data[days:]], color='blue', linestyle='solid')
            plt.plot(dates, [r.get('s_deaths_to_date') for r in self.data[days:]], color='red', linestyle='solid')
            plt.plot(dates, [r.get('cases_to_date') for r in self.data[days:]], color='green', linestyle='dotted')
            plt.plot(dates, [r.get('deaths_to_date') for r in self.data[days:]], color='orange', linestyle='dotted')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
            plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_cases))], self.sigmoid_cases, color='grey', linestyle='dashed')
            plt.xticks([self.s_start + datetime.timedelta(d) for d in range(0, len(self.bell_cases),7)], rotation=90)
            if self.s_total_deaths >= 50 : 
                plt.axvline(self.s_day0, color='tan', linestyle='dashed', linewidth=2, label='day0')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_deaths))], self.sigmoid_deaths, color='grey', linestyle='dashed')
                plt.axvline(self.s_peak_deaths, color='tan', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_peak_cases, color='grey', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.s_end, color='grey', linestyle='dashed', linewidth=2, label='end')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.grid()
            plt.xticks(date_range, rotation=90)
            plt.show()
            print()
        return

    def t (self, day, offset) :
        """
        return the scaled time from the day in the infection cycle, between t=-1 (s_start_days) to t=+1 (s_end_days)
        dilation controls the symmetry of the distribution by manipulating time when t > 0.
        """
        if offset == 1 :
            lag = self.lag
            dilation = self.dilation_deaths
        else :
            lag = 0
            dilation = self.dilation_cases
        x = 2 * (day - self.s_start_days - lag) - self.cycle
        if x > 0 and dilation != 1 : x /= dilation
        return x / self.cycle

    def bell_A(self, L, r, d, offset) :
        """
        return a point in the scaled bell distribution using the derritative of the sigmoid function 
        """
        x = self.t(d, offset)
        A = L * math.exp(-1 * r * x) / (1 + math.exp(-1 * r * x)) ** 2
        return A

    def bell_L(self, A, r, d, offset) :
        """
        given a point in the bell distribution, work out the scale factor L
        """
        x = self.t(d, offset)
        L = A * (1 + math.exp(-1 * r * x)) ** 2 / math.exp(-1 * r * x)
        return L

    def abs_error(self, L, r, offset) :
        """
        calculate the average absolute error between the smoothed data and bell distribution for a given L and r:
        """
        name = 's_cases' if offset == 0 else 's_deaths'
        n = 0
        result = 0
        d = self.s_start_days
        if self.s_end_days < self.s_latest_days : d2 = self.s_end_days
        else : d2 = self.s_latest_days
        while d <= d2 : 
            if self.data[d].get(name) is not None :
                result += abs(self.data[d].get(name) - self.bell_A(L, r, d, offset))
                n += 1
            d += 1
        if n == 0 : return None
        else : return result / n

    def bell_r(self, L, r, offset, tries=0) :
        """
        work out the best value for r
        """
        cases = 'Cases' if offset == 0 else 'Deaths'
        n = 16
        step = 2.0
        while step > 0.01 and n > 0 :
            # get errors ordered by r is lower, same, higher
            error = [self.abs_error(L, r - step, offset), self.abs_error(L, r, offset), self.abs_error(L, r + step, offset)]
            if self.debug > 1 : print(f"r={r}, step={step}, error = {error}")
            direction = error.index(min(error)) - 1     # direction of lowest error is -1, 0, +1 steps
            r += direction * step
            if direction == 0 : step /= 2
            # limit stops to prevent run-away
            if r < 4.0 : r = 4.0
            if r > 8.0 : r = 8.0
            n -= 1
        if self.debug > 0 : print(f"> {cases} {tries}: L = {int(L):,}, r = {round(r, 2)}")
        return r

    def fit_cases(self, day) :
        # fit L_cases and r_cases to the smoothed data
        previous_L = 0.0
        previous_r = 0.0
        tries = 0
        if self.r_cases is None : self.r_cases = 6
        while tries < 10 :
            self.L_cases = self.bell_L(self.data[day].get('s_cases'), self.r_cases, day, 0)
            self.r_cases = self.bell_r(self.L_cases, self.r_cases, 0, tries)
            if int(self.L_cases) == previous_L and round(self.r_cases, 2) == previous_r : break
            previous_L = int(self.L_cases)
            previous_r = round(self.r_cases,2)
            tries += 1
        if tries >= 20 : print(f"** fit_cases was not solved")
        return
        
    def fit_deaths(self, day) :
        # fit L_deaths and r_deaths to smoothed data
        previous_L = 0.0
        previous_r = 0.0
        tries = 0
        if self.r_deaths is None : self.r_deaths = 6
        while tries < 10 :
            self.L_deaths = self.bell_L(self.data[day].get('s_deaths'), self.r_deaths, day, 1)
            self.r_deaths = self.bell_r(self.L_deaths, self.r_deaths, 1, tries)
            if int(self.L_deaths) == previous_L and round(self.r_deaths, 2) == previous_r : break
            previous_L = int(self.L_deaths)
            previous_r = round(self.r_deaths, 2)
            tries += 1
        if tries >= 20 : print(f"** fit_deaths was not solved")
        return

    def build_curves(self) :
        """
        Build a bell distribution curve model for the smoothed number of new cases / deaths.
        This is the derrivative of the sigmoid population function A = L / (1 + exp(-rt))
        A = L * exp(-rt) / (1 + exp(-rt)) ** 2
        """
        self.bell_cases = []
        self.sigmoid_cases = []
        self.bell_deaths = []
        self.sigmoid_deaths = []
        self.L_cases = None             # scale factor for cases
        self.r_cases = None             # r factor for cases
        self.L_deaths = None            # scale factor for deaths
        self.r_deaths = None            # r factor for deaths
        if self.s_peak_case_days < self.s_latest_days : d = self.s_peak_case_days
        else : d = self.s_latest_days
        self.fit_cases(d)
        if self.s_peak_death_days < self.s_latest_days : d = self.s_peak_death_days
        else : d = self.s_latest_days
        self.fit_deaths(d)
        # generate data points, starting with point -1 so we can get a delta for new cases / deaths
        cases = []
        cases_to_date = 0
        deaths = []
        deaths_to_date = 0
        for d in range(self.s_start_days, self.s_end_days) :
            cases.append(self.bell_A(self.L_cases, self.r_cases, d, 0))
            deaths.append(self.bell_A(self.L_deaths, self.r_deaths, d, 1))
            if d <= self.s_latest_days :
                cases_to_date += cases[-1]
                deaths_to_date += deaths[-1]
        cases_rescale = self.s_total_cases / cases_to_date
        if self.debug > 0 : print(f"cases_rescale = {cases_rescale}")
        deaths_rescale = self.s_total_deaths / deaths_to_date
        if self.debug > 0 : print(f"deaths_rescale = {deaths_rescale}")
        cases_to_date = 0
        deaths_to_date = 0
        for d in range(0, self.s_end_days - self.s_start_days) :
            self.bell_cases.append(cases[d] * cases_rescale)
            self.bell_deaths.append(deaths[d] * deaths_rescale)
            cases_to_date += self.bell_cases[-1]
            deaths_to_date += self.bell_deaths[-1]
            self.sigmoid_cases.append(cases_to_date)
            self.sigmoid_deaths.append(deaths_to_date)
        return

    def prediction(self, predict=predict_setting, start=0) :
        """
        use the bell curves to predict future cases / deaths
        """
        if self.s_end_days < 1 : return
        if predict == 0 : predict = int(self.smooth/2) + 1
        if predict < 1 : return
        print()
        print(f"              Prediction ---    Total -------")
        print(f"Date          Cases   Deaths    Cases  Deaths")
        for d in range(start, predict) :
            i = self.s_latest_days - self.s_start_days + d
            if i >= len(self.bell_cases) : break
            print(f"{self.s_latest + datetime.timedelta(d):%Y-%m-%d}" + \
                  f" {num(self.bell_cases[i])} {num(self.bell_deaths[i])}" + \
                  f" {num(self.sigmoid_cases[i])} {num(self.sigmoid_deaths[i])}")
        print()
        return

    def analyse(self, days=days_setting, predict=predict_setting, ylog=ylog_setting, daily=daily_setting, infection=infection_setting, totals=totals_setting) :
        self.report()
        self.plot(ylog=ylog, daily=daily, infection=infection, totals=totals)
        self.show(days=days)
        self.prediction(predict=predict)
        return
