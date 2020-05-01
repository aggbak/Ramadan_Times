# Displays the prayer times
import tkinter as tk
import datetime
import json
import urllib.request
import os.path
import time
import winsound
import threading


ATHAN_EP = "http://api.aladhan.com/v1/hijriCalendarByAddress?address=Glenolden,%20PA"
TODAY_CACHE_FNAME = "prayer_times_cache.json"
TOM_CACHE_FNAME = "tom_prayer_times_cache.json"
KEYS_INTERESTED = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
globl_prayer_string = ""
globl_looping = True
globl_prayer_text = None
globl_time_to_pray = False
globl_calling_athan = False
app = None

def callAthanThread():
    # Wait a minute to call athan
    time.sleep(60)
    winsound.PlaySound("athan.wav", winsound.SND_FILENAME)
    global global_calling_athan
    globl_calling_athan = False
    return None

class Application(tk.Frame):
    def __init__(self, today_timings, master=None):
        super().__init__(master)
        self.master = master
        self.today_timings = today_timings
        self.pack()
        self.create_widgets()

    # Generate the graphical user interface 
    def create_widgets(self):
        global globl_prayer_string
        global globl_prayer_text

        
        
        self.pt = tk.StringVar()
        self.pt.set(globl_prayer_string)
        self.prayer_label = tk.Label(textvariable=self.pt)
        self.prayer_dates = self.today_timings["date"]["gregorian"]["date"]
        self.title_text = "Date: " + self.prayer_dates
        self.title_label = tk.Label(master=self, text=self.title_text)
        self.title_label.pack()
        # Add title headers for the app
        self.grid_frame = tk.Frame(master=self)
        self.grid_frame.pack()
        self.pr_title = tk.Label(self.grid_frame, text="Prayer")
        self.pr_title.grid(row=0, column=0)
        self.time_title = tk.Label(self.grid_frame, text="Time (EDT)")
        self.time_title.grid(row=0, column=1)
        self.athan_thread = threading.Thread(target=callAthanThread)
        # Get the timings
        prayer_timings = self.today_timings["timings"]
        for i in range(5):
            prayer_name = KEYS_INTERESTED[i]
            prayer_time = prayer_timings[prayer_name]
            name_label = tk.Label(self.grid_frame, text=prayer_name.replace("(EDT)",""))
            time_label = tk.Label(self.grid_frame, text=convertMilToMerid(prayer_time.replace("(EDT)","")))
            
            name_label.grid(row=i+1, column=0)
            time_label.grid(row=i+1, column=1)
        
        # Tack on prayer label to bottom
        self.prayer_label.pack()

    # Have this also be kind of a clock tick
    def update_prayer_time(self):
        global globl_prayer_string
        self.pt.set(globl_prayer_string)
        global globl_time_to_pray
        global globl_calling_athan
        # Check if it is time for a prayer
        if globl_time_to_pray and globl_calling_athan == False:
            globl_calling_athan = True
            print("Calling athan")
            self.athan_thread.start()
            

        



def getTomorrowDate():
    return datetime.date.today() + datetime.timedelta(days=1)


def getDateString(date_obj):
    string = "%02d-%02d-%04d" % (date_obj.day, date_obj.month, date_obj.year)
    return string

def getCurDateString():
    return getDateString(datetime.datetime.today())

def getTomDateString():
    tomorrow_date = getTomorrowDate()
    return getDateString(tomorrow_date)

def getJsonData(endPoint):
    data = urllib.request.urlopen(endPoint)
    return json.load(data)

def getJsonTodayData(jsonData):
    # Check the 30 days from the calendar
    current_date_string = getCurDateString()
    current_day_code = None
    # Do a linear search for the day code that corresponds to today
    for day_offset in range(0, 31):
        day_off_str = day_offset
        current_date = jsonData["data"][day_off_str]["date"]["gregorian"]["date"]
        if current_date == current_date_string:
            current_day_code = day_off_str
            break
    # Get the timing
    today_data = jsonData["data"][current_day_code]
    return today_data

def getJsonTomorrowData(jsonData):
    # Check the 30 days from the calendar
    current_date_string = getTomDateString()
    current_day_code = None
    # Do a linear search for the day code that corresponds to today
    for day_offset in range(0, 31):
        day_off_str = day_offset
        current_date = jsonData["data"][day_off_str]["date"]["gregorian"]["date"]
        if current_date == current_date_string:
            current_day_code = day_off_str
            break
    # Get the timing
    today_data = jsonData["data"][current_day_code]
    return today_data

# Save the current day's timings
def saveTodayInfo(timing_json):
    cache_file = open(TODAY_CACHE_FNAME,"w")
    json_string = json.dumps(timing_json)
    cache_file.write(json_string)
    cache_file.close()

# Load the current day's timings
def loadTodayInfo():
    cache_file = open(TODAY_CACHE_FNAME,"r")
    timing_json = json.load(cache_file)
    cache_file.close()
    return timing_json

def saveTomInfo(timing_json):
    cache_file = open(TOM_CACHE_FNAME,"w")
    json_string = json.dumps(timing_json)
    cache_file.write(json_string)
    cache_file.close()

# Load the current day's timings
def loadTomInfo():
    cache_file = open(TOM_CACHE_FNAME,"r")
    timing_json = json.load(cache_file)
    cache_file.close()
    return timing_json

# Return boolean value deciding whether we need to load from
# Cache or not
# Today changing means tomorrow changes as well
def checkForReload():
    if not(os.path.exists(TODAY_CACHE_FNAME)) or not(os.path.exists(TOM_CACHE_FNAME)):
        return True
    try:
        today_data = loadTodayInfo()
        last_read_date = today_data["date"]["gregorian"]["date"]
        today_date = getCurDateString()
        return last_read_date != today_date
    # On any failure to read the data, we have to reload
    except:
        return True

