#-*-coding:utf-8-*-

# import difflib
# # import jieba
# import Levenshtein
#
# str1 = "Materials Science & Engineering C"
# str2 = "Materials Science and Engineering: C"
#
# str1 = "Tongdao Wang"
# str2 = "Wang, Tongdao"
#
# # 1. difflib
# seq = difflib.SequenceMatcher(None, str1, str2)
# ratio = seq.ratio()
# print('difflib similarity1: ', ratio)
#
# # difflib 去掉列表中不需要比较的字符
# seq = difflib.SequenceMatcher(lambda x: x in ' 我的雪', str1, str2)
# ratio = seq.ratio()
# print('difflib similarity2: ', ratio)
#
# # 2. hamming距离，str1和str2长度必须一致，描述两个等长字串之间对应位置上不同字符的个数
# # sim = Levenshtein.hamming(str1, str2)
# # print 'hamming similarity: ', sim
#
# # 3. 编辑距离，描述由一个字串转化成另一个字串最少的操作次数，在其中的操作包括 插入、删除、替换
# sim = Levenshtein.distance(str1, str2)
# print('Levenshtein similarity: ', sim)
#
# # 4.计算莱文斯坦比
# sim = Levenshtein.ratio(str1, str2)
# print('Levenshtein.ratio similarity: ', sim)
#
# # 5.计算jaro距离
# sim = Levenshtein.jaro(str1, str2)
# print('Levenshtein.jaro similarity: ', sim)
#
# # 6. Jaro–Winkler距离
# sim = Levenshtein.jaro_winkler(str1, str2)
# print('Levenshtein.jaro_winkler similarity: ', sim)



import langid                             #引入langid模块
import time

s1 = '你好 hello world'
s2 = 'hello'
s3 = 'Flüssigkeiten zum Nassbehandeln von Wäschestücken werden vielfach mit Dampf aufgeheizt. Dazu wird der Dampf mit hoher Geschwindigkeit durch eine Düse (30) der aufzuheizenden Flüssigkeit direkt zugeführt. Aufgrund der hohen Geschwindigkeit, mit der der Dampf in die aufgeheizte Flüssigkeit einströmt, entstehen starke Geräusche sowie Schwingungen und Vibrationen. Um mindestens die Geräusche zu reduzieren, ist es bereits bekannt, zusätzlich Druckluft zuzuführen. Das verschlechtert den Wärmeübergang. Die Erfindung sieht es vor, in die Düse (30) eine kleine Menge der aufzuheizenden Flüssigkeit einzusaugen und dadurch in der Düse (30) ein Kondensat-Dampfgemisch zu bilden. Alternativ oder zusätzlich kann hinter der Düse (30) ein Strömungsteiler vorgesehen sein, der die Strömungsgeschwindigkeit des Dampfs bzw. Dampf-Kondensatgemisches erhöht. Hierdurch und/oder durch die Bildung eines Dampf-Kondensatgemisches in der Düse (30) werden die Geräuschentwicklung beim Einleiten des Dampfs in die aufzuheizende Flüssigkeit sowie Schwingungen und Vibrationen ohne die Zufuhr von Druckluft verringert'

m = langid.classify(s3)
start_time = time.time()
print(start_time)
i = langid.classify(s1)
j = langid.classify(s2)

print(i[0])

end_time = time.time()
print(end_time)

print('======Time consuming is %.2fs======' %(end_time - start_time))