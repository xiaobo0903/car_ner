#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
该程序是为了进行姓氏、金额、和电话号码的提取的工作，因为这些内容的提取会比较固化；
'''
import re
import os
import sys
import terminal_predict2 as tfner
#百家姓
nor_name = [
    "王","李","张","刘","陈","杨","赵","黄","周","吴","徐","孙","胡","朱","高","林","何","郭","马","罗","梁","宋","郑","谢","韩","唐","冯","于","董","萧","程","曹","袁","邓",
    "许","傅","沈","曾","彭","吕","苏","卢","蒋","蔡","贾","丁","魏","薛","叶","阎","余","潘","杜","戴","夏","钟","汪","田","任","姜","范","方","石","姚","谭","廖","邹","熊",
    "金","陆","郝","孔","白","崔","康","毛","邱","秦","江","史","顾","侯","邵","孟","龙","万","段","雷","钱","汤","尹","黎","易","常","武","乔","贺","赖","龚","文","庞","樊",
    "兰","殷","施","陶","洪","翟","安","颜","倪","严","牛","温","芦","季","俞","章","鲁","葛","伍","韦","申","尤","毕","聂","丛","焦","向","柳","邢","路","岳","齐","沿","梅",
    "莫","庄","辛","管","祝","左","涂","谷","祁","时","舒","耿","牟","卜","肖","詹","关","苗","凌","费","纪","靳","盛","童","欧","甄","项","曲","成","游","阳","裴","席","卫",
    "查","屈","鲍","位","覃","霍","翁","隋","植","甘","景","薄","单","包","司","柏","宁","柯","阮","桂","闵","解","强","柴","华","车","冉","房","边","净","阴","闫","佘","练",
    "骆","付","代","麦","容","悲","初","瞿","褚","班","全","名","井","米","谈","宫","虞","奚","佟","符","蒲","穆","漆","卞","东","储","党","从","艾","苻","厉","岑","燕","吉",
    "冷","仇","伊","首","郁","娄","楚","邝","历","狄","简","胥","连","帅","封","危","支","原","滕","苑","信","索","栗","官","沙","池","藏","师","国","巩","刁","茅","杭","巫",
    "居","窦","皮","戈","麻","饶","习","巴","旷","宗","荆","荣","孝","蔺","廉","员","西","寇","刃","见","底","区","郦","卓","琚","续","朴","蒙","敖","花","应","喻","冀","尚",
    "顿","菅","嵇","雒","弓","忻","权","谌","卿","扈","海","冼","伦","鹿","宿","山","桑","裘","达","么","智","郎","农","戚","屠","尉","蓝","招","攀","栾","荚","税","勾","由","福"
]

MAXNUM = 180

#些类是为了解决汽车类的标注内容而设定的，通过正则的方式提取姓氏、金额、电话等内容;
class ex_car_info:
    # nkey = {}
    # rkey = {}

    #提取姓氏
    def ex_person(self, str):

        nkey = {}
        pattern = re.compile("([\u4e00-\u9fa5]{0,1})(女士|先生)")  #    
        m = pattern.findall(str)
        stmp = ''
        for rs in m:
            if rs[0] in nor_name:      #为了去掉一些不合规的姓氏
                stmp = rs[0]
            stmp = stmp + rs[1]
            nkey[stmp] = "name"
            break   
        return nkey

    #提取32万、43万以及多少期贷款这种格式的数据
    def ex_price1(self, str):

        nkey = {}
        pattern = re.compile("\\d{2,3}[万|期]")  # 
        m = pattern.findall(str)

        for rs in m:
            nkey[rs] = "price"
        return nkey

    #提取10,234这种格式的数据
    def ex_price2(self, str):

        nkey = {}
        pattern = re.compile("\\d{2,4},\\d{3}")  # 
        m = pattern.findall(str)
        for rs in m:
            nkey[rs] = "price"
        return nkey

    # #提取三十多万、五十多万等格式的金额
    def ex_price3(self, str):

        nkey = {}
        pattern = re.compile("\\d{1,2}多万")   # 
        m = pattern.findall(str)
        for rs in m:
            nkey[rs] = "price"
        return nkey

    #提取手机号码,11位数字，为从1打头
    def ex_mobile(self, str):

        nkey = {}
        pattern = re.compile("1[34578]\\d{7,10}")  # 
        m = pattern.findall(str)
        for rs in m:
            nkey[rs] = "phone"
        return nkey

    #提取400或者800号码，这类号码是营销电话，不需提取，只需要消除掉即可，需要在提取金额前替换掉
    def ex_48phone(self, str):

        nkey = {}
        pattern = re.compile("[4|8]00\\d{5,7}")  # 
        m = pattern.findall(str)
        for rs in m:
            nkey[rs] = "phone"
        return nkey

    #该部分对于输入的文本内容进行分析和处理，调用各种处理内容后，返回相应的处理结果
    def ex_inStr(self, str):
        #把输入的str内容处理掉回车和换行等
        nstr = re.sub("\[.*?\]", "", str) #去掉文本中的时间戳信息[11:22:22]
        nstr = nstr.replace(" ", "")      #去掉文本中的空格，下面通过空格来替换回车和换行符;
        nstr = nstr.replace("\r"," ").replace("\n", " ").replace("  ", " ")
        nkey1 = self.ex_person(nstr)
        nkey2 = self.ex_48phone(nstr)
        nkey3 = self.ex_mobile(nstr)
        nkey4 = self.ex_price1(nstr)
        nkey5 = self.ex_price2(nstr)
        nkey6 = self.ex_price3(nstr)                
        # self.ex_price3(str)
        #把nkey中提取的信息整理成按name,phone,price格式的内容;

        nkey = {**nkey1, **nkey2, **nkey3, **nkey4, **nkey5, **nkey6 }
        rkey = self.ch_ex_dirt(nkey)
        print(rkey)
        slist = self.ex_Str_List(nstr)        
        return(rkey, slist)   #返回两个内容：rkey是识别出的姓名、电话和金额等内容；slist是为了NER识别时进行的字符串的切割内容；

    #因为NER只能够处理200个字符以内的数据，所以需要把字符串切割成200字符以内的数据列表
    def ex_Str_List(self, str):
        strList = []
        astr = str.split(" ")
        tstr = ""
        for item in astr:
            if len(item) < 3:
                continue
            tstr = tstr + "," + item
            if len(tstr) >MAXNUM:        #如果字符串长度大于180个时进行截取；
                strList.append(tstr)
                tstr = ""
        print(len(strList))
        return(strList)

    def ch_ex_dirt(self, nkey):

        rkey = {}
        for key, value in nkey.items():
            v = rkey.get(value, "")
            if v == "":
                rkey[value] = key
            else:
                rkey[value] = v+"|"+key
        return rkey

    #获取汽车信息的实体内容，返回的是json串
    def get_Car_Ner_Result(self, car_txt):
        nkey, slist = self.ex_inStr(car_txt)
        jvec = []
        jmod = []
        jfoc = []
        #tfner只能够处理200个字符串以内的数据，所以需要把文本切割成多个分片进行处理；
        for item in slist:
            avec, amod, afoc = tfner.predict(item)
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
        nkey["matedate"] = matedata
        print(nkey)
        return nkey

    def ex_file(self, filename):

        infile = filename
        try:
            inf = open(infile,'r')
        except:
            print('文件打开错误')
            exit(2)

        fstr = ""
        lines =  inf.readlines() #依次读取每行
        for line in lines: #依次读取每行
            self.ex_person(line)
            self.ex_48phone(line)
            self.ex_mobile(line)
            self.ex_price1(line)
            self.ex_price2(line)
            self.ex_price3(line)

if __name__ == "__main__":
    ex = ex_car_info()
    ex.strip_time("[12:12:11]aaaaa[22:11:22]aaaaa[33:33:33]")
