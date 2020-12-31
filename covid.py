##################################################################################################
"""
Module:   Covid data analysis
Date:     01 May 2020
Author:   Tony Matthews
"""
##################################################################################################

##################################################################################################
# Model Parameters
# geoId:       2 letter code for the region.
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
# Process Parameters
# days:        Number of days of raw / smoothed data to show
# predict:     Number of days of predicted data to show
# ylog:        Plot cases / death charts using logarithmic Y axis
# daily:       Plot graph showing new cases / new deaths
# infection:   Plot graph showing infection rate
# totals:      Plot graph showing total cases / total deaths
##################################################################################################

import json
import datetime
import math
import matplotlib.pyplot as plt

def average(lst): 
    """
    calculate average of a list (of numbers)
    """
    return sum(lst) / len(lst) 

def num(x, width=8): 
    """
    format a number for display in a data table
    """
    if x is None :
        if width == 0 : return '---'
        else : return width * ' '
    n = int(round(x,0))
    if n == 0 and x > 0 :
        s = width * ' ' + '< 0.5'
    else :
        s = width * ' ' + f"{n:,}"
    return s if width==0 else s[-width:]

json_data = None        # string with json data downloaded from web site
region_name = {}        # dictionary of geoIds available in the data

# global settings
ylog_setting = 1        # global default Y axis setting
days_setting = 14       # number of days data to show
predict_setting = 10    # number of days prediction to show
ylog_setting = 1        # log or linear Y axis
daily_setting = 1       # plot daily new cases / new deaths. 0 = no, 1 = yes, 2 = linear, 3 = log
infection_setting = 1   # plot infection rate. 0 = no, 1 = yes
totals_setting = 0      # plot cumulative cases / deaths. 0 = no, 1 = yes, 2 = linear, 3 = log, 4 = deaths only
smooth_setting = 3      # number of days to use when smoothing data
growth_setting = 40     # number of days when virus spread before peak
lag_setting = 4         # days lag between peak cases and peak deaths
spread_setting = 7      # number of days to use look back when calculating infection rate
dilation_setting = 1    # dilation to apply to deaths (1 = Normal, 2 = slower fall, 0.8 = faster fall)
d_cases_setting = 0     # dilation to apply to cases
d_clip_setting = 2      # clip setting for dilation applied to time
clip_setting = 10       # max Y value displayed on infection rate plot
figwidth_setting = 12   # width for plots
debug_setting = 0       # debug setting: 0 = silent, 1 = info, 2 = details

def setting(days=None, predict=None, ylog=None, daily=None, infection=None, totals=None, smooth=None, growth_days=None, lag=None
    , spread=None, dilation=None, d_cases=None, d_clip=None, clip=None, figwidth=None, debug=0) :
    """
    configure global settings 
    """
    # configure any global settings
    global days_setting, predict_setting, ylog_setting, daily_setting, infection_setting, totals_setting
    global smooth_setting, growth_setting, lag_setting, spread_setting, dilation_setting, d_cases_setting
    global d_clip_setting, clip_setting, figwidth_setting, debug_setting
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
    if d_clip is not None : d_clip_setting = d_clip
    if clip is not None : clip_setting = clip
    if figwidth is not None : figwidth_setting = figwidth
    if debug is not None : debug_setting = debug
    return

def data_load(fn, find=None, debug=None) :
    """
    load json data file fn and build dictionary of region names 
    """
    # clean up any problems in the download file and load buffer
    global json_data, region_name, debug_setting
    if debug is None : debug = debug_setting
    n=0
    s = ''
    f = open(fn, 'r' )
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
    if debug > 1 : print(f"{n:,} lines read from {fn}")
    # build dictionary of the region names
    region_name = {}
    for r in json.loads(json_data).get('records') :
        id = r.get('geoId')
        if id not in region_name.keys() :
            region_name[id] = r.get('countriesAndTerritories').replace('_', ' ')
    if debug > 0 : print(f"{len(region_name.keys())} region(s) found in {fn}")
    # find region?
    if find is not None and len(region_name) > 0 :
        n = 0
        if debug > 0 : print()
        for id in region_name.keys() : 
            if find.lower() in region_name[id].lower() :
                print(f"{id} : {region_name[id]}")
                n += 1
        print(f"\n{n} region(s) containing '{find}' found in {fn}")
    return