# Reload the timings from the endpoint and save to files
def reloadTimings():
    calendar_json = getJsonData(ATHAN_EP)
    today_timings = getJsonTodayData(calendar_json)
    tomorrow_timings = getJsonTomorrowData(calendar_json)
    saveTodayInfo(today_timings)
    saveTomInfo(tomorrow_timings)
    return today_timings, tomorrow_timings

# Get hours and minutes
def getTimeFromPrayerVal(prayer_val):
    # Remove the time zone part
    time_string = prayer_val.split(" ")[0]
    # Get the hour and minute as integers
    hour, minute = [int(time_elem) for time_elem in time_string.split(":")]
    return hour, minute



# Gets the name, time, and index of the last past prayer
def getLastPastPrayer(today_timings):
    prayer_mapping = today_timings["timings"]
    global KEYS_INTERESTED
    found_idx = -1
    idx = 0
    # Extract the date from the mappings
    day, month, year = [int(time_elem) for time_elem in today_timings["date"]["gregorian"]["date"].split("-")]
    for key in KEYS_INTERESTED:
        current_prayer_time = prayer_mapping[key]
        hour, minute = getTimeFromPrayerVal(current_prayer_time)
        # Create the time object for the prayer
        time_prayer = datetime.datetime(year, month, day, hour, minute)
        # Get the difference
        if time_prayer >= datetime.datetime.now():
            found_idx = idx
            return found_idx - 1
        idx += 1
    return found_idx

# Get the amount of time until next prayer    
def getTimeUntilNextPrayer(today_prayer_times, tomorrow_prayer_times, idx):
    global KEYS_INTERESTED
    next_idx = idx + 1
    # If the next_idx == 1: then look at next day's prayer_times
    next_day = next_idx // 5
    # Next_idx loops back over
    next_idx = next_idx % 5
    relevant_timings = today_prayer_times
    # Can treat like a boolean due to index domain
    if next_day:
        relevant_timings = tomorrow_prayer_times
    next_prayer_name = KEYS_INTERESTED[next_idx]
    day, month, year = [int(time_elem) for time_elem in relevant_timings["date"]["gregorian"]["date"].split("-")]
    hour, minute = getTimeFromPrayerVal(relevant_timings["timings"][next_prayer_name])
    time_prayer = datetime.datetime(year, month, day, hour, minute)
    time_diff = time_prayer - datetime.datetime.now()
    return time_diff, next_idx
    
def formatTimeUntilNextPrayer(time_delta, idx):
    global KEYS_INTERESTED
    out_str = "There are "
    pieces = [[0, "hours"], [0, "minutes"], [0, "seconds"]]
    diff_hours = time_delta.seconds // 3600
    diff_mins = (time_delta.seconds // 60) % 60
    diff_secs = (time_delta.seconds) % 60
    pieces[0][0] = diff_hours
    pieces[1][0] = diff_mins
    pieces[2][0] = diff_secs
    # Do checks for if it is that prayers time (be accurate to the minute)
    if diff_hours == 0 and diff_mins == 0:
        global globl_time_to_pray
        globl_time_to_pray = True
        return "It is time for " + KEYS_INTERESTED[idx] + "!"

    globl_time_to_pray = False
    # Do checks to convert plural units to singular
    for i in range(0, 3):
        if pieces[i][0] == 1:
            pieces[i][1] = pieces[i][1][:-1]
    
    revised_pieces = list(filter(lambda piece: piece[0] != 0, pieces))
    revised_pieces = list(map(lambda piece: str(piece[0]) + " " + piece[1], revised_pieces))
    pieces_string = ", ".join(revised_pieces)
    out_str += pieces_string + " until " + KEYS_INTERESTED[idx]
    return out_str

def convertMilToMerid(time_str):
    hours, mins = [int(i) for i in time_str.split(":")]
    merid = "a.m."
    if hours > 12:
        hours -= 12
        merid = "p.m."
    return str(hours) + ":" + str(mins) + " " + str(merid)

def clock_main(today_timings, tomorrow_timings):
    looping = True
    previous_time = None
    current_time = None
    idx = getLastPastPrayer(today_timings)
    global globl_prayer_string
    global globl_looping
    global app
    time_diff, next_idx = getTimeUntilNextPrayer(today_timings, tomorrow_timings, idx)
    while globl_looping:
        current_time = datetime.datetime.today()
        # If the day changes during runtime then reload again
        if previous_time != None:
            if current_time.day != previous_time.day:
                today_timings, tomorrow_timings = reloadTimings()
        time.sleep(.98)
        if not(globl_looping):
            break
        idx = getLastPastPrayer(today_timings)
        time_diff, next_idx = getTimeUntilNextPrayer(today_timings, tomorrow_timings, idx)
        globl_prayer_string = formatTimeUntilNextPrayer(time_diff, next_idx)
        if globl_looping:
            app.update_prayer_time()
        else:
            break
        previous_time = current_time
    return 

def main():
    # Have access to the global prayer_string
    global globl_prayer_string
    global globl_looping
    # Reload all the JSON data upon check
    if checkForReload():
        # Get JSONData from the web
        today_timings, tomorrow_timings = reloadTimings()
        print("Reload prayer times")
    else:
        today_timings = loadTodayInfo()
        tomorrow_timings = loadTomInfo()

    # After loading then there is a tick every second to check
    # Start that thread
    clock_thread = threading.Thread(target=clock_main, args=(today_timings, tomorrow_timings))
    clock_thread.start()
    global app
    root = tk.Tk()
    
    app = Application(today_timings, master=root)
    app.mainloop()
    globl_looping = False
    clock_thread.join()
    


if __name__ == "__main__":
    main()

