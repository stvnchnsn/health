import sqlite3
import pandas as pd
import os

conn = sqlite3.connect('./health_db.sqlite')
cur = conn.cursor()

if not 'email_attachments' in [i.name for i in os.scandir()]:
    os.mkdir('./email_attachments')

# Read from starting_db
exercise_data = pd.read_excel('./starting_db.xlsx',sheet_name = 'exercises')
workout_exercise_data = pd.read_excel('./starting_db.xlsx',sheet_name = 'workout_exercise')
workout_data = pd.read_excel('./starting_db.xlsx',sheet_name = 'workout')
training_plan_data = pd.read_excel('./starting_db.xlsx',sheet_name = 'training_plan')
training_plan_exercise_workout_data = pd.read_excel('./starting_db.xlsx',sheet_name = 'training_plan_exercise_workout')
cardio_data = pd.read_excel('./starting_db.xlsx',sheet_name = 'cardio')
# Body Region Table
cur.execute('''CREATE TABLE IF NOT EXISTS body_region (
    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
    name TEXT)''')
body_regions = {'lower':0,'core':1,'upper':2}
q = '''SELECT * FROM body_region'''
cur.execute(q)
if len(cur.fetchall())<len(body_regions):
    cur.execute('''DELETE FROM body_region''')
    for region, _id in body_regions.items():
        cur.execute('''INSERT INTO body_region (id,name) Values (?,?)''',(_id,region,))

# Muscle Group Table
cur.execute('''CREATE TABLE IF NOT EXISTS muscle_groups (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT,
    body_region_id, INTERGER)
    ''')

muscles_to_region = {'feet':0,'calves':0,'hamstrings':0,'glutes':0,'hips':0,'quads':0,'groin':0,'gluteals':0,'quadriceps':0,
            'abs':1,'obliques':1,'hip flexors':1,'lower back':1,
            'shoulders':2,'upper back':2,'arms':2,'chest':2}
muscles_to_id = {}
for i, k in zip(range(1,1+len(muscles_to_region.keys())),muscles_to_region.keys()):
    muscles_to_id[k] = i


q = 'SELECT * FROM muscle_groups'
cur.execute(q)
if len(cur.fetchall())<len(muscles_to_region):
    cur.execute('DELETE FROM muscle_groups')
    for group,body_region_id in muscles_to_region.items():
        cur.execute('INSERT INTO muscle_groups (name,body_region_id) VALUES (?,?)',(group,body_region_id))

# BIOMETRICS Table
cur.execute('''CREATE TABLE IF NOT EXISTS biometrics (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT,
    descrip TEXT,
    metric FLOAT
)'''
)
# Equipment Table
cur.execute('''CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
    name TEXT)''')
equipment = ['box','stability ball','kettle ball','buddy','exercise band','stick','cable pulley','pull-up bar','bench','no equipment']
q = '''SELECT * FROM equipment'''
cur.execute(q)
if len(cur.fetchall())<len(equipment):
    cur.execute('''DELETE FROM equipment''')
    for i,e in enumerate(equipment):
        cur.execute('INSERT INTO equipment (id,name) VALUES (?,?)',(i,e))


# Exercise Table
cur.execute('''CREATE TABLE IF NOT EXISTS exercise (
    id INTEGER NOT NULL PRIMARY KEY UNIQUE, 
    name TEXT,
    descrip TEXT,
    media TEXT,
    difficulty FLOAT,
    duration INTEGER,
    body_region_id
)''')

q = '''SELECT * FROM exercise'''
cur.execute(q)
refresh_exercise_data = False # used to determine if the junction tables should be updated
if len(cur.fetchall())<len(exercise_data):
    refresh_exercise_data = True
    cur.execute('''DELETE FROM exercise''')
    for i, exercise in enumerate(exercise_data['name']):
        cur.execute('''INSERT INTO exercise (id,name,descrip,media,difficulty,duration,body_region_id) 
                        Values (?,?,?,?,?,?,?)''',
                        (i,exercise_data.loc[i,'name'],exercise_data.loc[i,'descrip'],
                        exercise_data.loc[i,'media'],exercise_data.loc[i,'difficulty'],
                        exercise_data.loc[i,'duration'],body_regions[exercise_data.loc[i,'body_regions']]
                        )
                    )

# Workout Table

cur.execute('''CREATE TABLE IF NOT EXISTS workout (
    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
    name TEXT,
    type TEXT)
    ''')
