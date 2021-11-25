import base64
import string
import random
import pandas as pd
from scipy import spatial
from datetime import datetime, timezone

import psycopg2

from config import is_whiskers, threshold
from train_utils import embedding_dim

# handle = "localhost"
handle = "34.93.181.52"
database = "telio_lions"



def get_base64_str(image):
    try:
        with open(image, "rb") as imageFile:
            base64_str = str(base64.b64encode(imageFile.read()))[2:-1]
        return base64_str
    except Exception as e:
        return ''


def aggregate(x):
    ret_row = x.iloc[0]
    ref_datetime = datetime.fromisoformat('1970-01-01 00:00:00')
    for index, row in x.iterrows():
        click_date = row['click_date']
        if click_date > ref_datetime:
            ref_datetime = click_date
            ret_row = row
    return ret_row


def get_all_lions():
    ret = 0
    conn = None
    rv = dict()
    sql = "SELECT name, sex, status, click_date, upload_date, latitude, longitude, face FROM lion_data;"
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
        df = df.groupby(['name'])['sex', 'status', 'click_date', 'upload_date', 'latitude', 'longitude', 'face']. \
            apply(lambda x: aggregate(x)).reset_index()
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


def get_current_count():
    ret = dict()
    r = 0
    male_lions = 0
    female_lions = 0
    unknown_sex_lions = 0
    alive_lions = 0
    dead_lions = 0
    conn = None
    sql = "select sex, status from (select sex, status, row_number() over " \
          "(partition by name order by name asc) as row_number from lion_data) temp where row_number=1;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        records = cur.fetchall()
        cur.close()
        total_lions = len(records)
        for record in records:
            sex = record[0]
            status = record[1]
            if sex == 'M':
                male_lions += 1
            elif sex == 'F':
                female_lions += 1
            else:
                unknown_sex_lions += 1
            if status == 'D':
                dead_lions += 1
            else:
                alive_lions += 1
        ret['total'] = str(total_lions)
        ret['male'] = str(male_lions)
        ret['female'] = str(female_lions)
        ret['unknown_sex'] = str(unknown_sex_lions)
        ret['alive'] = str(alive_lions)
        ret['dead'] = str(dead_lions)
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = dict()
        r = -1
    finally:
        if conn is not None:
            conn.close()
        return ret, r


def get_lion_parameter(lion_id, parameter_name):
    ret = 0
    ret_str = ""
    conn = None
    sql = "SELECT " + parameter_name + " FROM lion_data WHERE id = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_id,))
        records = cur.fetchall()
        cur.close()
        if len(records) == 1:
            ret_str = str(records[0][0])
        else:
            ret = -1
            ret_str = 'Not Found'
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def get_user_parameter(username, parameter_name):
    ret = 0
    ret_str = ""
    conn = None
    sql = "SELECT " + parameter_name + " FROM user_data WHERE username = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (username,))
        records = cur.fetchall()
        cur.close()
        if len(records) == 1:
            ret_str = str(records[0][0])
        else:
            ret = -1
            ret_str = 'Not Found'
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def delete_lion_id(username, lion_id):
    role, ret = get_user_parameter(username, 'role')
    if role != 'admin':
        return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "DELETE FROM lion_data WHERE id = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_id,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def delete_lion_name(username, lion_name):
    role, ret = get_user_parameter(username, 'role')
    if role != 'admin':
        return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "DELETE FROM lion_data WHERE name = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_name,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def delete_user(username1, username2, password2):
    role, ret = get_user_parameter(username1, 'role')
    if role != 'admin':
        ret, rr = login(username2, password2)
        if ret is False:
            return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "DELETE FROM user_data WHERE username = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (username2,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def update_user_parameter(who, whose, password, var_name, var_value):
    role, ret = get_user_parameter(who, 'role')
    if role != 'admin':
        ret, rr = login(whose, password)
        if ret is False:
            return "Insufficient Permissions", -1
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "UPDATE user_data SET " + var_name + " = %s WHERE username = %s;"

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (var_value, whose,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def update_lion_name_parameter(lion_name, var_name, var_value):
    ret = 0
    ret_str = "Success"
    conn = None
    sql = "UPDATE lion_data SET " + var_name + " = %s WHERE name = %s;"

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (var_value, lion_name,))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return ret_str, ret


