    import logging
    import shelve

    log = logging.getLogger(__name__)

    #autostart is cronjob only on startup (and 1 time every month)
    def autostart():
        dummy=init_powershelf()
        dummy=init_shelf()
        return 1


    #initialize global variables
    #otherwise error if you read it and they are not present
    def init_powershelf():
        try:
            sh = shelve.open("ManfredsPowerEvent.slv")
            sh["bms"]=-1
            sh["cnt_power"]=0
            sh["pwr_lastcall"]=14000.2
            #power state -1 is "unknown" -> on every reboot power event on or off will be fired
            sh["power_state"]=-1
            sh.close
        except:
            pass
        return 1


    #initialize global variables
    #otherwise error if you read it and they are not present
    def init_shelf():
        try:
            sh = shelve.open("ManfredsGlobalVariables.slv")
            dummy=sh["batpwr"]
            dummy=sh["ignit"]
            dummy=sh["bms"]
            dummy=sh["ELM_Voltage"]
            dummy=sh["kmh"]

            dummy=sh["soc"]
            dummy=sh["soc_time"]
            dummy=sh["cec"]
            dummy=sh["ced"]
            dummy=sh["odo"]
            dummy=sh["lon"]
            dummy=sh["lat"]
            dummy=sh["lonlat_time"]

            dummy=sh["ds_time"]
            dummy=sh["ds_lon"]
            dummy=sh["ds_lat"]
            dummy=sh["ds_odo"]
            dummy=sh["ds_soc"]
            dummy=sh["ds_cec"]
            dummy=sh["ds_ced"]

            dummy=sh["cs_time"]
            dummy=sh["cs_lon"]
            dummy=sh["cs_lat"]
            dummy=sh["cs_odo"]
            dummy=sh["cs_soc"]
            dummy=sh["cs_cec"]
            dummy=sh["cs_ced"]

            dummy=sh["cnt_ignit"]
            dummy=sh["cnt_bms"]

            dummy=sh["drive_state"]
            dummy=sh["charge_state"]

            dummy=sh["elap_poll"]
            dummy=sh["last_cellvoltage"]
            dummy=sh["webstatus_time"]

            sh.close
        except:
            sh["batpwr"]=0.0
            sh["ignit"]=-1
            sh["bms"]=-1
            sh["ELM_Voltage"]=0.0
            sh["kmh"]=0.0

            sh["soc"]=0.0
            sh["soc_time"]=1.0
            sh["cec"]=0.0
            sh["ced"]=0.0
            sh["odo"]=0.0
            sh["lon"]=0.0
            sh["lat"]=0.0
            sh["lonlat_time"]=1.0

            sh["ds_time"]=1.0
            sh["ds_lon"]=0.0
            sh["ds_lat"]=0.0
            sh["ds_odo"]=0.0
            sh["ds_soc"]=0.0
            sh["ds_cec"]=0.0
            sh["ds_ced"]=0.0

            sh["cs_time"]=1.0
            sh["cs_lon"]=0.0
            sh["cs_lat"]=0.0
            sh["cs_odo"]=0.0
            sh["cs_soc"]=0.0
            sh["cs_cec"]=0.0
            sh["cs_ced"]=0.0

            sh["cnt_ignit"]=0
            sh["cnt_bms"]=0

            sh["drive_state"]=0
            sh["charge_state"]=0

            sh["elap_poll"]=0.0
            sh["last_cellvoltage"]=3.0
            sh["webstatus_time"]=1.0
            
            sh.close
        
        return 1