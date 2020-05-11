import os
import datetime
import yaml
from RCNN_Model_executor import run_model

from flask import Flask, render_template, redirect, url_for, request


result_folder = 'static/result'
download_folder = 'static/download'

if not os.path.exists(result_folder):
    os.makedirs(result_folder)

if not os.path.exists(download_folder):
    os.makedirs(download_folder)


app = Flask(__name__)

app.config['SERVER_BUSY'] = False
app.config['RESULT_FOLDER'] = result_folder
app.config['DOWNLOAD_FOLDER'] = download_folder
app.config['RESULT_NAME'] = 'None'


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/upload-files', methods=['GET', 'POST'])
def upload_files():

    if app.config['SERVER_BUSY']:
        return 'Server is busy, try again later!'

    app.config['SERVER_BUSY'] = True

    # getting video file
    video = request.files['video']
    if video:

        # filename
        exten = video.filename.split('.')[-1].lower()
        now = datetime.datetime.now()
        name = 'result_{}.{}'.format(now.strftime("%Y%m%d%H%M"), exten)
        app.config['RESULT_NAME'] = name

        video_path = os.path.abspath(os.path.join(app.config['DOWNLOAD_FOLDER'], video.filename))
        result_download_path = os.path.abspath(os.path.join(app.config['RESULT_FOLDER'], app.config['RESULT_NAME']))
        video.save(video_path)
    else:
        return redirect('/')

    # getting files with new logo
    banners_list = ['3_ms_logo', '1_gp_logo', '4_ns_logo', '5_pp_logo', '2_hk_logo', '6_pl_logo']
    replace_logo = {}
    for ban in banners_list:

        ban_logo = request.files[ban]
        if ban_logo:

            logo_path = os.path.abspath(os.path.join(app.config['DOWNLOAD_FOLDER'], ban_logo.filename))
            ban_logo.save(logo_path)
            replace_logo.update({int(ban.split('_')[0]): str(logo_path)})
    if len(replace_logo) <= 0:

        return redirect('/')
    time_intervals = []
    int_nums = int(request.form['interval_counter'])
    for int_num in range(1,int_nums+1):
        time_sec_1, time_sec_2 = 0,0
        name_1, name_2 = 'time_beg_{}'.format(int_num), 'time_end_{}'.format(int_num)

        time_1 = request.form[name_1]
        if time_1:
            try:
                min1, sec1 = time_1.split(':')
            except:
                min1, sec1 = 0,0
            time_sec_1 = int(min1) * 60 + int(sec1)

        time_2 = request.form[name_2]
        if time_2:
            try:
                min2, sec2 = time_2.split(':')
            except:
                min2, sec2 = 0, 0
            time_sec_2 = int(min2) * 60 + int(sec2)

        time_intervals.append([time_sec_1, time_sec_2])

    # updating configs
    with open('models/configurations/config.yml', 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)

    with open('models/configurations/config.yml', 'w') as file:

        data['video_path'] = video_path
        data['saving_link'] = result_download_path
        data['logos_path'] = replace_logo
        data['time_intervals'] = time_intervals
        yaml.dump(data, file)


    return render_template('processing.html')


@app.route('/processing', methods=['GET', 'POST'])
def processing():
    if app.config['RESULT_NAME'] == 'None':

        return redirect('/')

    # run model
    run_model()
    # getting saving link
    result_video_link = os.path.join(app.config['RESULT_FOLDER'], app.config['RESULT_NAME'])
    app.config['SERVER_BUSY'] = False
    return render_template('result.html', result_video_link=result_video_link)


@app.route('/finish', methods=['GET', 'POST'])
def end_session():

    if app.config['SERVER_BUSY']:
        return redirect('/')

    # deleting used files
    used_files = os.listdir(app.config['DOWNLOAD_FOLDER'])
    for file in used_files:
        os.unlink(os.path.join(app.config['DOWNLOAD_FOLDER'], file))

    app.config['RESULT_NAME'] = 'None'

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, port=8080)
