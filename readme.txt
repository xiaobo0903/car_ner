关于CAR_NER的安装说明:

一、运行环境描述：
1、redis服务：用于celery的并发处理；以及一些临时数据的保存使用；（临时数据的保存大约是在三个小时左右)
2、celery识别work：可以支持多台并行处理，越多系统的并发性能越好，可以根据实际情况进行配置；
3、web接口服务和celery的任务调度：这两个服务可以合并到一个环境中，完全是无状态的处理，所以可以对于这个环境可以进行线性的扩展，前面只需要增加一个类似SLB的负载均衡器即可；


二、运行环境要求:
linux:CentOS/Ubunutu
Python: >python3.5
tensorflow: ==1.15

1、redis服务集群的安装
apt install redis-server
安装完成后，需要记住IP地址及访问的端口信息,以配置其它程序进行访问；

2、WEB服务及celery任务调度的程序安装:
需要安装python3.5以上环境；
可以通过environment.yml进行环境的初始化，前提是需要安装conda;
首先安装anacoda虚拟运行环境,然后运行：
conda create -n ner python=3.6
python需要安装celery、flask、redis等主要模块；
进入ner虚拟环境
conda activate ner
conda install flask
conda install redis
conda install celery
conda install zmq
pip install tensorflow==1.15
可能还需要其它的软件，可以根据需要进行安装；

三、应用软件的安装:（每台机器都需要安装）

1、指定安装应用的目录（例如:/home)
2、进入应用安装目录下载应用程序
用git来下载安装相应的软件(这里不包含模型数据)
git clone https://github.com/xiaobo0903/car_ner.git
下载软件并会建立car_ner目录；

3、下载识别模型（从百度盘上下载，大约6G)

链接: https://pan.baidu.com/s/1VOf-JNGM_nJUIhgtwa9IXg  密码: 49wv

下载后拷到安装目录进行解压，会生成./car和chinese_L-12_H-768_A-12目录，./car目录下就是模型文件
tar xvf car.model.tar
会新建两个目录 car和 chinese_L-12_H-768_A-12

4、配置内容：
修改celery_web.py中关于redis的访问地址：
共有三个地方需要修改（根据实际配置情况，修改redis访问地址）

#################################################################################################
   r_redis = redis.StrictRedis(host="car-redis", port=6379, db=3)

   app.config['CELERY_BROKER_URL'] = 'redis://car-redis:6379/0' # broker是一个消息传输的中间件
   app.config['CELERY_RESULT_BACKEND'] = 'redis://car-redis:6379/1' # 任务执行器
#################################################################################################

修改terminal_predict2.py中的内容(第27行)，路径修改为实际的安装路径（后期需要改进）
######################################################################################
dir_name = '/Users/boxiao/car_ner'
######################################################################################

修改完成后，即环境的安装工作完成；

四、配置运行环境
1、设置PYTHONPATH=程序安装目录
export PYTHONPATH=/path/app
2、设置flask环境变量
export FLASK_APP=/path/app/celery_web.py
3、使用flask来启动web服务(至少选择一台服务器即可)
# flask run 
4、并发worker进程的启动(每台机器可启动一个并发进程worker)
celery -A celery_web.celery_ worker --pool solo --loglevel=info (pool solo是指只启动一个worker进程)

如果以上配置无误，可以看到每个worker机的连接信息；

五、操作方式：
1、获取demo文本,主要是为了测试使用，读取本地的文本文件，会生成提交页面
http://you_domain/toIndex

2、提交识别信息(form/post) 具体可以查看第一步的页面格式
form/areatext name="car_txt" 识别form对像的名称是"car_txt"
submit的地址： http://you_domain/car-info-ner
如果成功会返回json信息，其中含有task_id项内容；

3、获取结果，根据task_id的标识获取状态和结果(get方式)
http://you_domain/get_task_result/<task_id>


