import datetime

raw_time1 = "04.05.22"
raw_time2 = "28.08.01"
time_format = "%d.%m.%y"
time1 = datetime.datetime.strptime(raw_time1, time_format)
time2 = datetime.datetime.strptime(raw_time2, time_format)
times = {"1": time1, "2": time2}

