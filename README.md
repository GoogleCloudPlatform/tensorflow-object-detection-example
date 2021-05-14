# Control element detection app for vehicle's dashboards

This is the user interface section of our final project which connects to a pre-trained model and allows the user to run inference on a given image and view which control elements it presents.

## Products
- [TensorFlow][1]
- [TensorFlow Object Detection API][2]

## Language
- [Python][2]

[1]: https://www.tensorflow.org/
[2]: https://github.com/tensorflow/models/tree/master/research/object_detection
[3]: https://python.org

## Prerequisites
- Linux OS
- Docker installed


This application provides a simple user authentication mechanism.
 You can change the username and password by modifying the following
 part in `/opt/object_detection_app_p3/decorator.py`.

```
USERNAME = 'username'
PASSWORD = 'passw0rd'
```
## Run instructions
From this repository home directory, run:
```
sudo -i
```
You should now be using a root user, which allows you to invoke docker commands.
Now run the following and replace parameters as needed:
```
source setup.sh <MODEL_PATH> <LABEL_PATH> <DETECTION_THRESHOLD>
```
Relevant parameters are:
```
MODEL_PATH = Path to exported model directory (main directory, not saved_model). Default is my_model.
LABEL_PATH = Path to label map .pbtxt file. Default is label_map.pbtxt.
DETECTION_THRESHOLD = A float value which determines above which level of confidence detected elements should be displayed (between 0.0 and 1.0). Default is 0.5.
```

Example run line:
```
source setup.sh my_model_v2/ label_map.pbtxt 0.4
```

The last command outputs the application status, as in the
 following example:
```
Model path is my_model_v2/
Label map path is label_map.pbtxt
Control element detection threshold: 0.4
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:80/ (Press CTRL+C to quit)
```

You have to wait around 60secs for the application to finish loading
 the pretrained model graph. You'll see the message 
 `Running on http://0.0.0.0:80/ (Press CTRL+C to quit)` when it's ready.

Now you can access the user interface using a web browser.
 When you upload an image file with a `jpeg`, `jpg`, or `png` extension,
 the application shows the result of the control element detection inference.
 The inference may take up to 30 seconds, depending on the image.

The following example shows "ac_dial" in the image. You can also check
 other objects such as gear_lever, rpm_meter, ac_dial and emergency_button by clicking
 on their labels shown to the right of the image.

 ![](docs/img/screenshot.png)