def get_user_info(username):
    rv = dict()
    ret = 0
    conn = None
    sql = """SELECT username, name, email, phone, role FROM user_data WHERE username = %s;"""

    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (username,))
        record = cur.fetchall()[0]
        rv['username'] = record[0]
        rv['name'] = record[1]
        rv['email'] = record[2]
        rv['phone'] = record[3]
        rv['role'] = str(record[4])
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        rv = dict()
    finally:
        if conn is not None:
            conn.close()
        return rv, ret

def get_data(offset, count, loggedinuser):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT username, name, email, phone, role FROM user_data WHERE username !='" + loggedinuser + "' ;"
    try:
        conn = psycopg2.connect(host=handle,
                                        database=database,
                                        user="postgres",
                                        password="admin")
        cur = conn.cursor()
        cur.execute(sql, (offset, count,))
        records = cur.fetchall()
        user_instances = list()
        for record in records:
            one_record = dict()
            one_record['username'] = record[0]
            one_record['name'] = record[1]
            one_record['email'] = record[2]
            one_record['phone'] = record[3]
            one_record['role'] = str(record[4])
            user_instances.append(one_record)
        rv['users'] = user_instances
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
            print("DB Error: " + str(error))
            ret = -1
            rv = dict()
    finally:
        if conn is not None:
            conn.close()
            return rv, ret



def get_lion_id_info(lion_id):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT id, name, sex, status, click_date, upload_date, latitude, longitude, " \
          "face, whisker, l_ear, r_ear, l_eye, r_eye, nose FROM lion_data WHERE id = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_id,))
        records = cur.fetchall()
        if len(records) != 1:
            ret = -1
        else:
            record = records[0]
            rv['id'] = record[0]
            rv['name'] = record[1]
            rv['sex'] = record[2]
            rv['status'] = record[3]
            rv['click_date'] = str(record[4])
            rv['upload_date'] = str(record[5])
            rv['latitude'] = record[6]
            rv['longitude'] = record[7]
            #rv['image'] = record[8]
            rv['face'] = record[8]
            rv['whisker'] = record[9]
            rv['l_ear'] = record[10]
            rv['r_ear'] = record[11]
            rv['l_eye'] = record[12]
            rv['r_eye'] = record[13]
            rv['nose'] = record[14]
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


def get_lion_name_info(lion_name):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT id, name, sex, status, click_date, upload_date, latitude, longitude, " \
          "face, whisker, l_ear, r_ear, l_eye, r_eye, nose FROM lion_data WHERE name = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_name,))
        records = cur.fetchall()
        lions_instances = list()
        for record in records:
            one_record = dict()
            one_record['id'] = record[0]
            one_record['name'] = record[1]
            one_record['sex'] = record[2]
            one_record['status'] = record[3]
            one_record['click_date'] = str(record[4])
            one_record['upload_date'] = str(record[5])
            one_record['latitude'] = record[6]
            one_record['longitude'] = record[7]
            # one_record['image'] = record[8]
            one_record['face'] = record[8]
            one_record['whisker'] = record[9]
            one_record['l_ear'] = record[10]
            one_record['r_ear'] = record[11]
            one_record['l_eye'] = record[12]
            one_record['r_eye'] = record[13]
            one_record['nose'] = record[14]
            lions_instances.append(one_record)
        rv['lions_instances'] = lions_instances
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret



def get_lion_gender_info(lion_gender):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT id, name, sex, status, click_date, upload_date, latitude, longitude, " \
          "face, whisker, l_ear, r_ear, l_eye, r_eye, nose FROM lion_data WHERE sex = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_gender,))
        records = cur.fetchall()
        lions_instances = list()
        for record in records:
            one_record = dict()
            one_record['id'] = record[0]
            one_record['name'] = record[1]
            one_record['sex'] = record[2]
            one_record['status'] = record[3]
            one_record['click_date'] = str(record[4])
            one_record['upload_date'] = str(record[5])
            one_record['latitude'] = record[6]
            one_record['longitude'] = record[7]
            # one_record['image'] = record[8]
            one_record['face'] = record[8]
            one_record['whisker'] = record[9]
            one_record['l_ear'] = record[10]
            one_record['r_ear'] = record[11]
            one_record['l_eye'] = record[12]
            one_record['r_eye'] = record[13]
            one_record['nose'] = record[14]
            lions_instances.append(one_record)
        rv['lions_instances'] = lions_instances
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret


