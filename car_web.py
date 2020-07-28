#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
该程序是通过接口的方式来调用汽车识别模型的内容，并返回识别的结果；
接口的入口通过POST方式来提交识别的内容，因为只是支持汉字的内容，为了保证接口正常处理，
需要把汉字的内容进行encode编码，所以接收后会产先进行decode，如果出现错识，则需要在提交的时候处理encode 
返回的结果不进行encode处理；

method = POST
nertxt = encode("这是需要识别的文本内容")
return info:
{
    "code":"00XX/90XX",如果是00开头，则是处理正常的返回；如果90开头，则是错误信息
    "info":"处理完成/",
    "jresult":{
        "VEC":{"宝马":1,"奔驰":2},
        "MOD":{"自动档":2, "手动档":3},
        "FOC":{"贷款":2,"支付宝":2},
        "MOB":{"13910001010":1},
        "NAME":{"张先生":1,"李先生",1},
        "PRICE":{"20万":1, "1000":1, "120000":1}
    }
}

'''
from flask import Flask, request, render_template
from pathlib import Path
from ex_car_info import ex_car_info
from flask import Response, json
import re

app = Flask(__name__)
app.debug = True # 修改代码自动重启

@app.route('/toIndex')
def to_index():
    car_txt = Path("./car_txt.txt").read_text()
    return render_template("index.html", car_txt=car_txt)


#此接口不支持文件上传，因为不想内容落在本地后处理，后期可能会遇到处理并发性的问题，
# 看实际情况再解决，目前一个NCR的处理字符数最多为200个，所以需要把文件切割成多个小文件进行处理；
@app.route('/car-info-ner',methods=("POST","GET")) 
def car_info_ner(): 			
    car_txt = request.form.get('car_txt')
    ex = ex_car_info()
    result = ex.get_Car_Ner_Result(car_txt)
    return Response(json.dumps(result),content_type='application/json')

if __name__ == '__main__':
    app.run("0.0.0.0",5000)