import os
import cv2
import shutil
import tempfile
import pandas as pd
from PIL import Image
from utils import lion_model, extract_lion_data


if __name__ == "__main__":
    data_dir = 'data'
    face_dir = os.path.join(data_dir, 'face')
    whisker_dir = os.path.join(data_dir, 'whisker')
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
    if os.path.exists('face.csv'):
        os.remove('face.csv')
    if os.path.exists('whisker.csv'):
        os.remove('whisker.csv')
    os.mkdir(data_dir)
    os.mkdir(face_dir)
    os.mkdir(whisker_dir)
    face_df = pd.DataFrame(columns=['Image', 'Id'])
    whisker_df = pd.DataFrame(columns=['Image', 'Id'])
    source_dir = 'Preprocessed_Images'
    lion_name_dirs = os.listdir(source_dir)
    for lion_name_dir in lion_name_dirs:
        root_dir = os.path.join(source_dir, lion_name_dir)
        lion_images = os.listdir(root_dir)
        for lion_image in lion_images:
            lion_image_path = os.path.join(root_dir, lion_image)
            prefix = ''.join(lion_image.split('.')[:-1])
            ext = lion_image.split('.')[-1]
            lion_face_filename = lion_name_dir + '_' + prefix + '_face.' + ext
            lion_face_filepath = os.path.join(face_dir, lion_face_filename)
            lion_whisker_filename = lion_name_dir + '_' + prefix + '_whisker.' + ext
            lion_whisker_filepath = os.path.join(whisker_dir, lion_whisker_filename)
            tmp_dir = None
            try:
                tmp_dir = tempfile.mkdtemp()
                pil_img = Image.open(lion_image_path)
                src = cv2.imread(lion_image_path)
                temp_image = src.copy()
                coordinates, whisker_cords, face_cords, status = lion_model.get_coordinates(lion_image_path,
                                                                                            'temp_lion')
                if status != "Success":
                    continue
                lion_path, face_path, whisker_path, lear_path, rear_path, \
                    leye_path, reye_path, nose_path, face_embedding, whisker_embedding = \
                    extract_lion_data(face_cords, 'temp_lion', pil_img, coordinates, tmp_dir, temp_image)
                if len(face_path) > 0:
                    shutil.copy(face_path, lion_face_filepath)
                    face_df.loc[len(face_df.index)] = [lion_face_filename, lion_name_dir]
                if len(whisker_path) > 0:
                    shutil.copy(whisker_path, lion_whisker_filepath)
                    whisker_df.loc[len(whisker_df.index)] = [lion_whisker_filename, lion_name_dir]
            except Exception as e:
                if tmp_dir and os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir)
                continue
    face_df.to_csv('face.csv', index=False)
    whisker_df.to_csv('whisker.csv', index=False)
