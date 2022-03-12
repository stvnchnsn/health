import sqlite3
import pandas as pd
import datetime as dt
import time
import pickle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

HEALTH_DB_FP  = './health_db.sqlite'



def main():
    ew = Email_Workout(start_date = '2/21/2022',plan = "eight week high volume")
    ew.email_alert(hour_of_day = 5)
protocol = main

class Email_Workout:
    def __init__(self,start_date,plan):
        global HEALTH_DB_FP
        
        self.email_attachments_fp = './email_attachments/'
        self.health_db_fp = HEALTH_DB_FP
        self.start_date = pd.to_datetime(start_date)
        self.plan = plan
        self.day_of_plan()
        if self.relative_days_to_start < 0:
            print(f'Plan Starts in {-1*self.relative_days_to_start} day(s)')
        self.days_in_plan()
        print('Number of days in plan = {}'.format(self.duration_of_plan ))

    def day_of_plan(self):
        '''returns and integer of the number of days in relation to start day'''
        self.relative_days_to_start = (dt.date.today() - dt.date(year =self.start_date.year, month= self.start_date.month ,day = self.start_date.day)).days
        return self.relative_days_to_start
    def days_in_plan(self):
        '''returns how many days are in the plan'''
        conn = sqlite3.connect(self.health_db_fp)
        cur = conn.cursor()
        q = '''SELECT training_plan_exercise_workout.sequence_id
                FROM training_plan_exercise_workout JOIN training_plan
                ON training_plan.name = (?)'''
        cur.execute(q,(self.plan,))
        self.duration_of_plan = len(cur.fetchall())
        return self.duration_of_plan 
    
    def retreive_workout(self):
        '''generates current days workout'''
        conn = sqlite3.connect(self.health_db_fp)
        cur = conn.cursor()
        q = '''SELECT exercise.name, exercise.descrip,workout_exercise.repitions,training_plan_exercise_workout.circuits
                FROM training_plan JOIN training_plan_exercise_workout JOIN exercise JOIN workout_exercise JOIN workout
                ON training_plan_exercise_workout.workout_id = workout.id AND workout_exercise.exercise_id = exercise.id
                AND workout_exercise.workout_id = workout.id
                WHERE training_plan_exercise_workout.sequence_id = (?) and training_plan.name = (?)'''
        cur.execute(q,(self.relative_days_to_start,self.plan))
        workout_rows = cur.fetchall()
        self.curr_workout = pd.DataFrame.from_records(workout_rows,columns = ['name','descrip','repitions','circuit'])
        if len(self.curr_workout)==0:self.is_workout_today = False
        else:self.is_workout_today = True
    
    def retreive_cardio(self):
        'generates current cardio workout'
        conn = sqlite3.connect('./health_db.sqlite')
        cur = conn.cursor()
        q = '''SELECT DISTINCT cardio.name,cardio.descrip, cardio.distance,cardio.duration
                FROM training_plan JOIN training_plan_exercise_workout  JOIN cardio
                ON  training_plan_exercise_workout.cardio_id = cardio.id 
                WHERE training_plan_exercise_workout.sequence_id = (?) and training_plan.name = (?) '''
        cur.execute(q,(self.relative_days_to_start,self.plan))
        cardio_rows = cur.fetchall()
        self.curr_cardio = pd.DataFrame.from_records(cardio_rows,columns = ['name','descrip','distance','duration'])
        if len(self.curr_cardio) == 0: self.is_cardio_today = False
        else: self.is_cardio_today =True
    def generate_excel_files(self):
        self.retreive_workout()
        self.retreive_cardio()
        if self.is_workout_today:
            self.curr_wo_fname = f"workout_schedule_{dt.date.today().strftime('%d_%b_%Y')}.xlsx"
            self.curr_wo_fp = self.email_attachments_fp+self.curr_wo_fname
            self.curr_workout.to_excel(self.curr_wo_fp)
        if self.is_cardio_today:
            self.curr_cardio_fname = f"cardio_schedule_{dt.date.today().strftime('%d_%b_%Y')}.xlsx"
            self.curr_cardio_fp = self.email_attachments_fp+self.curr_cardio_fname 
            self.curr_cardio.to_excel(self.curr_cardio_fp)
    def send_email(self):
        email_info = pickle.load(open('email_info.pkl','rb'))
        fromaddr = email_info['from_email']
        password = email_info['password']
        toaddr = email_info['to_email']

        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = f"Daily Workout Schedule for {self.plan}"

        body = f'''Welcome to day {self.relative_days_to_start} of {self.duration_of_plan} of the {self.plan} plan!
        Today's workouts are attached! Go get some!'''
        msg.attach(MIMEText(body, 'plain'))

        if self.is_workout_today:
            filename = self.curr_wo_fname 
            attachment = open(self.curr_wo_fp , "rb")

            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
            msg.attach(part)
        if self.is_cardio_today:
            filename = self.curr_cardio_fname 
            attachment = open(self.curr_cardio_fp , "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
            msg.attach(part)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromaddr,password )
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()

    def email_alert(self,hour_of_day = 5):
        '''checks every 10 seconds until the hour of day is meet then sends email and sleeps 
        for 23hrs and 59 mins, then checks every 10 seoncds again until hour of day is meet...
        ends when the relative_days_to_start is greater than the duration of the plan'''

        self.day_of_plan() # updates self.relative_days_to_start 
        while self.relative_days_to_start <= self.duration_of_plan:
            # 
            if dt.datetime.now().hour != hour_of_day:
                print('sleeping for 10 seconds at ',dt.datetime.now().strftime("%d-%b-%Y_%H:%M"))
                time.sleep(10)
                self.day_of_plan() # updates self.relative_days_to_start 
            if dt.datetime.now().hour == hour_of_day:
                self.day_of_plan() # updates self.relative_days_to_start 
                self.generate_excel_files()
                try:
                    self.send_email()
                    print('Sent email at ',dt.datetime.now().strftime("%d-%b-%Y_%H:%M"))
                except:
                    print('Tried sending email but failed at ',dt.datetime.now().strftime("%d-%b-%Y_%H:%M"))
                print('sleeping for 23hrs and 59 mins...')
                time.sleep(86340)
        print('end of training plan!')





    


if __name__ == "__main__":
    protocol()