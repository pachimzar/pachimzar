import sys
import time
from datetime import datetime as dt
import csv
import numpy as np
import pandas as pd
import yagmail
from pretty_html_table import build_table
from IPython.display import display
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

# define the countdown function for countdowm timer.
def countdown(t):

   while t:
       mins, secs = divmod(t, 60)
       timer = '{:02d}:{:02d}'.format(mins, secs)
       print(timer, end="\r")
       time.sleep(1)
       t -= 1
   print ("Time's Up!")

def SaveData():

       from csv import DictWriter # Import DictWriter class from CSV module


       tim = dt.now()
       date_time = tim.strftime("%b-%d-%Y (%H:%M:%S)")


       # list of column names
       field_names = ['shelf', 'data & time', 'act_soil_moist_index', 'soil_moist_lmt']


       df = pd.DataFrame({'shelf': ["Top", "Middle", "Bottom"], 'data & time': [date_time, date_time, date_time], 'act_soil_moist_index': [Soil_Moist_A0, Soil_Moist_A1, Soil_Moist_A2], 'soil_moist_lmt': [lower_limit_A0, lower_limit_A1, lower_limit_A2]})

       df.to_csv('Soil_Moisture_Reading.csv', mode='a', index=False, header=False)
       
def email(subject, HTML):
    
    user = "pachimzar+waterpi@gmail.com"
    app_password = "tctpbxvyjkgjotka"
       
    to = "pachimzar@gmail.com"
    
    with yagmail.SMTP(user,app_password) as yag:
        yag.send(to = to, subject = subject, contents = HTML)

