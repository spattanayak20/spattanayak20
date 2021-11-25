import base64
from configparser import ConfigParser
from os import read
import cv2
import imagehash
from numpy.core.fromnumeric import compress
import pandas as pd
import PIL
import psycopg2
import matplotlib.pyplot as plt
import scipy.fftpack
import hashlib
from db_driver import aggregate
# handle = "localhost"
handle = "34.93.181.52"
database = "telio_lions"


def get_all_compressed_faces():
    ret = 0
    conn = None
    rv = dict()
    sql = "SELECT name,face FROM compressed_images;"
    try :
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")

        cur = conn.cursor()
        cur.execute(sql)
        records = cur.fetchall()
        for record in records:
            record = records[0]
            rv['name'] = record[0]
            rv['face'] = record[1]
        cur.close()

        # df = pd.DataFrame(records, columns=['name', 'face'])
        # df = df.groupby(['name'])['face'].apply(lambda x: aggregate(x)).reset_index()
        # lions = list()
        # for index, row in df.iteritems():
        #     info = dict()
        #     info['name'] = row['name']
        #     info['face'] = row['face']
        #     lions.append(info)
        # rv['lions'] = lions
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        rv = dict()
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


def get_all_compressed_lions():
    ret = 0
    conn = None
    rv = dict()
    sql = "SELECT C1.name, L1.sex, L1.status, L1.click_date, L1.upload_date, L1.latitude, L1.longitude, C1.face FROM compressed_images C1 "\
         "INNER JOIN lion_data L1 "\
        "ON C1.id = L1.id;"

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        records = cur.fetchall()
        cur.close()
        df = pd.DataFrame(records, columns=['name', 'sex', 'status', 'click_date',
                                            'upload_date', 'latitude', 'longitude', 'face'])
        df = df.groupby(['name'])['sex', 'status', 'click_date', 'upload_date', 'latitude', 'longitude', 'face'].apply(lambda x: aggregate(x)).reset_index()
        lions = list()
        for index, row in df.iterrows():
            info = dict()
            info['name'] = row['name']
            info['sex'] = row['sex']
            info['status'] = row['status']
            info['click_date'] = str(row['click_date'])
            info['upload_date'] = str(row['upload_date'])
            info['latitude'] = row['latitude']
            info['longitude'] = row['longitude']
            info['face'] = row['face']
            lions.append(info)
        rv['lions'] = lions
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        rv = dict()
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


# string_return
def get_base64_str(image):
    try:
        with open(image, "rb") as imageFile:
            base64_str = str(base64.b64encode(imageFile.read()))[2:-1]
        return base64_str
    except Exception as e:
        return ''

def duplicate_img_detected(hash_value):
    ret = False
    status = "Success"
    conn = None
    sql = "SELECT hash_value FROM lion_data ;"
    try:
        conn = psycopg2.connect(host= handle,
                                database=database,
                                user="postgres",
                                password="admin")

        cur = conn.cursor()
        cur.execute(sql)
        records = cur.fetchall()
        cur.close()
        df = pd.DataFrame(records,columns=['hash'])
        hash_list = df['hash'].tolist()

        if hash_value not in hash_list:
            ret = 0
        else:
            ret = 1
            status = "Duplicate image Detected"

    except (Exception, psycopg2.DatabaseError) as error:
            print("DB Error: " + str(error))
            ret_str = str(error)
            ret = -1
            status = "DB error"
    finally:
        if conn is not None:
            conn.close()
        return ret ,status


def img_hash_value(images):
    try:
        hash_value = imagehash.dhash(PIL.Image.open(images))
        print('Hash_value ',str(hash_value))
        return hash_value
    except Expection as e:
        return ''


# def verify():
#     def init():
#         if not if_table_exists(table_name='compressed_TB'):
#             create_user_data_table()
#         else:
#             insert_compressed_data()

def insert_compressed_data(_id, name,
                           image, face,
                           whisker, lear,
                           rear, leye,
                           reye, nose
                           ):
    ret = 0
    status = "Success"
    conn = None
    try:
        try:
            image_bytes = get_base64_str(image)
        except Exception as e:
            image_bytes = ''
            pass
        face_bytes = get_base64_str(face)

        whisker_bytes = get_base64_str(whisker)
        try:
            lear_bytes = get_base64_str(l_ear)
        except Exception as e:
            lear_bytes = ''
            pass

        try:
            rear_bytes = get_base64_str(r_ear)
        except Exception as e:
            rear_bytes = ''
            pass
        try:
            leye_bytes = get_base64_str(l_eye)
        except Exception as e:
            leye_bytes = ''
            pass
        try:
            reye_bytes = get_base64_str(r_eye)
        except Exception as e:
            reye_bytes = ''
            pass
        try:
            nose_bytes = get_base64_str(nose)
        except Exception as e:
            nose_bytes = ''
            pass



        # try:
        #     hash_value = hash_value
        # except Exception as e:
        #     hash_value = ''
        #     pass

        sql = """INSERT INTO compressed_images VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING ID;"""
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_id,
                          name,
                          image_bytes,
                          face_bytes,
                          whisker_bytes,
                          lear_bytes,
                          rear_bytes,
                          leye_bytes,
                          reye_bytes,
                          nose_bytes
                          ))
        _id = cur.fetchone()[0]
        if _id:
            conn.commit()
            print("Committed --> " + str(_id))
        else:
            ret = -1
            status = "Failed to insert data."

    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        status = str(error)
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def create_compressed_table():
    ret = 0
    status = "Success"
    conn = None

    sql = sql = "CREATE TABLE compressed_images ( id text PRIMARY KEY," \
                "name text, " \
                "image text, " \
                "face text, " \
                "whisker text, " \
                "l_ear text, " \
                "r_ear text, " \
                "l_eye text, " \
                "r_eye text, " \
                "nose text);"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        status = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, status

