    import logging
    import shelve
    import time
    import requests
    import json

    log = logging.getLogger(__name__)

    #poll is called by cronjob every 1 minute
    #main module
    def poll():

        #debug
        try:
            elap=time.time()
        except:
            elap=-1

        #load global variables
        sh = shelve.open("ManfredsGlobalVariables.slv")

        #read event relevant OBD values
        sh["bms"]=get_bms()
        sh["ignit"]=get_ignit()
        sh["batpwr"]=get_batpwr()

        #init impulse flags
        drive_start=False
        drive_end=False
        charge_start=False
        charge_end=False
        call_webstatus=False

        #check driving status
        if sh["ignit"]==1:
            sh["cnt_ignit"]=0
            if sh["drive_state"]==0:
                drive_start=True
        if sh["ignit"]!=1 and sh["drive_state"]==1:
            sh["cnt_ignit"] +=1
            if sh["cnt_ignit"] >= 3:
                drive_end=True

        # check charging status
        if sh["bms"]==1 and sh["ignit"]==0 and sh["batpwr"]<-1.0:
            sh["cnt_bms"]=0
            if sh["charge_state"]==0:
                charge_start=True
        if (sh["bms"]!=1 or sh["ignit"]==1) and sh["charge_state"]==1:
            sh["cnt_bms"] += 1
            if sh["cnt_bms"] >= 3:
                charge_end=True

        #fire events
        if drive_start:
            sh["drive_state"]=1
            call_webstatus=True
            __salt__["event.fire"]({}, "vehicle/drive/start")
        if drive_end:
            sh["drive_state"]=0
            call_webstatus=True
            __salt__["event.fire"]({}, "vehicle/drive/end")
        if charge_start:
            sh["charge_state"]=1
            call_webstatus=True     
            __salt__["event.fire"]({}, "vehicle/charge/start")
        if charge_end:
            sh["charge_state"]=0
            call_webstatus=True
            __salt__["event.fire"]({}, "vehicle/charge/end")  

        #webstatus every 30 minutes
        if (elap > (sh["webstatus_time"] + 1800.0)):
            call_webstatus=True

        #close global variables
        sh.close()

        #read all obds
        dummy=read_all_obds()

        #make drive/charge-protocol
        if drive_start:
            dummy=prot_drive_start()
        if drive_end:
            dummy=prot_drive_end()
        if charge_start:
            dummy=prot_charge_start()
        if charge_end:
            dummy=prot_charge_end()
        
        #put status to web
        if call_webstatus:
            dummy=webstatus()
        
        #debug
        sh = shelve.open("ManfredsGlobalVariables.slv")
        try:
            sh["elap_poll"]=time.time() - elap
        except:
            sh["elap_poll"]=-1.0
        ret={}
        ret['call_duration']=sh["elap_poll"]
        ret['charge_state']=sh["charge_state"]
        ret['drive_state']=sh["drive_state"]
        ret['ELM_Voltage']=sh["ELM_Voltage"]

        sh.close()
        return ret





    def webstatus():
        url = "http://www.mywebsite.com/mysubdirectory/receivewebhook.php"
        data = {}

        sh = shelve.open("ManfredsGlobalVariables.slv")

        data["soc"] = sh["soc"]
        data["soctime"] = sh["soc_time"]
        data["lon"] = sh["lon"]
        data["lat"] = sh["lat"]
        data["lonlattime"] = sh["lonlat_time"]
        
        result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            pass
        else:
            try:
                sh["webstatus_time"]=time.time()
            except:
                pass

        sh.close()



    def read_all_obds():
        # load global variables
        sh = shelve.open("ManfredsGlobalVariables.slv")
        try:
            nowtime=time.time()
        except:
            nowtime=3.0

        # get location from gps
        args = []
        kwargs = {}
        try:
            sh["lon"] = (__salt__['ec2x.gnss_location'](*args, **kwargs)['lon'])
        except:
            pass
        try:
            sh["lat"] = (__salt__['ec2x.gnss_location'](*args, **kwargs)['lat'])
            sh["lonlat_time"]=nowtime
        except:
            pass
        #get adapter voltage
        args = ["ELM_Voltage"]
        kwargs = {}
        try:
            sh["ELM_Voltage"] = (__salt__['obd.query'](*args, **kwargs)['value'])
        except:
            pass
        #get other obds
        args = ["fromscript"]
        kwargs["bytes"] = 64
        kwargs["baudrate"] = 500000
        kwargs["protocol"] = '6'
        kwargs["verify"] = False
        kwargs["force"] = True
        #get soc
        try:
            kwargs["mode"]='220'
            kwargs["pid"]='105'
            kwargs["header"]='7E4'
            kwargs["formula"]='bytes_to_int(message.data[34:35])'
            sh["soc"]= __salt__['obd.query'](*args, **kwargs)['value'] / 2.0
            sh["soc_time"]=nowtime
        except:
            pass
        #get cec
        try:
            kwargs["mode"]='220'
            kwargs["pid"]='101'
            kwargs["header"]='7E4'
            kwargs["formula"]='bytes_to_int(message.data[41:45])'
            sh["cec"]= __salt__['obd.query'](*args, **kwargs)['value'] / 10.0
        except:
            pass
        #get ced
        try:
            kwargs["mode"]='220'
            kwargs["pid"]='101'
            kwargs["header"]='7E4'
            kwargs["formula"]='bytes_to_int(message.data[45:49])'
            sh["ced"]= __salt__['obd.query'](*args, **kwargs)['value'] / 10.0
        except:
            pass
        #get odo
        try:
            kwargs["mode"]='22'
            kwargs["pid"]='B002'
            kwargs["header"]='7C6'
            kwargs["formula"]='bytes_to_int(message.data[10:12])'
            sh["odo"]= __salt__['obd.query'](*args, **kwargs)['value'] / 1.0
        except:
            pass
        #get km/h
        try:
            kwargs["mode"]='220'
            kwargs["pid"]='100'
            kwargs["header"]='7B3'
            kwargs["formula"]='bytes_to_int(message.data[32:33])'
            sh["kmh"]= __salt__['obd.query'](*args, **kwargs)['value'] / 1.0
        except:
            pass

        sh.close
        return 1

    def get_bms():
        #bms relay 1=on means "charging or driving"
        #obd.query Relay_Ignit mode=220 pid=101 header=7E4 bytes=64 formula='((bytes_to_int(message.data[12:13]))&1)/1'
        #unit=OnOff baudrate=500000 protocol=6 verify=false force=true
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
            return (int(__salt__['obd.query'](*args, **kwargs)['value'])&1)/1
        except:
            return -1

    def get_ignit():
        #ignition relay 1=on means "driving"
        #obd.query Relay_Ignit mode=220 pid=101 header=7E4 bytes=64 formula='((bytes_to_int(message.data[53:54]))&4)/4'
        #unit=OnOff baudrate=500000 protocol=6 verify=false force=true
        try:
            args = ['Relay_Ignit']
            kwargs = {
            'mode': '220',
            'pid': '101',
            'header': '7E4',
            'baudrate': 500000,
            'bytes': 64,
            'formula': 'bytes_to_int(message.data[53:54])',
            'protocol': '6',
            'verify': False,
            'force': True,
            }
            return (int(__salt__['obd.query'](*args, **kwargs)['value'])&4)/4
        except:
            return -1

    def get_batpwr():
        #Battery power[W] positive=drive / negative=charge
        #obd.query Batt_Power mode=220 pid=101 header=7E4 bytes=64
        #formula='(twos_comp(bytes_to_int(message.data[13:15]),16)/10.0)*((bytes_to_int(message.data[15:17]))/10.0)/1000.0'
        #unit=kW baudrate=500000 protocol=6 verify=false force=true
        try:
            args = ['batpwr']
            kwargs = {
                'mode': '220',
                'pid': '101',
                'header': '7E4',
                'bytes': 64,
                'formula': '(twos_comp(bytes_to_int(message.data[13:15]),16))*((bytes_to_int(message.data[15:17])))',
                'baudrate': 500000,
                'protocol': '6',
                'verify': False,
                'force': True,
                }
            return __salt__['obd.query'](*args, **kwargs)['value']/100000.0
        except:
            return (0.0)

    #
    class flc(float):
        def __str__(self):
            return self.__repr__().replace(".",",")


    #charging protocol
    def prot_charge_start():
        sh = shelve.open("ManfredsGlobalVariables.slv")
        try:
            sh["cs_time"]=time.time()
        except:
            sh["cs_time"]=2.0
        sh["cs_lon"]=sh["lon"]
        sh["cs_lat"]=sh["lat"]
        sh["cs_odo"]=sh["odo"]
        sh["cs_soc"]=sh["soc"]
        sh["cs_cec"]=sh["cec"]
        sh["cs_ced"]=sh["ced"]
        sh.close()

    #driving protocol
    def prot_drive_start():
        sh = shelve.open("ManfredsGlobalVariables.slv")
        try:
            sh["ds_time"]=time.time()
        except:
            sh["ds_time"]=2.0
        sh["ds_lon"]=sh["lon"]
        sh["ds_lat"]=sh["lat"]
        sh["ds_odo"]=sh["odo"]
        sh["ds_soc"]=sh["soc"]
        sh["ds_cec"]=sh["cec"]
        sh["ds_ced"]=sh["ced"]
        sh.close()


    #charging protocol
    def prot_charge_end():
        sh = shelve.open("ManfredsGlobalVariables.slv")
        try:
            et=time.time()
        except:
            et=3.0
        
        #duration 5sec on error
        dt=(et - sh["cs_time"])
        if dt<=0.0:
            dt=5.0 

        fileh = open('chargeprot.csv', "a")
        if fileh.tell() < 10:
            fileh.write('start time;lon;lat;odo;soc;cec;ced;end time;lon;lat;odo;soc;cec;ced;summary time;odo;soc;cec;ced;avg speed;avg kW charged\n')
        #fileh.write(txt + '\n')
        
        fileh.write(time.strftime("%d.%m.%Y %H:%M:%S;",time.localtime(sh["cs_time"])))
        fileh.write("{0:.6f};".format(sh["cs_lon"]).replace('.', ','))
        fileh.write("{0:.6f};".format(sh["cs_lat"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cs_odo"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cs_soc"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cs_cec"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cs_ced"]).replace('.', ','))

        fileh.write(time.strftime("%d.%m.%Y %H:%M:%S;",time.localtime(et)))
        fileh.write("{0:.6f};".format(sh["lon"]).replace('.', ','))
        fileh.write("{0:.6f};".format(sh["lat"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["odo"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["soc"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cec"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ced"]).replace('.', ',')) 

        fileh.write(time.strftime("%H:%M:%S;",time.gmtime(dt)))
        fileh.write("{0:.1f};".format(sh["odo"] - sh["cs_odo"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["soc"] - sh["cs_soc"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cec"] - sh["cs_cec"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ced"] - sh["cs_ced"]).replace('.', ','))

        fileh.write("{0:.0f};".format((sh["odo"] - sh["cs_odo"])*3600.0/dt).replace('.', ','))
        fileh.write("{0:.2f}".format((sh["cec"] - sh["cs_cec"])*3600.0/dt).replace('.', ','))

        fileh.write("\n")

        sh.close()
        fileh.close()

    #driving protocol
    def prot_drive_end():
        sh = shelve.open("ManfredsGlobalVariables.slv")
        try:
            et=time.time()
        except:
            et=3.0
        
        #duration 5sec on error
        dt=(et - sh["ds_time"])
        if dt<=0.0:
            dt=5.0 

        #distance 0.1km on error
        dist=sh["odo"] - sh["ds_odo"]
        if dist<=0.0:
            dist=0.1


        fileh = open('driveprot.csv', "a")
        if fileh.tell() < 10:
            fileh.write('start time;lon;lat;odo;soc;cec;ced;end time;lon;lat;odo;soc;cec;ced;summary time;odo;soc;cec;ced;avg speed;avg kWh/100km\n')
        #fileh.write(txt + '\n')
        
        fileh.write(time.strftime("%d.%m.%Y %H:%M:%S;",time.localtime(sh["ds_time"])))
        fileh.write("{0:.6f};".format(sh["ds_lon"]).replace('.', ','))
        fileh.write("{0:.6f};".format(sh["ds_lat"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ds_odo"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ds_soc"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ds_cec"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ds_ced"]).replace('.', ','))

        fileh.write(time.strftime("%d.%m.%Y %H:%M:%S;",time.localtime(et)))
        fileh.write("{0:.6f};".format(sh["lon"]).replace('.', ','))
        fileh.write("{0:.6f};".format(sh["lat"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["odo"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["soc"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cec"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ced"]).replace('.', ',')) 

        fileh.write(time.strftime("%H:%M:%S;",time.gmtime(dt)))
        fileh.write("{0:.1f};".format(dist).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["soc"] - sh["ds_soc"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["cec"] - sh["ds_cec"]).replace('.', ','))
        fileh.write("{0:.1f};".format(sh["ced"] - sh["ds_ced"]).replace('.', ','))

        fileh.write("{0:.0f};".format(dist*3600.0/dt).replace('.', ','))
        fileh.write("{0:.2f}".format((sh["ced"] - sh["ds_ced"] - sh["cec"] + sh["ds_cec"])*100.0/dist).replace('.', ','))
        
        fileh.write("\n")

        sh.close()
        fileh.close()