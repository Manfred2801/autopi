import logging
import shelve
import time

log = logging.getLogger(__name__)

#started by cronjob every minute
def powerevent():
    #load global variables
    sh = shelve.open("ManfredsPowerEvent.slv")
    #read bms-relay from OBD
    try:
        args = ['Relay_BMS']
        kwargs = {
        'mode': '220',
        'pid': '101',
        'header': '7E4',
        'bytes': 64,
        'baudrate': 500000,
        'formula': 'bytes_to_int(message.data[12:13])',
        'protocol': '6',
        'verify': False,
        'force': True,
        }
        sh["bms"]=(int(__salt__['obd.query'](*args, **kwargs)['value'])&1)/1
    except:
        sh["bms"]=-1
    tnow=time.time()
    tdiff=tnow-sh["pwr_lastcall"]
    #reset power-state to unknown when last call was more than 7000sec
    #better to have more "power off" events than an empty battery!
    if tdiff>7000:
        sh["power_state"]=-1
    #check power status
    if sh["bms"]==1 and sh["power_state"]!=1:
        sh["power_state"]=1
        sh["cnt_power"] = 0
        __salt__["event.fire"]({}, "vehicle/pwr/on")
    if sh["bms"]!=1 and sh["power_state"]!=0:
        sh["cnt_power"] += 1
        #give me 10 minutes before power off event
        if sh["cnt_power"] >= 10:
            sh["power_state"]=0
            __salt__["event.fire"]({}, "vehicle/pwr/off")
    #close global variables
    #ret = {"bms":sh["bms"],"cnt_power":sh["cnt_power"], "power_state":sh["power_state"], "last_call":tdiff}
    ret = {"power_state":sh["power_state"],"call_duration":(time.time()-tnow)}
    sh["pwr_lastcall"]=tnow
    sh.close()
    return (ret)