def get_lion_status_info(lion_status):
    rv = dict()
    ret = 0
    conn = None
    sql = "SELECT id, name, sex, status, click_date, upload_date, latitude, longitude, " \
          "face, whisker, l_ear, r_ear, l_eye, r_eye, nose FROM lion_data WHERE status = %s;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (lion_status,))
        records = cur.fetchall()
        lions_instances = list()
        for record in records:
            one_record = dict()
            one_record['id'] = record[0]
            one_record['name'] = record[1]
            one_record['sex'] = record[2]
            one_record['status'] = record[3]
            one_record['click_date'] = str(record[4])
            one_record['upload_date'] = str(record[5])
            one_record['latitude'] = record[6]
            one_record['longitude'] = record[7]
            # one_record['image'] = record[8]
            one_record['face'] = record[8]
            one_record['whisker'] = record[9]
            one_record['l_ear'] = record[10]
            one_record['r_ear'] = record[11]
            one_record['l_eye'] = record[12]
            one_record['r_eye'] = record[13]
            one_record['nose'] = record[14]
            lions_instances.append(one_record)
        rv['lions_instances'] = lions_instances
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
    finally:
        if conn is not None:
            conn.close()
        return rv, ret

def get_all_lion_embeddings():
    ret = list()
    conn = None
    sql = "SELECT id, name, face_embedding, whisker_embedding FROM lion_data;"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = list()
    finally:
        if conn is not None:
            conn.close()
        return ret


def match_lion(face_embedding, whisker_embedding, ret):
    ret['threshold'] = threshold.get_threshold()
    match_data = list()
    embeddings = get_all_lion_embeddings()
    if len(face_embedding) == 0:
        face_emb = [float(0.0) for _ in range(0, embedding_dim, 1)]
    else:
        face_emb = list()
        for x in face_embedding.split(','):
            try:
                face_emb.append(float(x))
            except Exception as e:
                print(x)
                face_emb.append(float('0.0'))
    if len(whisker_embedding) == 0:
        whisker_emb = [float(0.0) for _ in range(0, embedding_dim, 1)]
    else:
        whisker_emb = list()
        for x in whisker_embedding.split(','):
            try:
                whisker_emb.append(float(x))
            except Exception as e:
                print(x)
                whisker_emb.append(float('0.0'))
    no_face_or_whisker = 1
    for embedding in embeddings:
        ref_id = embedding[0]
        ref_lion_name = embedding[1]
        ref_face_embedding = list()
        for x in embedding[2].split(','):
            try:
                ref_face_embedding.append(float(x))
            except Exception as e:
                print(x)
                ref_face_embedding.append(float('0.0'))
        ref_whisker_embedding = list()
        for x in embedding[3].split(','):
            try:
                ref_whisker_embedding.append(float(x))
            except Exception as e:
                print(x)
                ref_whisker_embedding.append(float('0.0'))
        face_distance = spatial.distance.cosine(ref_face_embedding, face_emb)
        whisker_distance = spatial.distance.cosine(ref_whisker_embedding, whisker_emb)
        if is_whiskers:
            d = face_distance
        else:
            d = whisker_distance
        if d != 0:
            no_face_or_whisker = 0
            match_data.append((ref_id, ref_lion_name, face_distance, whisker_distance))

    if is_whiskers:
        index = 3
    else:
        index = 2

    if len(match_data) == 0:
        if no_face_or_whisker:
            ret['type'] = 'Unknown'
            ret['distance'] = 1.00
        else:
            ret['type'] = 'New'
            ret['distance'] = threshold.get_threshold()
    else:
        match_data.sort(key=lambda x1: x1[index])

    print(match_data)

    if len(match_data) > 0:
        _1st_match = match_data[0]
        d_1st = _1st_match[index]
        if d_1st <= threshold.get_threshold():
            ret['type'] = 'Similar'
            ret['similar'] = [{'id': _1st_match[0], 'name': _1st_match[1]}]
            ret['distance'] = round(d_1st, 2)
        else:
            ret['type'] = 'New'
            ret['distance'] = round(d_1st, 2)
    if len(match_data) > 1:
        _2nd_match = match_data[1]
        d_2nd = _2nd_match[index]
        if d_2nd <= threshold.get_threshold():
            ret['similar'].append({'id': _2nd_match[0], 'name': _2nd_match[1]})
            ret['distance'] = round(d_2nd, 2)
    if len(match_data) > 2:
        _3rd_match = match_data[2]
        d_3rd = _3rd_match[index]
        if d_3rd <= threshold.get_threshold():
            ret['similar'].append({'id': _3rd_match[0], 'name': _3rd_match[1]})
            ret['distance'] = round(d_3rd, 2)
    return ret


