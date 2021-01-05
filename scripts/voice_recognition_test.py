#!/usr/bin/python
# -*- coding: utf8 -*-#

import threading
import rospy
import signal
import os
import traceback
import sys
import tty
import termios
import time

from std_msgs.msg import String
from stt_service.srv import start_stt, start_sttRequest, start_sttResponse
from stt_service.srv import stop_stt, stop_sttRequest, stop_sttResponse
from sentence_recognition.srv import SentenceRecognition, SentenceRecognitionRequest, SentenceRecognitionResponse


class VoiceRecognitionTest:
    node_name = "voice_recognition_test"
    service_stt_start = "/stt_node/service/start_stt"
    service_stt_stop = "/stt_node/service/start_stt"
    service_sentence_recognition = "/sentence_recognition/service/request"

    def __init__(self):
        rospy.init_node(VoiceRecognitionTest.node_name)
        self.isRunKeyboardHooking = False
        self.isSttOn = False
        
        self.__stt_service_start = rospy.wait_for_service(VoiceRecognitionTest.service_stt_start)
        self.__stt_service_start = rospy.ServiceProxy(VoiceRecognitionTest.service_stt_start, start_stt)

        self.__stt_service_stop = rospy.wait_for_service(VoiceRecognitionTest.service_stt_stop)
        self.__stt_service_stop = rospy.ServiceProxy(VoiceRecognitionTest.service_stt_stop, stop_stt)

        self.__sentence_recognition_service = rospy.wait_for_service(VoiceRecognitionTest.service_sentence_recognition)
        self.__sentence_recognition_service = rospy.ServiceProxy(VoiceRecognitionTest.service_sentence_recognition, SentenceRecognition)


    def run(self):
        self.isRunKeyboardHooking = True

        # sub scribe 2 topics
        rospy.loginfo("subscribe ros topic : /stt_node/topic/doing_sentence")
        rospy.Subscriber(
                "/stt_node/topic/doing_sentence", 
                String, self.sttOngoingTopicPrint)
        
        rospy.loginfo("subscribe ros topic : /stt_node/topic/sentence")
        rospy.Subscriber(
                "/stt_node/topic/sentence", 
                String, self.sttResTopicHandle)

        try:
            while self.isRunKeyboardHooking:
                k = self.getkey()
                if k == 'esc':
                    self.isRunKeyboardHooking = False
                else:
                    if(self.isSttOn!=True):
                        print("keyboard input : ", k)
                        rospy.loginfo("==========listening start==========")
                        self.isSttOn = True
                        request = start_sttRequest()
                        self.__stt_service_start.call(request)
                    else:
                        print("stt is on process...")

        except (KeyboardInterrupt, SystemExit):
            os.system('stty sane')
            print('stop keyboard hooking')

    def sttOngoingTopicPrint(self, data):
        # print topic /stt_node/topic/doing_sentence
        rospy.loginfo("stt ongoing : " + data.data)
        
    
    def sttResTopicHandle(self, data):
        # print topic /stt_node/topic/sentence
        rospy.loginfo("--------listening stop--------")
        rospy.loginfo("stt res : " + data.data)
        self.isSttOn = False

        # set time
        start_pt = time.time()
        rospy.loginfo("start time : " + str(start_pt))

        # service call /sentence_recognition/service/request
        sen_recog_request = SentenceRecognitionRequest()
        sen_recog_request.sentence = data.data #요청 문장
        sen_recog_request.request_type = ""
        sen_recog_request.language_code = "KOR" # lang_code
        sen_recog_response = self.__sentence_recognition_service(sen_recog_request)
        end_pt = time.time()

        # print result of sentence_recognition
        rospy.loginfo("######################################")
        rospy.loginfo("## time spend : " + str(end_pt-start_pt))
        rospy.loginfo("######################################")
        rospy.loginfo("##\n")
        rospy.loginfo("## error_code : "+ self.getSenRecoErrorCodeDef(sen_recog_response.error_code))
        rospy.loginfo("## fulfillment_text : "+ sen_recog_response.fulfillment_text)
        rospy.loginfo("## intent : "+ sen_recog_response.intent)
        rospy.loginfo("## engine : "+ sen_recog_response.engine)
        rospy.loginfo("## entities : "+ str(sen_recog_response.entities))
        rospy.loginfo("## json_data : "+ sen_recog_response.json_data)
        
    def getSenRecoErrorCodeDef(self, num):
        result = ""
        if num == 0:
            result = "SUCCESS"
        elif num == 1:
            result = "FAIL"
        elif num == 2:
            result = "LIMIT_RETRY"
        elif num == 3:
            result = "TIMEOUT"
        return result
    
    def getkey(self):
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        try:
            while self.isRunKeyboardHooking:
                b = os.read(sys.stdin.fileno(), 3).decode()
                if len(b) == 3:
                    k = ord(b[2])
                else:
                    k = ord(b)
                key_mapping = {
                    127: 'backspace',
                    10: 'return',
                    32: 'space',
                    9: 'tab',
                    27: 'esc',
                    65: 'up',
                    66: 'down',
                    67: 'right',
                    68: 'left'
                }
                return key_mapping.get(k, chr(k))
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    @staticmethod
    def signal_handler(sig, frame):
        self.isRunKeyboardHooking = False
        del sig, frame
        rospy.loginfo("Ctrl + C interrupt")
        rospy.signal_shutdown("Ctrl + C interrupt")


if __name__ == '__main__':
    try:
        node = VoiceRecognitionTest()
        signal.signal(signal.SIGINT, node.signal_handler)
        node.run()
    except Exception as err:
        rospy.logwarn("## VoiceRecognitionTest: node run Exception: \n%s", str(err))
        print("Exception : %s" % str(err))
        traceback.print_exc(file=sys.stdout)
    finally:
        rospy.loginfo("## VoiceRecognitionTest: program shutdown")
