from paddleocr import PaddleOCR
from math import log, sqrt
from fuzzywuzzy import process
from prettytable import PrettyTable
import statistics
import os
import re


def rt_calc(acc, lv):
    rt = 0
    if acc > 0 and acc < 70:
        rt = sqrt(acc / 70) * 0.5 * lv
    elif acc >= 70 and acc < 97:
        rt = (0.7 - 0.2 * log((100 - acc) / 3, 10)) * lv
    elif acc >= 97 and acc < 99.7:
        rt = (0.7 - 0.16 * log((100 - acc) / 3, 10)) * lv
    elif acc >= 99.7 and acc < 99.97:
        rt = (0.78 - 0.08 * log((100 - acc) / 3, 10)) * lv
    elif acc >= 99.97 and acc <= 100:
        rt = (2 * acc - 199) * lv
    else:
        rt = -1
    return rt


ocr_ch_en = PaddleOCR(use_angle_cls=True, use_gpu=False)
ocr_jp = PaddleOCR(use_angle_cls=True, use_gpu=False, lang='japan')
song_name_list = dict()
all_players = dict() #{id:[song_name, acc, rt] * charts_num}
teams = list()
failed_img = list()
single_avg_rt = dict()
team_avg_rt = dict()

charts_num = int(input('请输入谱面数量及名称、定数:'))

for i in range(charts_num):
    n = input()
    l = float(input())
    song_name_list[n] = l
    
print(song_name_list)
    
teams_num = int(input('请输入队伍总数:'))

for j in range(teams_num):
    teams.append([])
    while True:
        a = input()
        if a == '':
            break
        else:
            teams[j].append(a)
            all_players[a] = dict()
            for k in song_name_list.keys():
                all_players[a][k] = list()

print(teams)
print(all_players)

img_list = list()


for i in os.listdir():
    if '.jpg' in i or '.png' in i:
       img_list.append(i)


for i in img_list:
    err = False
    result = ocr_ch_en.ocr(i, cls=True)
    song_name = ''
    player_id = ''
    acc = float(0)
    for line in result:
        text = line[1][0]
        #print(text)
        a = process.extractOne(text, song_name_list.keys())
        b = process.extractOne(text, all_players.keys())
        if a[1] >= 85:
            song_name = a[0]
        if b[1] >= 80 and len(b[0]) == len(text):
            print(text)
            print(b)
            player_id = b[0]
        if '%' in text:
            res = re.search('\\d\\d\\.\\d\\d', text)
            try:
                acc = float(text[res.span()[0]:res.span()[1]])
            except:
                print(res)
    if player_id == '' or acc == 0.0:
        print('处理图片\'' + i + '\'时出现问题(曲名/玩家名/acc未识别)，请重新人工检查')
        failed_img.append(i)
        print(song_name)
        print(player_id)
        print(acc)
        err = True
    elif song_name == '':
        result = ocr_jp.ocr(i, cls=True)
        for line in result:
            if line[1][0] in song_name_list:
                song_name = line[1][0]
        if song_name == '':
            print('处理图片\'' + i + '\'时出现问题(曲名/玩家名/acc未识别)，请重新人工检查')
            failed_img.append(i)
            err = True
    if err == False:
        rt = rt_calc(acc, song_name_list[song_name])
        if rt == -1:
            print('处理图片\'' + i + '\'时出现问题(acc异常)，请重新人工检查')
            failed_img.append(i)
            print(acc)
        else:
            print(player_id + ' ' + song_name)
            print(i)
            if all_players[player_id][song_name] == []:
                all_players[player_id][song_name] = [acc, rt]
            
print(failed_img)
print(all_players)
table = PrettyTable(['Team','ID'] + list(song_name_list.keys()))
for i in all_players:
    t = 0
    tp_list = ['无数据'] * charts_num
    rt_list = ['无数据'] * charts_num
    for j in range(len(teams)):
        if i in teams[j]:
            t = j + 1
    for k in all_players[i]:
        #print(tp_list, rt_list)
        #print(list(song_name_list.keys()).index(k))
        try:
            tp_list[list(song_name_list.keys()).index(k)] = str(all_players[i][k][0]) + '% '
            rt_list[list(song_name_list.keys()).index(k)] = str(round(all_players[i][k][1], 3))
        except IndexError:
            tp = float(input('请输入' + i + '的 \'' + k + '\'tp(-1即代表未参赛)'))
            if tp != -1:
                r = rt_calc(tp, song_name_list[k])
                tp_list[list(song_name_list.keys()).index(k)] = str(tp) + '% '
                rt_list[list(song_name_list.keys()).index(k)] = str(round(r, 3))
            else:
                tp_list[list(song_name_list.keys()).index(k)] = '未参赛'
                rt_list[list(song_name_list.keys()).index(k)] = ''
    if '未参赛' not in tp_list:
        single_avg_rt[i] = statistics.mean(list(map(float, rt_list)))
    else:
        single_avg_rt[i] = -1
    table.add_row([str(t), i] + [m + n for m, n in zip(tp_list, rt_list)])
print(single_avg_rt)
for i in teams:
    tmp = list()
    for j in i:
        if single_avg_rt[j] != -1:
            tmp.append(single_avg_rt[j])
    print(tmp)
    team_avg_rt[teams.index(i)] = statistics.mean(tmp)
single_avg_rt= sorted(single_avg_rt.items(), key=lambda d:d[1], reverse = True)
team_avg_rt= sorted(team_avg_rt.items(), key=lambda d:d[1], reverse = True)
print('-------------------------------最终结果-------------------------------')
print(table)
print('\n个人排名(id, 平均rt):')
for i in range(len(single_avg_rt)):
    print(str(i + 1) + '. ' + str(single_avg_rt[i]))
print('\n小组排名(小组序号, 平均rt):')
for i in range(len(team_avg_rt)):
    print(str(i + 1) + '. ' + str(team_avg_rt[i]))