def insert_lion_data(_id, name,
                     sex, life_status,
                     utc_click_datetime,
                     lat, lon,
                     image, face,
                     whisker, lear,
                     rear, leye,
                     reye, nose,
                     face_embedding,
                     whisker_embedding,hash_value):
    ret = 0
    status = "Success"
    conn = None
    try:
        upload_date = datetime.now(timezone.utc)
        click_date = utc_click_datetime
        try:
            image_bytes = get_base64_str(image)
        except Exception as e:
            image_bytes = ''
            pass
        face_bytes = get_base64_str(face)
        whisker_bytes = get_base64_str(whisker)
        try:
            lear_bytes = get_base64_str(lear)
        except Exception as e:
            lear_bytes = ''
            pass
        try:
            rear_bytes = get_base64_str(rear)
        except Exception as e:
            rear_bytes = ''
            pass
        try:
            leye_bytes = get_base64_str(leye)
        except Exception as e:
            leye_bytes = ''
            pass
        try:
            reye_bytes = get_base64_str(reye)
        except Exception as e:
            reye_bytes = ''
            pass
        try:
            nose_bytes = get_base64_str(nose)
        except Exception as e:
            nose_bytes = ''
            pass

        try:
            str_hash_value = str(hash_value)
        except Exception as e:
            str_hash_value = ''
            pass

        sql = """INSERT INTO lion_data VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING ID;"""
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_id,
                          name,
                          sex,
                          life_status,
                          click_date,
                          upload_date,
                          lat,
                          lon,
                          image_bytes,
                          face_bytes,
                          whisker_bytes,
                          lear_bytes,
                          rear_bytes,
                          leye_bytes,
                          reye_bytes,
                          nose_bytes,
                          face_embedding,
                          whisker_embedding,str_hash_value))
        _id = cur.fetchone()[0]
        if _id:
            conn.commit()
            print("Committed --> " + str(_id))
        else:
            ret = -1
            status = "Failed to insert lion data."
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        status = str(error)
    finally:
        if conn is not None:
            conn.close()
        return ret, status


def drop_table(table_name):
    ret = 0
    status = "Success"
    conn = None
    sql = "DROP TABLE " + table_name + ";"
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


def truncate_table(table_name):
    ret = 0
    status = "Success"
    conn = None
    sql = "TRUNCATE " + table_name + ";"
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


def create_user_data_table():
    ret = 0
    status = "Success"
    conn = None
    sql = "CREATE TABLE user_data (username text PRIMARY KEY, " \
          "name text, " \
          "email text, " \
          "phone text, " \
          "role text, " \
          "password text);"
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


def create_lion_data_table():
    ret = 0
    status = "Success"
    conn = None
    sql = "CREATE TABLE lion_data (id text PRIMARY KEY, " \
          "name text, " \
          "sex text, " \
          "status text, " \
          "click_date timestamp without time zone, " \
          "upload_date timestamp without time zone, " \
          "latitude text, " \
          "longitude text, " \
          "image text, " \
          "face text, " \
          "whisker text, " \
          "l_ear text, " \
          "r_ear text, " \
          "l_eye text, " \
          "r_eye text, " \
          "nose text, " \
          "face_embedding text, " \
          "whisker_embedding text, " \
          "hash_value text);"
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


def if_table_exists(table_name):
    ret = False
    conn = None
    sql = "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = '" + table_name + "');"""
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        ret = cur.fetchone()[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = False
    finally:
        if conn is not None:
            conn.close()
        return ret

def verify_user(user):
    conn = None
    sql = "SELECT username FROM user_data "
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                            password="admin")
        cur = conn.cursor()
        cur.execute(sql)
        records = cur.fetchall()
        cur.close()
        df = pd.DataFrame(records,columns = ['username'])
        user_list = df['username'].tolist()
        print("Username is",user)
        if user in user_list:
            ret = 0
            ret_str= ''
            print("User is found")
        else:
            ret = -1
            print("User is not found ")
            ret_str = "User not found"
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret_str = str(error)
        ret = -1
    finally:
        if conn is not None:
            conn.close()
            return ret ,ret_str