if __name__ == "__main__":
    global ON
    global OFF


    ON = GPIO.LOW
    OFF = GPIO.HIGH
    GPIO.setmode(GPIO.BCM) # GPIO pins based on  "Broadcom SOC channel"
    GPIO.setwarnings(False)


    # Create the I2C bus
    i2c = busio.I2C(board.SCL, board.SDA)

    # Create the ADC object using the I2C bus
    ads = ADS.ADS1015(i2c)

    # Create single-ended input on channel A0, A1, and A2
    # Channel A0 is the top shelf soil moisture sensor, A1 is middle shelf moisture sensor and
    # A2 is bottom shelf sensor.

    chan_A0 = AnalogIn(ads, ADS.P0) #Signal from  Moisture Sensor on Ads1x5 A0
    chan_A1 = AnalogIn(ads, ADS.P1) #Signal from  Moisture Sensor on Ads1x5 A1
    chan_A2 = AnalogIn(ads, ADS.P2) #Signal from  Moisture Sensor on Ads1x5 A2

    subject = "Attention: Water Controller Successful"

    HTML = """
    <!DOCTYPE html>
    <html>
       <body>
           Indoor Plant Watering Controller started up sucessfully!
       </body>
    </html>
    """
    email(subject, HTML)

     
    try:
   
       # Counts the number of consecutive watering per soil moisture sensor
       n_A0 = 0 # Number of consecutive waterings for sensor A0
       n_A1 = 0  # Number of consecutive waterings for sensor A1
       n_A2 = 0  # Number of consecutive waterings for sensor A2
       tstrt = None
       mstrt = None
       bstrt = None
       tsm_beg = None
       msm_beg = None
       bsm_beg = None
       tend = None
       mend = None
       bend = None
       tsm_end = None
       msm_end = None
       bsm_end = None
       top_list = ()
       mid_list = ()
       bot_list = ()
       count = 0

       while True:

           # Take 5 soil moisture reading from sensors A0, A1, and A2.
           sum_A0_value = 0; sum_A1_value = 0; sum_A2_value = 0
           avg_A0_value = 0; avg_A1_value = 0; avg_A2_value = 0

           tim = dt.now()
           reading_date_time = tim.strftime("%b-%d-%Y (%H:%M:%S)") # Date and time that moisture readings were taken

           for sample  in range(1,5):
               sum_A0_value = sum_A0_value + chan_A0.value
               sum_A1_value = sum_A1_value + chan_A1.value
               sum_A2_value = sum_A2_value + chan_A2.value

               time.sleep(1)

               avg_A0_value = round(sum_A0_value/5, 0)
               avg_A1_value = round(sum_A1_value/5, 0)
               avg_A2_value = round(sum_A2_value/5 ,0)

           # Calculates soil moisture index, where 0 is bone dry soil and 10 is
           # saturated soil,   from  sensor  values from A0, A1 and A2 Sensors

           Soil_Moist_A0 = round(22.39-0.000872*avg_A0_value,2) # Top Shelf Soil Moisure Reading
           Soil_Moist_A1 = round(21.73-0.00134*avg_A1_value,2) # Middle Shelf Soil Moisture Reading
           Soil_Moist_A2 = round(21.35-0.001275*avg_A2_value,2) # Bottom Shelf Soil Moisture Reading

           lower_limit_A0 = 6.50 #Lower moisture limit to trigger water system for top shelf
           lower_limit_A1 = 6.50 #Lower moisture limit to trigger water system for middle shelf
           lower_limit_A2 = 7.00 #Lower moisture limit to trigger water system for bottom shelf

           SaveData()
           probe =  {Soil_Moist_A0, Soil_Moist_A1, Soil_Moist_A2}
           for i  in probe:
               print(i) 

           if  (Soil_Moist_A0 < lower_limit_A0) or (Soil_Moist_A1 < lower_limit_A1) or (Soil_Moist_A2 < lower_limit_A2):


               #  Watering Time in seconds per Shelf.  Pump rate is 8.3 mL per second or 0.56 Tbls per seconds

               t_A0 = 90 # Valve A0
               t_A1 = 90  # Valve A1
               t_A2 = 90 # Valve A2

               GPIO.setup(24, GPIO.OUT) # Pump circuit
               GPIO.output(24, ON) # Turn on pump
               print ('Pump  is ON')

               time.sleep(15)
           
               if Soil_Moist_A0 < lower_limit_A0:

                   if n_A0 == 0:
                       tim = dt.now()
                       tstrt = tim.strftime("%b-%d-%Y (%H:%M:%S)") # Watering start time for Top Self in military time
                       tsm_beg = Soil_Moist_A0 # Soil moisture before watering starts

                   GPIO.setup(27, GPIO.OUT) # Solenoid Valve A0 circuit
                   GPIO.output(27, ON) # Open valve A0
                   print ('Valve A0 OPEN')

                   t = t_A0
                   countdown(t)

                   GPIO.output(27, OFF)
                   print ('Valve A0 CLOSED')

                   n_A0 = n_A0 + 1 # Count the number of consecutive watering for Top Shelf       

               if  Soil_Moist_A1 < lower_limit_A1:

                   if n_A1==0:

                       tim =  dt.now()
                       mstrt =  tim.strftime("%b-%d-%Y (%H:%M:%S)") # Watering start time for Middle Shelf in military time
                       msm_beg = Soil_Moist_A1 # Soil moisture before watering starts

                   GPIO.setup(22, GPIO.OUT) # Solenoid Valve A1 circuit
                   GPIO.output(22, ON) # Open valve A1
                   print ('Valve A1 OPEN')
 
                   t = t_A1
                   countdown(t)

                   GPIO.output(22, OFF)
                   print ('Valve A1 CLOSED')

                   n_A1 = n_A1 + 1 # Count the number of consecutive watering for Middle Shelf

               if  Soil_Moist_A2 < lower_limit_A2:

                   if n_A2 == 0:

                       tim  = dt.now()
                       bstrt =  tim.strftime("%b-%d-%Y (%H:%M:%S)") # Watering start time for Middle Shelf in military time
                       bsm_beg = Soil_Moist_A2 # Soil moisture before watering starts

                   GPIO.setup(23, GPIO.OUT) # Solenoid Valve A2 circuit
                   GPIO.output(23, ON) # Open valve A2
                   print ('Valve A2 OPEN')

                   t = t_A2
                   countdown(t)

                   GPIO.output(23,OFF)
                   print ('Valve A2 CLOSED')

                   n_A2 = n_A2 + 1 # Count the number of consecutive watering for Bottom Shelf

               GPIO.setup(24, GPIO.OUT) # Pump circuit
               GPIO.output(24, OFF) # Turn off pump
               print ('Pump  is OFF')

               t = int(60*10)
               print (t/60, ' minutes before retesting')
               countdown(t) #Wait 10 minutes before retesting soil moisture
           
           if Soil_Moist_A0 > lower_limit_A0 and n_A0 > 0:
                tim = dt.now()
                tend =  tim.strftime("%b-%d-%Y (%H:%M:%S)") # Watering end time for Top Shelf in military time
                sm_end = Soil_Moist_A0 # Soil moisture at end of watering top shelf
                top_list = ("Top", tstrt, tend, tsm_beg, tsm_end, t_A0, n_A0)
               
           if Soil_Moist_A1 > lower_limit_A1 and n_A1 > 0:
                tim = dt.now()
                mend =  tim.strftime("%b-%d-%Y (%H:%M:%S)") # Watering end time for Middle Shelf in military time
                msm_end = Soil_Moist_A1 # Soil moisture at end of watering middle shelf
                mid_list = ("Middle", mstrt, mend, msm_beg, msm_end, t_A1, n_A1)
           
           if Soil_Moist_A2 > lower_limit_A2 and n_A2 >0:
                tim = dt.now()
                bend =  tim.strftime("%b-%d-%Y (%H:%M:%S)") # Watering end time for Bottom Shelf in military time
                bsm_end = Soil_Moist_A2 # Soil moisture at end of watering bottom shelf
                bot_list = ("Bottom", bstrt, bend, bsm_beg, bsm_end, t_A2, n_A2)    
           
           if top_list != () or mid_list != () or bot_list != ():  
                data1  = [top_list, mid_list, bot_list]
                print (data1)
                df1 = pd.DataFrame(data1, columns=['Shelf', 'Beg, Watering', 'End Watering', 'Beg. Soil Moisture', ' End. Soil Moistue',  'Water Cycle Time, sec.', 'Number of Consecutive Waterings'])

                subject = "Attention: Indoor Plant Watering Completed"

                HTML = """
                <!DOCTYPE html>
                <html>
                </html>
                """.format(build_table(df1, 'blue_light', width='7px', text_align='center', font_size='10',))

                email(subject, HTML)
                
                print ("Email sent successfully !")

                # Counts the number of consecutive watering per soil moisture sensor
                n_A0 = 0 # Number of consecutive waterings for sensor A0
                n_A1 = 0  # Number of consecutive waterings for sensor A1
                n_A2 = 0  # Number of consecutive waterings for sensor A2
                tstrt = None
                mstrt = None
                bstrt = None
                tsm_beg = None
                msm_beg = None
                bsm_beg = None
                tend = None
                mend = None
                bend = None
                tsm_end = None
                msm_end = None
                bsm_end = None
                top_list = ()
                mid_list = ()
                bot_list = ()
            
            
           elif n_A0 == 0 and n_A1 ==0 and n_A2 ==0:       
                t= int(60*5 )
                print ('Wait ',  t/60, ' minutes  before retesting')
                countdown(t)
                count = count + 1
            
                if count == 4:
                   tim = dt.now()
                   time_stamp =  tim.strftime("%b-%d-%Y (%H:%M:%S)")     
                   data2  = {'Date Time': [time_stamp],
                             'A0_Moisture':[Soil_Moist_A0],
                             'A1_Moisture': [Soil_Moist_A1],
                             'A2_Moisture': [Soil_Moist_A2]}
                   df2 = pd.DataFrame(data2)

                   
                   subject = "Indoor Plant Watering Readings"

                   HTML = """
                   <!DOCTYPE html>
                   <html>
                   </html>
                   """.format(build_table(df2, 'blue_light', width='7px', text_align='center', font_size='10',))

                   email(subject, HTML)
    
                   print ("Email sent successfully !")
                   count = 0
                   t =  0
    

    except KeyboardInterrupt:

       GPIO.setup(27, GPIO.OUT)
       GPIO.output(27, OFF)
       GPIO.setup(23, GPIO.OUT)
       GPIO.output(23, OFF)

       GPIO.setup(22, GPIO.OUT)
       GPIO.output(22, OFF)

       GPIO.setup(24, GPIO.OUT)
       GPIO.output(24, OFF)
    
      
       subject = "Attention: Water System Failured"

       HTML = """
       <!DOCTYPE html>
       <html>
           <body>
                System failure: Pythn Scriped Aborted!
                Check watering system.
            </body>
        </html>
       """
       email(subject, HTML)
   
    finally:
    
       GPIO.cleanup() 



