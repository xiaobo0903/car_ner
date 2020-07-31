#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
该程序是通过接口的方式来调用汽车识别模型的内容，并返回识别的结果；
接口的入口通过POST方式来提交识别的内容，因为只是支持汉字的内容，为了保证接口正常处理，
需要把汉字的内容进行encode编码，所以接收后会产先进行decode，如果出现错识，则需要在提交的时候处理encode 
返回的结果不进行encode处理；

method = POST/form
car_txt = "这是需要识别的文本内容"
return info:
{
	"app_name": "CAR_NER",
	"process_status": "complted",
	"result": {
		"matedate": {
			"FOC": {      #FOC是用户的关注内容
				"保养": 1, #后面的数字是出现的次数
				"保险": 1,
				"分期": 1,
				"置换": 1
			},
			"MOD": {       #FOC是用户的关注车型的内容
				"加长": 1,
				"动感": 1,
				"后备箱": 2,
				"脚垫": 1,
				"豪华": 3,
				"贴膜": 1,
				"轿跑": 1,
				"黑的": 2
			},
			"VEC": {       #FOC是用户的关注车的品牌和车
				"奔驰": 3
			}
		},
		"name": "张先生",
		"phone": "13520419261",
		"price": "39万|400万|200万|40万|392,800|424,800|449,800|394,800|45,000|357,800|658,000|15,000|46,000|354,800|31,300|13,000"
	},
	"task_id": "e94e0a70-e94c-41e4-b66a-d336b7135791",
	"time": "2020-07-31 09:21:33"
}

'''
from flask import Flask, request, render_template,Response, json
from pathlib import Path
from ex_car_info import ex_car_info
from celery import Celery
from celery import group
import redis
from celery.result import AsyncResult
from celery.result import GroupResult
import terminal_predict2 as tfner
import time

app = Flask(__name__)
app.debug = True # 修改代码自动重启
# 用以储存消息队列
r_redis = redis.StrictRedis(host="127.0.0.1", port=6379, db=3)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0' # broker是一个消息传输的中间件
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/1' # 任务执行器
celery_ = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
celery_.conf.update(app.config)

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
    nkey, slist = ex.ex_inStr(car_txt)
    #根据切分的内容，调用后台的并发处理框架进行并行处理
    task_id = call_ner_AI(slist)
    #把中间的过程写入到redis中；
    r_redis.set(task_id, json.dumps(nkey), ex=10800)
    return json.dumps(result_json(task_id, "submit"),ensure_ascii=False)
 
@celery_.task(name='my_background_task')
def my_background_task(item):
    avec, amod, afoc = tfner.predict(item)
    return avec, amod, afoc
 
def call_ner_AI(ilist):
    # 发送任务到celery,并返回任务ID,后续可以根据此任务ID获取任务结果
    jobs = group(my_background_task.s(item) for item in ilist)
    result = jobs.apply_async()
    print("the worker id is:")
    result.save()
    return result.id

#该部分只是简单实现了处理的流程，后期需要进行优化；现在如果需要获取最终的结果，必需采用轮询的方式进行处理，处理的效率很底，后期需要改为chord回调的方式进行处理;
@app.route('/get_task_result/<task_id>',methods=("POST","GET")) 
def get_task_result(task_id):
    g_result = GroupResult.restore(task_id, app=celery_)
    if g_result and g_result.successful():
        jvec = []
        jmod = []
        jfoc = []
        #通过get()取值只能够取一次，多次会阻塞(可能是设置问题)，没时间查找其它的方式，目前先把取出的值放入到redis中，然后从redis中再进行取值
        nlist = None
        if r_redis.get("result_"+task_id):
            nlist = json.loads(r_redis.get("result_"+task_id))
        else:
            nlist = g_result.get()
        
        r_redis.set("result_"+task_id, json.dumps(nlist), ex=10800)
        for avec, amod, afoc in nlist:
            jvec = jvec + avec
            jmod = jmod + amod
            jfoc = jfoc + afoc
        dvec = {}
        dmod = {}
        dfoc = {}
        dvec = tfner.stat_element_num(jvec)
        dmod = tfner.stat_element_num(jmod)
        dfoc = tfner.stat_element_num(jfoc)
        matedata = {}
        matedata["VEC"] = dvec
        matedata["MOD"] = dmod
        matedata["FOC"] = dfoc
        r_vel = json.loads(r_redis.get(task_id))
        r_vel["matedate"] = matedata
        ret = result_json(task_id, "complted")
        ret["result"] = r_vel        
        return json.dumps(ret,ensure_ascii=False)

    elif not g_result:
        return json.dumps(result_json(task_id, "NO_TASK"), ensure_ascii=False)
    else:
        return json.dumps(result_json(task_id, "Waitting"), ensure_ascii=False)

#获得结果的模版
def result_json(task_id, statue):
    result = {}
    ticks = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    result["time"] = str(ticks)
    result["process_status"] = statue
    result["app_name"] = "CAR_NER"
    result["task_id"] = task_id    
    return result

if __name__ == '__main__':
    app.run("0.0.0.0", 5000)

 