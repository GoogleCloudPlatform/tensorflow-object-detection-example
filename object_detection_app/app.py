#!/usr/bin/python
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


from wtforms import ValidationError
from wtforms import Form
from werkzeug.datastructures import CombinedMultiDict
from utils import label_map_util
import tensorflow as tf
from PIL import ImageDraw
from PIL import Image
import numpy as np
from flask_wtf.file import FileField
from flask import url_for
from flask import request
from flask import render_template
from flask import redirect
from flask import jsonify
from flask import Flask
import base64
import cStringIO
import sys
import tempfile

MODEL_BASE = '/opt/models/research'  # VM内のtensorflowまでのpath
sys.path.append(MODEL_BASE)
sys.path.append(MODEL_BASE + '/object_detection')
sys.path.append(MODEL_BASE + '/slim')


app = Flask(__name__)


PATH_TO_CKPT = '/opt/graph_def/frozen_inference_graph.pb'  # model file
PATH_TO_LABELS = MODEL_BASE + \
    '/object_detection/data/mscoco_label_map.pbtxt'  # map file

content_types = {'jpg': 'image/jpeg',
                 'jpeg': 'image/jpeg',
                 'png': 'image/png'}  # 送られてくるCOntent type
extensions = sorted(content_types.keys())  # 上記の拡張子をsort


def is_image():  # 画像かどうか判断
    def _is_image(form, field):
        if not field.data:  # もしfield にdataがなかったら
            raise ValidationError()  # validation error
        # fieldにデータがあったら，filenameを拡張子でsplitして，拡張子以前のファイル名を全て小文字にする
        # そして指定した拡張子がなかった場合
        elif field.data.filename.split('.')[-1].lower() not in extensions:
            raise ValidationError()  # validation error
    return _is_image  # 全部クリアしたらimageですよ


class PhotoForm(Form):  # flask-wtf というflaskの拡張．FIeldをいい感じに作ってくれるくん
    input_photo = FileField(
        'File extension should be: %s (case-insensitive)' % ', '.join(extensions),
        validators=[is_image()])


class ObjectDetector(object):  # 物体検出を行うclass

    def __init__(self):
        self.detection_graph = self._build_graph()
        self.sess = tf.Session(graph=self.detection_graph)

        label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
        categories = label_map_util.convert_label_map_to_categories(
            label_map, max_num_classes=90, use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)

    def _build_graph(self):
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        return detection_graph

    def _load_image_into_numpy_array(self, image):
        (im_width, im_height) = image.size
        return np.array(image.getdata()).reshape(
            (im_height, im_width, 3)).astype(np.uint8)

    def detect(self, image):  # 実際にdetect する部分
        image_np = self._load_image_into_numpy_array(image)
        image_np_expanded = np.expand_dims(image_np, axis=0)

        graph = self.detection_graph
        image_tensor = graph.get_tensor_by_name('image_tensor:0')
        boxes = graph.get_tensor_by_name('detection_boxes:0')
        scores = graph.get_tensor_by_name('detection_scores:0')
        classes = graph.get_tensor_by_name('detection_classes:0')
        num_detections = graph.get_tensor_by_name('num_detections:0')

        (boxes, scores, classes, num_detections) = self.sess.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})

        boxes, scores, classes, num_detections = map(
            np.squeeze, [boxes, scores, classes, num_detections])

        return boxes, scores, classes.astype(int), num_detections


def draw_bounding_box_on_image(image, box, color='red', thickness=4):  # 画像の上に検出boxを書くやつ
    draw = ImageDraw.Draw(image)
    im_width, im_height = image.size
    ymin, xmin, ymax, xmax = box
    (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                  ymin * im_height, ymax * im_height)
    draw.line([(left, top), (left, bottom), (right, bottom),
               (right, top), (left, top)], width=thickness, fill=color)


def encode_image(image):  # base64にdecodeする
    image_buffer = cStringIO.StringIO()
    image.save(image_buffer, format='PNG')
    imgstr = 'data:image/png;base64,{:s}'.format(
        base64.b64encode(image_buffer.getvalue()))
    return imgstr


def detect_objects(image_path):  # 物体検出関数
    image = Image.open(image_path).convert('RGB')  # image_pathで渡されたimageをoepn
    boxes, scores, classes, num_detections = client.detect(
        image)  # 上記classを実行して帰ってくる値を格納
    image.thumbnail((480, 480), Image.ANTIALIAS)  # 画像サイズをアンチエイリアスで縮小

    new_images = {}
    for i in range(num_detections):  # 物体検出したシリーズ
        if scores[i] < 0.7:  # 0.7以下なら何も言わない
            continue
        cls = classes[i]  # クラス（分類）を格納
        if cls not in new_images.keys():
            new_images[cls] = image.copy()
        draw_bounding_box_on_image(new_images[cls], boxes[i],
                                   thickness=int(scores[i]*10)-4)

    result = {}
    result['original'] = encode_image(image.copy())  # originalはコピーする

    for cls, new_image in new_images.iteritems():
        category = client.category_index[cls]['name']
        result[category] = encode_image(new_image)  # カテゴリごとに画像を生成

    return result


@app.route('/')
def root():
    return ('roooootだよ')


@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        with tempfile.NamedTemporaryFile() as temp:
            form.input_photo.data.save(temp)
            temp.flush()
            result = detect_objects(temp.name)

        response = {
            'status': 'success',
            'detection': result
        }
        return jsonify(response)
    else:
        response = {
            'status': 'faild',
        }
        return jsonify()


client = ObjectDetector()  # initialize class


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