def admin_reset_password(_admin_username, _admin_password, _username):
    role, ret = get_user_parameter(_admin_username, 'role')
    #verify user
    u_ret,ret_s = verify_user(_username)
    print(u_ret,ret_s)
    if role != 'admin':
        return "Insufficient Permissions",-1
    else:
        ret, rr = login(_admin_username, _admin_password)
        if ret is False:
            return "Invalid Admin-name or Invalid Password", -1
        else:
            if u_ret == -1:
                return "Invalid User", -1
            else:
                n = 10
                _pwd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
                ret = 0
                ret_str = _pwd
                conn = None
                sql = "UPDATE user_data SET password = %s WHERE username = %s;"

                try:
                    conn = psycopg2.connect(host=handle,
                                            database=database,
                                            user="postgres",
                                            password="admin")
                    cur = conn.cursor()
                    cur.execute(sql, (_pwd, _username,))
                    conn.commit()
                    cur.close()
                except (Exception, psycopg2.DatabaseError) as error:
                    print("DB Error: " + str(error))
                    ret_str = str(error)
                    ret = -1
                finally:
                    if conn is not None:
                        conn.close()
                    return ret_str, ret

    # if role != 'admin':
    #     return "Insufficient Permissions"
    # else:
    #     ret, rr = login(_admin_username, _admin_password)
    #     if ret is False:
    #         r = -1
    #         return "Invalid Admin-name or Invalid Password",r
    #     else:
    #         n = 10
    #         _pwd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
    #         ret = 0
    #         ret_str = _pwd
    #         conn = None
    #         sql = "UPDATE user_data SET password = %s WHERE username = %s;"
    #
    #         try:
    #             conn = psycopg2.connect(host=handle,
    #                                     database=database,
    #                                     user="postgres",
    #                                     password="admin")
    #             cur = conn.cursor()
    #             cur.execute(sql, (_pwd, _username,))
    #             conn.commit()
    #             cur.close()
    #         except (Exception, psycopg2.DatabaseError) as error:
    #             print("DB Error: " + str(error))
    #             ret_str = str(error)
    #             ret = -1
    #         finally:
    #             if conn is not None:
    #                 conn.close()
    #             return ret_str, ret

def modify_password(_un, _old_pw, _new_pw):
    ret, rr = login(_un, _old_pw)
    if ret is True:
        ret_str, ret = update_user_parameter('admin',_un, _old_pw, 'password', _new_pw)
    else:
        ret_str = "Invalid existing password."
        ret = -1
    return ret, ret_str


def login(un, pwd):
    ret = True
    role = ''
    conn = None
    sql = """select password from user_data where username = %s"""
    # sql = "update password from user_data where username = %s"
    try:
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (un,))
        record = cur.fetchall()
        if len(record) != 1:
            ret = False
            role = ''
        else:
            record = record[0]
            if str(record[0]) != pwd:
                ret = False
                role = ''
            else:
                role, ret_code = get_user_parameter(un, 'role')
                if ret_code != 0:
                    ret = False
                    role = ''
                else:
                    ret = True
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = False
        role = ''
    finally:
        if conn is not None:
            conn.close()
        return ret, role


def create_new_user(_name, _email, _phone, _role, _un):
    ret = 0
    status = "Success"
    conn = None
    _pwd = ''
    sql = """INSERT INTO user_data(username, name, email, phone, role, password) 
             VALUES(%s,%s,%s,%s,%s,%s) RETURNING username;"""
    try:
        n = 10
        _pwd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))
        conn = psycopg2.connect(host=handle,
                                database=database,
                                user="postgres",
                                password="admin")
        cur = conn.cursor()
        cur.execute(sql, (_un, _name, _email, _phone, _role, _pwd,))
        un = cur.fetchone()[0]
        if un:
            conn.commit()
            print("Committed --> " + str(un))
        else:
            ret = -1
            status = "Failed to commit."
    except (Exception, psycopg2.DatabaseError) as error:
        print("DB Error: " + str(error))
        ret = -1
        status = str(error)
        _pwd = ''
    finally:
        if conn is not None:
            conn.close()
        return _pwd, ret, status