def region_load(fn=None, geoId=None, debug=None, population=None, density=None) :
    """
    load json data for a region. fn and geoId are optional 
    """
    global json_data, region_name, debug_setting
    if debug is None : debug = debug_setting
    if fn is not None : data_load(fn, debug=debug)
    if geoId is None and len(region_name) > 0 : geoId = list(region_name.keys())[0]
    if geoId is None or region_name.get(geoId) is None : return
    # get the records for the region
    data = [r for r in json.loads(json_data).get('records') if r.get('geoId') == geoId]
    # convert data for each record
    for r in data :
        r['dateRep'] = datetime.datetime.strptime(r.get('dateRep'), "%d/%m/%Y")
        r['cases_weekly'] = int(r.get('cases_weekly'))
        r['deaths_weekly'] = int(r.get('deaths_weekly'))
        r['population'] = int(r.get('popData2019')) if population is None else population
        r['density'] = density
    # ECDC reports data weekly instead of daily as of 17/12/2020. Add previous 6 missing days back in for each record
    for i in range(0, len(data)) :
        # track number of cases / deaths added in previous records
        cases_added = 0
        deaths_added = 0
        for j in range(0,6):
            r = {}
            r['dateRep'] = data[i].get('dateRep') - datetime.timedelta(j+1)
            r['cases'] = int(data[i].get('cases_weekly') / 7)
            r['deaths'] = int(data[i].get('deaths_weekly') / 7)
            r['population'] = data[i].get('popData2019')
            r['density'] = data[i].get('density')
            data.append(r)
            cases_added += r['cases']
            deaths_added += r['deaths']
        # ensure weekly total is correct by subtracting what we added
        data[i]['cases'] = data[i].get('cases_weekly') - cases_added
        data[i]['deaths'] = data[i].get('deaths_weekly') - deaths_added
    # sort records so they are all in ascending date order
    data = sorted(data, key = lambda r: r.get('dateRep'))
    # calculate cumulative data
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
    def __init__(self, fn=None, geoId=None, smooth=None, growth_days=None, lag=None, spread=None, dilation=None, d_cases=0, d_clip=None, population=None, density=None, figwidth=None, debug=None) :
        # process parameters
        global smooth_setting, growth_setting, lag_setting, spread_setting, dilation_setting, d_cases_setting, d_clip_setting, figwidth_setting, debug_setting
        self.debug = debug if debug is not None else debug_setting
        self.smooth = smooth if smooth is not None else smooth_setting
        if self.smooth % 2 == 0 : self.smooth += 1      # make sure the average is balanced around the centre point
        self.growth_days = growth_days if growth_days is not None else growth_setting
        self.lag = lag if lag is not None else lag_setting
        self.spread = spread if spread is not None else spread_setting
        self.dilation_deaths = dilation if dilation is not None else dilation_setting
        self.dilation_cases = d_cases if d_cases != 0 else dilation
        if self.dilation_cases is None :
            self.dilation_cases = d_cases_setting if d_cases_setting != 0 else dilation_setting
        self.d_clip = d_clip if d_clip is not None else d_clip_setting
        self.figwidth = figwidth if figwidth is not None else figwidth_setting
        self.figsize = (self.figwidth, self.figwidth * 9 / 16)     # size of charts
        # load data
        global region_name
        self.data = region_load(fn, geoId, self.debug, population, density)
        if geoId is None and len(region_name) > 0 : geoId = list(region_name.keys())[0]
        if geoId is None or region_name.get(geoId) is None :
            print(f"Region not recognised: '{geoId}'\n")
            return
        self.geoId = geoId
        self.name = region_name.get(geoId)
        if self.debug > 0 : print(f"Region {self.geoId} = {self.name}")
        # check we have some data to work on
        if len(self.data) == 0 :
            print(f"no records available for geoId {self.geoId}")
            return
        self.count = len(self.data)
        self.latest = self.data[-1].get('dateRep')                                          # date when last data was provided
        self.total_cases = self.data[-1].get('cases_to_date')                               # total number of cases reported
        self.total_deaths = self.data[-1].get('deaths_to_date')                             # total number of deaths reported
        self.population = self.data[-1].get('population')                                   # region population
        self.density = self.data[-1].get('density')                                         # region population density (people / km2)
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
        case_rescale = self.data[self.s_latest_days].get('cases_to_date') / self.s_total_cases if self.s_total_cases > 0 else 1
        death_rescale = self.data[self.s_latest_days].get('deaths_to_date') / self.s_total_deaths if self.s_total_deaths > 0 else 1
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
        self.s_infection_peak = 0              # peak value for infection rate
        self.s_infection_peak_date = None      # date when infection rate peaks
        self.s_infection_peak_days = None      # index for day when infection rate peaks
        self.s_infection_latest = 0            # latest value for infection rate
        self.s_infection_latest_date = None    # date of latest infection rate
        self.s_infection_latest_days = None    # index for latest infection rate
        peak = 0
        for i in range(0,len(self.data)) :
            self.data[i]['s_cases_to_date'] = None
            self.data[i]['s_deaths_to_date'] = None
            self.data[i]['s_infection'] = None
            if self.data[i].get('s_cases') is None : continue
            # rescale smoothed data and update
            self.data[i]['s_cases'] *= case_rescale
            self.data[i]['s_deaths'] *= death_rescale
            self.s_total_cases += self.data[i]['s_cases']
            self.s_total_deaths += self.data[i]['s_deaths']
            self.data[i]['s_cases_to_date'] = self.s_total_cases
            self.data[i]['s_deaths_to_date'] = self.s_total_deaths
            if i >= self.spread and self.s_total_cases >= 500 and self.data[i].get('s_cases') is not None and self.data[i - self.spread].get('s_cases') is not None and self.data[i - self.spread].get('s_cases') != 0:
                # calculate infection rate
                self.data[i]['s_infection'] = self.data[i].get('s_cases') / self.data[i - self.spread].get('s_cases')
                self.s_infection_latest = self.data[i].get('s_infection')
                self.s_infection_latest_days = i - self.count
                self.s_infection_latest_date = self.data[i].get('dateRep')
                if self.data[i].get('s_infection') > self.s_infection_peak :
                    self.s_infection_peak = self.data[i].get('s_infection')
                    self.s_infection_peak_days = i - self.count
                    self.s_infection_peak_date = self.data[i].get('dateRep')
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
            if self.dilation_cases < self.d_clip : t_decay = self.dilation_cases
            else : t_decay = self.d_clip
        self.s_end_days = self.s_start_days + int(self.cycle * (1 + t_decay) / 2)
        self.s_end = self.latest + datetime.timedelta(self.s_end_days)
        self.position = (self.s_latest_days - self.s_start_days) / (self.s_end_days - self.s_start_days)
        # find peak deaths, starting just before peak cases to avoid early false peaks
        peak = 0
        for i in range(self.s_start_days - self.lag, self.s_latest_days + 1) :
            if i > self.s_end_days : break      # avoid shifting to second peaks  i.e. china
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
        print(f"  {self.case_rate:,} cases per million, {self.death_rate:,} deaths per million (2019 population = {self.population:,})")
        print()
        print(f"Timeline: (-ve days are past, +ve days are predicted)")
        if self.s_end_days >= 0 :
            print(f"  Now:         {round(self.position,2):2.0%} through outbreak")
        else :
            print(f"  Now:         past end of first outbreak")
        # Add 1 to zero based indexes for relative day number
        print(f"  Start:       {self.s_start:%Y-%m-%d} ({self.s_start_days+1:3} days, when 50 or more cases were reported)")
        print(f"  Peak Cases:  {self.s_peak_cases:%Y-%m-%d} ({self.s_peak_case_days+1:3} days, {num(self.data[self.s_peak_case_days].get('s_cases'),0)} cases)")
        print(f"  End:         {self.s_end:%Y-%m-%d} ({self.s_end_days+1:3} days, {self.s_end_days - self.s_peak_case_days} days after peak cases)")
        if self.s_total_deaths >= 50 :
            print(f"  Day Zero:    {self.s_day0:%Y-%m-%d} ({self.s_day0_days+1:3} days, when 50 or more deaths were reported)")
            if self.s_peak_death_days < 0 :
                print(f"  Peak Deaths: {self.s_peak_deaths:%Y-%m-%d} ({self.s_peak_death_days+1:3} days, {num(self.data[self.s_peak_death_days].get('s_deaths'),0)} deaths)")
            else :
                print(f"  Peak Deaths: {self.s_peak_deaths:%Y-%m-%d} ({self.s_peak_death_days+1:3} days)")
        print()
        print(f"Parameters:")
        print(f"  Totals:      {self.data[self.s_latest_days].get('cases_to_date'):,} cases and {self.data[self.s_latest_days].get('deaths_to_date'):,} deaths at end of {self.s_latest:%Y-%m-%d}")
        print(f"  Smoothed:    {int(self.s_total_cases):,} cases and {int(self.s_total_deaths):,} deaths at end of {self.s_latest:%Y-%m-%d} ({self.smooth} points)")
        print(f"  Spread:      Peak infection rate {round(self.s_infection_peak,1)} ({self.s_infection_peak_date:%Y-%m-%d}, compared to {self.spread} days earlier)")
        print(f"               Latest infection rate {round(self.s_infection_latest,1)} ({self.s_infection_latest_date:%Y-%m-%d}, compared to {self.spread} days earlier)")
        print(f"  Growth:      {self.growth_days} days (Start -> Peak Cases) ")
        print(f"               X = {int(self.X_cases):,}, r = {round(self.r_cases,2)}, L = {int(self.L_cases):,}, dilation = {self.dilation_cases}, c = {self.C_cases:5.1%} for cases")
        if self.s_total_deaths >= 50 :
            print(f"  Lag:         {self.lag} days (Peak Cases -> Peak Deaths) ")
            print(f"               X = {int(self.X_deaths):,}, r = {round(self.r_deaths,2)}, L = {int(self.L_deaths):,}, dilation = {self.dilation_deaths}, c = {self.C_deaths:5.1%} for deaths")
        print()
        if self.s_end_days < 0 :
            d = self.s_end_days
            total_cases = int(self.data[d].get('cases_to_date'))
            cases_rate = int(round(total_cases * 1000000 / self.population, 0))
            total_deaths = int(self.data[d].get('deaths_to_date'))
            death_rate = int(round(total_deaths * 1000000 / self.population, 0))
            print(f"Outcome: {total_cases:,} total cases, {total_deaths:,} total deaths at end of {self.data[d].get('dateRep'):%Y-%m-%d}")
            print(f"  {cases_rate:,} cases per million ({cases_rate/1000000:5.2%}), {death_rate:,} deaths per million ({death_rate/1000000:5.3%})")
            if self.density is not None :
                print(f"  {round(cases_rate / self.density, 1)} cases km2, {round(death_rate / self.density, 1)} deaths km2")
            print(f"  ** first wave ended **")
        else :
            total_cases = int(self.sigmoid_cases[-1])
            cases_rate = int(round(self.X_cases * 1000000 / self.population, 0))
            total_deaths = int(self.sigmoid_deaths[-1])
            death_rate = int(round(self.X_deaths * 1000000 / self.population, 0))
            print(f"Outcome: {total_cases:,} total cases, {total_deaths:,} total deaths by end of {self.s_end:%Y-%m-%d}")
            print(f"  {self.total_cases / self.X_cases:5.1%} of predicted cases and {self.total_deaths / self.X_deaths:5.1%} of predicted deaths reported to date")
            print(f"  {total_cases / self.X_cases:5.1%} of predicted cases and {total_deaths / self.X_deaths:5.1%} of predicted deaths reported by end date")
            print(f"  {cases_rate:,} cases per million ({cases_rate/1000000:5.2%}), {death_rate:,} deaths per million ({death_rate/1000000:5.3%})")
            if self.density is not None :
                print(f"  {round(cases_rate / self.density, 1)} cases km2, {round(death_rate / self.density, 1)} deaths km2")
        print()
        return
    
    def show(self, days=None) :
        """
        show records for last number of days
        """
        global days_setting, clip_setting
        if days is None : days = days_setting
        print()
        print(f"              Raw ----------       Total --------     Smoothed ------      Total ---------")
        print(f"Date          Cases   Deaths       Cases   Deaths     Cases   Deaths       Cases   Deaths")
        for r in self.data[-1 * days:] :
            print(f"{r.get('dateRep'):%Y-%m-%d} {num(r.get('cases'))} {num(r.get('deaths'))} " + \
                  f" {num(r.get('cases_to_date'), 10)} {num(r.get('deaths_to_date'))} " + \
                  f" {num(r.get('s_cases'))} {num(r.get('s_deaths'))} " + \
                  f" {num(r.get('s_cases_to_date'), 10)} {num(r.get('s_deaths_to_date'))} ")
        print()
        return

    def plot(self, ylog=None, daily=None, infection=None, totals=None, clip=None) :
        """
        plot the graph of a property against the day reported
        """
        global ylog_setting, daily_setting, infection_setting, totals_setting
        if ylog is None : ylog = ylog_setting
        if daily is None : daily = daily_setting
        if infection is None : infection = infection_setting
        if totals is None : totals = totals_setting
        if clip is None : clip = clip_setting
        days = self.s_start_days
        dates = [r.get('dateRep') for r in self.data[days:]]
        date_range = [self.s_start + datetime.timedelta(d) for d in range(0, max(len(self.data[days:]), len(self.bell_cases)),7)]
        # plot daily data
        if daily > 0 :
            plt.figure(figsize=self.figsize)
            if daily == 3 or (ylog==1 and daily==1):
                plt.yscale('log')
                plt.ylim([1, self.L_cases])
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
        if infection > 0 :
            plt.figure(figsize=self.figsize)
            if ylog == 1 and infection != 2:
                plt.title(f"{self.name} (log Y axis) \nInfection Rate, based on number of new cases compared to {self.spread} days earlier\n(dotted line shows the predicted infection rate)")
                plt.yscale('log')
                plt.ylim([0.1,10])
            else :
                plt.title(f"{self.name}\nInfection Rate, based on number of new cases compared to {self.spread} days earlier\n(dotted line shows the predicted infection rate)")
                if self.s_infection_peak > clip : plt.ylim([0, clip])
                else : plt.ylim([0, 4 * (int(self.s_infection_peak / 4) + 1)])
            plt.plot(dates, [r.get('s_infection') for r in self.data[days:]], color='brown', linestyle='solid')
            plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.infection))], self.infection, color='grey', linestyle='dashed')
            plt.axhline(y=1, color='green', linestyle='dashed', linewidth=2, label='1')
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
        # plot totals: 0 = no, 1 = yes, 2 = linear, 3 = log, 4 = deaths only
        if totals > 0 :
            plt.figure(figsize=self.figsize)
            if totals==3 or (ylog==1 and totals==1):
                plt.yscale('log')
                plt.ylim([1, self.X_cases])
                plt.title(f"{self.name} (log Y axis)\nTotal Cases (green=raw, blue=smoothed)\nTotal Deaths (orange=raw, red=smoothed)")
            elif totals==4 :
                plt.title(f"{self.name}\nTotal Deaths (orange=raw, red=smoothed)")
            else :
                plt.title(f"{self.name}\nTotal Cases (green=raw, blue=smoothed)\nTotal Deaths (orange=raw, red=smoothed)")
            if totals != 4 :
                plt.plot(dates, [r.get('s_cases_to_date') for r in self.data[days:]], color='blue', linestyle='solid')
                plt.plot(dates, [r.get('cases_to_date') for r in self.data[days:]], color='green', linestyle='dotted')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_cases))], self.sigmoid_cases, color='grey', linestyle='dashed')
            plt.axvline(self.s_peak_cases, color='grey', linestyle='dashed', linewidth=2, label='peak')
            plt.plot(dates, [r.get('s_deaths_to_date') for r in self.data[days:]], color='red', linestyle='solid')
            plt.plot(dates, [r.get('deaths_to_date') for r in self.data[days:]], color='orange', linestyle='dotted')
            if self.s_total_deaths >= 50 : 
                plt.axvline(self.s_day0, color='tan', linestyle='dashed', linewidth=2, label='day0')
                plt.plot([self.s_start + datetime.timedelta(d) for d in range(0, len(self.sigmoid_deaths))], self.sigmoid_deaths, color='grey', linestyle='dashed')
                plt.axvline(self.s_peak_deaths, color='tan', linestyle='dashed', linewidth=2, label='peak')
            plt.axvline(self.latest, color='green', linestyle='dashed', linewidth=2, label='now')
            plt.axvline(self.s_start, color='grey', linestyle='dashed', linewidth=2, label='start')
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
        calculate the absolute error between the smoothed data and bell distribution for a given L and r:
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
        else : return result

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

    def sigmoid_L(self, A, r, d, offset) :
        """
        given a point in the sigmoid distribution, work out the scale factor L
        """
        x = self.t(d, offset)
        L = A * (1 + math.exp(-1 * r * x))
        return L

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
        self.r_cases = None             # r factor for cases
        self.L_cases = None             # scale factor for cases bell distribution function
        self.X_cases = None             # scale factor for cases sigmoid function
        self.r_deaths = None            # r factor for deaths
        self.L_deaths = None            # scale factor for deaths bell distribution function
        self.X_deaths = None            # scale factor for deaths sigmoid function
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
        for d in range(self.s_start_days, max(self.s_end_days, self.s_latest_days)) :
            cases.append(self.bell_A(self.L_cases, self.r_cases, d, 0))
            deaths.append(self.bell_A(self.L_deaths, self.r_deaths, d, 1))
            if d <= self.s_latest_days :
                cases_to_date += cases[-1]
                deaths_to_date += deaths[-1]
        # work out rescale factors
        d = self.s_end_days if self.s_end_days < self.s_latest_days else self.s_latest_days
        cases_rescale = self.data[d].get('s_cases_to_date') / cases_to_date if cases_to_date > 0 else 1
        if self.debug > 0 : print(f"cases_rescale = {cases_rescale}")
        deaths_rescale = self.data[d].get('s_deaths_to_date') / deaths_to_date if deaths_to_date > 0 else 1
        if self.debug > 0 : print(f"deaths_rescale = {deaths_rescale}")
        # apply scale factors to bell distributions and calculate sigmoid functions
        cases_to_date = 0
        deaths_to_date = 0
        for i in range(0, len(cases)) :
            self.bell_cases.append(cases[i] * cases_rescale)
            self.bell_deaths.append(deaths[i] * deaths_rescale)
            cases_to_date += self.bell_cases[-1]
            deaths_to_date += self.bell_deaths[-1]
            self.sigmoid_cases.append(cases_to_date)
            self.sigmoid_deaths.append(deaths_to_date)
        # work out implied scale factors for sigmoid functions
        self.X_cases = self.sigmoid_L(cases_to_date, self.r_cases, self.s_end_days, 0)
        self.X_deaths = self.sigmoid_L(deaths_to_date, self.r_deaths, self.s_end_days, 1)
        # work out consistency. error between smoothed data and prediction as percentage of 
        self.C_cases = 1.0 - self.abs_error(self.L_cases, self.r_cases, 0) / self.s_total_cases if self.s_total_cases != 0 else None
        self.C_deaths = 1.0 - self.abs_error(self.L_deaths, self.r_deaths, 1) / self.s_total_deaths if self.s_total_deaths !=0 else None
        # work out infection rate curve for cases:
        self.infection = []
        for i in range(0, len(self.sigmoid_cases)) :
            if i >= self.spread and self.bell_cases[i - self.spread] != 0 :
                self.infection.append(self.bell_cases[i] / self.bell_cases[i - self.spread])
            else :
                self.infection.append(None)
        return

    def prediction(self, predict=None, start=0) :
        """
        use the bell curves to predict future cases / deaths
        """
        global predict_setting
        if predict is None : predict = predict_setting
        if self.s_end_days < 1 : 
            print(f"  ** first wave ended **")
            return
        if predict == 0 : predict = int(self.smooth/2) + 1
        if predict < 1 : return
        print(f"              Prediction ---      Total -------")
        print(f"Date          Cases   Deaths      Cases  Deaths")
        for d in range(0, predict) :
            i = self.s_latest_days - self.s_start_days + d + start
            date = self.s_latest + datetime.timedelta(d)
            marker = f"  <-- latest raw data" if date == self.latest else ""
            if i >= len(self.bell_cases) : break
            print(f"{date:%Y-%m-%d}" + \
                  f" {num(self.bell_cases[i])} {num(self.bell_deaths[i])}" + \
                  f" {num(self.sigmoid_cases[i], 10)} {num(self.sigmoid_deaths[i])}{marker}")
        print()
        return

    def analyse(self, days=None, predict=None, ylog=None, daily=None, infection=None, totals=None) :
        global days_setting, predict_setting, ylog_setting, daily_setting, infection_setting, totals_setting
        if days is None : days = days_setting
        if predict is None : predict = predict_setting
        if ylog is None : ylog = ylog_setting
        if daily is None : daily = daily_setting
        if infection is None : infection = infection_setting
        if totals is None : totals = totals_setting
        self.report()
        self.plot(ylog=ylog, daily=daily, infection=infection, totals=totals)
        self.show(days=days)
        self.prediction(predict=predict)
        return
