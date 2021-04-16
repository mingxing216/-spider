# -*- coding:utf-8 -*-
from Utils.timers import Timer


class String_Compare_Test:
    def __init__(self, text):
        self.text = text

    def compare(self, text):
        return self.text != text

if __name__ == "__main__":
    timer = Timer()
    text = ""
    with open("test_data.html") as file_obj:
        text = file_obj.read()
    text2 = text + "111"

    compare = String_Compare_Test(text=text)
    timer.start()
    ret = None
    for i in range(1,1000000):
        ret = compare.compare(text)
    print("Use time {}".format(timer.use_time()))

