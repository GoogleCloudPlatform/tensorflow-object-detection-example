#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

MODEL_URL = 'http://download.tensorflow.org/models/object_detection/faster_rcnn_resnet50_coco_2018_01_28.tar.gz'

import base64
import io
import os
import pathlib
import sys
import tempfile

MODEL_BASE = '/opt/models/research'
sys.path.append(MODEL_BASE)
sys.path.append(MODEL_BASE + '/object_detection')
sys.path.append(MODEL_BASE + '/slim')
PATH_TO_LABELS = MODEL_BASE + '/object_detection/data/mscoco_label_map.pbtxt'

from decorator import requires_auth
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_wtf.file import FileField
import numpy as np
from PIL import Image
from PIL import ImageDraw
import tensorflow as tf
from utils import label_map_util
from werkzeug.datastructures import CombinedMultiDict
from wtforms import Form
from wtforms import ValidationError

# Patch the location of gfile
tf.gfile = tf.io.gfile


app = Flask(__name__)


@app.before_request
@requires_auth
def before_request():
  pass



content_types = {'jpg': 'image/jpeg',
                 'jpeg': 'image/jpeg',
                 'png': 'image/png'}
extensions = sorted(content_types.keys())


def is_image():
  def _is_image(form, field):
    if not field.data:
      raise ValidationError()
    elif field.data.filename.split('.')[-1].lower() not in extensions:
      raise ValidationError()

  return _is_image


class PhotoForm(Form):
  input_photo = FileField(
      'File extension should be: %s (case-insensitive)' % ', '.join(extensions),
      validators=[is_image()])


class ObjectDetector(object):

  def __init__(self):

    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(
        label_map, max_num_classes=90, use_display_name=True)
    self.category_index = label_map_util.create_category_index(categories)

    model_url = MODEL_URL
    base_url = os.path.dirname(model_url)+"/"
    model_file = os.path.basename(model_url)
    model_name = os.path.splitext(os.path.splitext(model_file)[0])[0]
    model_dir = tf.keras.utils.get_file(
        fname=model_name, origin=base_url + model_file, untar=True)
    model_dir = pathlib.Path(model_dir)/"saved_model"

    model = tf.saved_model.load(str(model_dir))
    model = model.signatures['serving_default']
    self.model = model

  def _load_image_into_numpy_array(self, image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)

  def detect(self, image):
    image_np = self._load_image_into_numpy_array(image)
    input_tensor = tf.convert_to_tensor(image_np)
    input_tensor = input_tensor[tf.newaxis,...]
    output_dict = self.model(input_tensor)

    num_detections = int(output_dict.pop('num_detections'))
    output_dict = {key:value[0, :num_detections].numpy() 
                   for key,value in output_dict.items()}
    boxes = output_dict['detection_boxes']
    classes = output_dict['detection_classes'].astype(np.int64)
    scores = output_dict['detection_scores']
   
    return boxes, scores, classes, num_detections


def draw_bounding_box_on_image(image, box, color='red', thickness=4):
  draw = ImageDraw.Draw(image)
  im_width, im_height = image.size
  ymin, xmin, ymax, xmax = box
  (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                ymin * im_height, ymax * im_height)
  draw.line([(left, top), (left, bottom), (right, bottom),
             (right, top), (left, top)], width=thickness, fill=color)


def encode_image(image):
  image_buffer = io.BytesIO()
  image.save(image_buffer, format='PNG')
  imgstr = 'data:image/png;base64,{:s}'.format(
      base64.b64encode(image_buffer.getvalue()).decode().replace("'", ""))
  return imgstr


def detect_objects(image_path):
  image = Image.open(image_path).convert('RGB')
  boxes, scores, classes, num_detections = client.detect(image)
  image.thumbnail((480, 480), Image.ANTIALIAS)

  new_images = {}
  for i in range(num_detections):
    if scores[i] < 0.7: continue
    cls = classes[i]
    if cls not in new_images.keys():
      new_images[cls] = image.copy()
    draw_bounding_box_on_image(new_images[cls], boxes[i],
                               thickness=int(scores[i]*10)-4)

  result = {}
  result['original'] = encode_image(image.copy())

  for cls, new_image in new_images.items():
    category = client.category_index[cls]['name']
    result[category] = encode_image(new_image)

  return result


@app.route('/')
def upload():
  photo_form = PhotoForm(request.form)
  return render_template('upload.html', photo_form=photo_form, result={})


@app.route('/post', methods=['GET', 'POST'])
def post():
  form = PhotoForm(CombinedMultiDict((request.files, request.form)))
  if request.method == 'POST' and form.validate():
    with tempfile.NamedTemporaryFile() as temp:
      form.input_photo.data.save(temp)
      temp.flush()
      result = detect_objects(temp.name)

    photo_form = PhotoForm(request.form)
    return render_template('upload.html',
                           photo_form=photo_form, result=result)
  else:
    return redirect(url_for('upload'))


client = ObjectDetector()


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80, debug=False)
