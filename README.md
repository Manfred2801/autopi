# autopi
tools for autopi.io for Hyundai Kona EV
The following functions for Autopi.io and Hyundai Kona EV 2019 can be found here:


####power settings for autopi
it is done by checking the obd "relay_bms", means the electric vehicle is either charging or driving.
you need:
my_autostart.py
cron_autostart.JPG
my_powerevent.py
cron_my_powerevent.JPG
power settings.txt



####trip settings for dongle
it is done by checking the obd "relay_bms" and "relay_ignit" and "bat_power", means the electric vehicle is either charging or driving.
you need:
my_autostart.py
cron_autostart.JPG
my_eventgen.py
cron_my_eventgen.JPG
trip settings.txt



####Driving and charging protocol csv-file
generates 2 csv files and stores it on autopi SD-card
stores date,time,location, ODO, SOC, energy charged, energy discharged, summary and avg values of each trip or each charge.
you need:
my_autostart.py
cron_autostart.JPG
my_eventgen.py
cron_my_eventgen.JPG
chargeprot.csv
driveprot.csv



####GetDataFromWebAPI.xlsm
used to fetch logged data from my.autopi.io directly to MS Excel.



####Charge status and location on personal website
I can see the status on my personal (hidden) website, without any password and stuff. Very simple view, optimized for mobile phone.
it is updated every half hour by dongle. A personal website with php-support is required for this!
you need:
my_autostart.py
cron_autostart.JPG
my_eventgen.py
cron_my_eventgen.JPG
receivewebhook.php
screenshot_mobile.jpg