for i in workout_data['id']:
    cur.execute('''INSERT INTO workout (id,name,type)
                VALUES (?,?,?)''',(i,workout_data.loc[i,'name'],workout_data.loc[i,'type']))

# Training Plan Table
cur.execute('''CREATE TABLE IF NOT EXISTS training_plan (
    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
    name TEXT,
    source TEXT)'''
            )
for i in training_plan_data['id']:
    cur.execute('''INSERT INTO training_plan (id,name,source)
                VALUES (?,?,?)''',(i,training_plan_data.loc[i,'name'],training_plan_data.loc[i,'source']))

# Cardio Table
cur.execute('''CREATE TABLE IF NOT EXISTS cardio (
    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
    name TEXT,
    descrip TEXT,
    distance TEXT,
    duration TEXT)''')
for i in cardio_data['id']:
    cur.execute('''INSERT INTO cardio (id, name, descrip,duration,distance)
                VALUES (?,?,?,?,?)''',(i,cardio_data.loc[i,'name'],
                                        cardio_data.loc[i,'descrip'],
                                        cardio_data.loc[i,'duration'],
                                        cardio_data.loc[i,'distance']
                                        )
                )

# Junction Tables
# exercise_muscle
cur.execute('''CREATE TABLE IF NOT EXISTS exercise_muscle (
    muscles_id INTEGER,
    exercise_id INTEGER,
    PRIMARY KEY (muscles_id,exercise_id)

)''')
if refresh_exercise_data:
    cur.execute('DELETE FROM exercise_muscle')
    for i, muscles in enumerate(exercise_data['muscles']):
        try:
            for m in eval(muscles):
                cur.execute('''INSERT INTO exercise_muscle (exercise_id,muscles_id)
                                VALUES (?,?)''',(i,muscles_to_id[m]))
        except TypeError:
            pass


# exercise_equipment
cur.execute('''CREATE TABLE IF NOT EXISTS exercise_equipment (
    equipment_id INTEGER,
    exercise_id INTEGER,
    PRIMARY KEY (equipment_id,exercise_id)

)''')
# exercise_biometrics
cur.execute('''CREATE TABLE IF NOT EXISTS exercise_biometrics (
    biometrics_id INTEGER,
    exercise_id INTEGER,
    PRIMARY KEY (biometrics_id,exercise_id)

)''')

# workout_exercise
cur.execute('''CREATE TABLE IF NOT EXISTS workout_exercise (
    exercise_id INTEGER,
    workout_id INTEGER,
    repitions TEXT,
    PRIMARY KEY (exercise_id,workout_id)

)''')
for i, _ in enumerate(workout_exercise_data['workout_id']):
    try:
        cur.execute('''INSERT INTO workout_exercise(exercise_id,workout_id,repitions)
                VALUES (?,?,?)''',(int(workout_exercise_data.loc[i,'exercise_id']),
                                    int(workout_exercise_data.loc[i,'workout_id']),
                                    workout_exercise_data.loc[i,'repitions']))
    except:
        print(workout_exercise_data.loc[i])


# training_plan_exercise_workout

cur.execute('''CREATE TABLE IF NOT EXISTS training_plan_exercise_workout (
            training_plan_id INTEGER,
            sequence_id INTEGER,
            workout_id INTEGER,
            circuits INTEGER,
            cardio_id INTEGER,
            PRIMARY KEY (training_plan_id,sequence_id,workout_id,cardio_id))
            ''')

for i, train_plan in enumerate(training_plan_exercise_workout_data['training_plan_id']):
    cur.execute('''INSERT INTO training_plan_exercise_workout(training_plan_id,sequence_id,workout_id,cardio_id,circuits)
                VALUES (?,?,?,?,?)''',(train_plan,
                                       int(training_plan_exercise_workout_data.loc[i,'sequence_id']),
                                       int(training_plan_exercise_workout_data.loc[i,'workout_id']),
                                       int(training_plan_exercise_workout_data.loc[i,'cardio_id']),
                                       training_plan_exercise_workout_data.loc[i,'circuits'] 
                                       )
                )

# Schedule Table
cur.execute('''CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT,
    descrip TEXT,
    sequence INTEGER,
    planned_date TEXT,
    actual_date TEXT,
    comments TEXT,
    exercise_id INTEGER
)''')
conn.commit()
