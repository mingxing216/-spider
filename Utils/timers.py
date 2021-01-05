# -*- coding:utf-8 -*-
import random
import time


class Timer(object):
    def __init__(self):
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def use_time(self):
        end_time = time.time()
        return '%.3f' % (end_time - self.start_time)


class FixedTimer(object):
    def __init__(self, min_seconds=5, max_seconds=10, fixed_time=10):
        self.min_seconds = min_seconds
        self.max_seconds = max_seconds
        self.fixed_time = fixed_time
        self.start_time = time.time()
        self.wait_time = random.uniform(self.min_seconds, self.max_seconds)

    def start(self, reset_random=True):
        self.start_time = time.time()
        if reset_random:
            self.wait_time = random.uniform(self.min_seconds, self.max_seconds)

    def wait(self):
        end_time = time.time()
        seconds = self.wait_time - (end_time - self.start_time)
        if seconds > 0:
            time.sleep(seconds)
        return '%.3f' % seconds


class AccumlateTimer(object):
    def __init__(self):
        self.total_time = 0
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.total_time += time.time() - self.start_time
        return '%.3f' % self.total_time


if __name__ == '__main__':
    timer = Timer()
    fixed_timer = FixedTimer(4, 10)
    total_timer = AccumlateTimer()

    timer.start()
    fixed_timer.start()
    print(fixed_timer.wait_time)
    total_timer.start()
    time.sleep(3)
    total_timer.stop()
    print("fixedTimer: {}".format(fixed_timer.wait()))
    print("timer: {}".format(timer.use_time()))
    total_timer.start()
    time.sleep(1)
    print(total_timer.stop())
    print('TotalTimer: {}'.format(total_timer.total_time))
    print("timer:{}".format(timer.use_time()))
