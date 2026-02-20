#导入模块
import argparse,os,json,shutil,tempfile,subprocess,re
import requests as req
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from time import sleep
'''
s时长stat-item duration
s名称title-txt
简介desc-info-text
'''
#单下载函数
def lot(url,bvid,p,modes,save):
    global head
    qual={112: '高清 1080P+', 80: '高清 1080P', 64: '高清 720P', 32: '清晰 480P', 16: '流畅 360P'}
    head=head.copy()
    head['referer']=f"https://www.bilibili.com/video/{bvid}/?{p}"
    gets=BeautifulSoup(req.get(url,headers=head).content,'html.parser')
    #api
    resp = req.get('https://api.bilibili.com/x/player/pagelist',params={'bvid': bvid},headers=head)
    resp.raise_for_status()
    data = resp.json()
    if data['code'] != 0:
        raise Exception(f"API 返回错误: {data['message']}")
    pages=data['data']
    if p > len(pages):
        print(f"错误：分 P 索引 {p} 超出范围（共 {len(pages)} P），跳过")
        return
    page=pages[p-1]
    title = page.get('part', '').strip()
    print(f'标题:\033[36;5m{title}\033[0m')
    #print(f"bvid:{bvid}")
    #print(f"cid:{page['cid']}")
    title=clean(title)
    params = {
        'bvid': bvid,
        'cid': page['cid'],
        'qn': 80,
        'fnval': 4048,      # DASH 格式
        'fourk': 1,
        'try_look': 1,      # 关键参数：模拟试看，可能提升画质
    }
    resp = req.get('https://api.bilibili.com/x/player/playurl', params=params, headers=head)
    resp.raise_for_status()
    data = resp.json()
    if data['code'] != 0:
        raise Exception(f"播放 API 返回错误: {data['message']}")
    dash = data['data']['dash']
    vl = dash['video'][0]
    al = dash['audio'][0]
    print('视频质量id:{0}  ({1})'.format(vl['id'],qual[vl['id']]))
    print(f"音频质量id:{al['id']}")
    print(f"分辨率: {vl.get('width', '?')}*{vl.get('height', '?')}px")
    print(f"时长:{data['data']['timelength']} ms")
    vu=vl['baseUrl']
    au=al['baseUrl']
    if modes[0] or modes[2]:
        print('\033[33;5m等待音频\033[0m',end='\r')
        ac=req.get(au,headers=head, stream=True, timeout=30).content
        print(f'音频大小:{len(ac)} B')#size
        if modes[2]:
            with open(f'{save+'/'+title}.mp3','wb') as af:
                af.write(ac)
            af.close()
            print(f"保存为\033[32m{title}.mp3\033[0m")
    if modes[0] or modes[1]:
        print('\033[33;5m等待视频\033[0m',end='\r')
        vc=req.get(vu,headers=head, stream=True, timeout=30).content
        print(f'视频大小:{len(vc)} B')#size
        if modes[1]:
            with open(f'{Path(save)/title}.{"m4v"if modes[0] else "mp4"}','wb') as vf:
                vf.write(vc)
            vf.close()
            print(f'保存为\033[32m{title}.{"m4v"if modes[0] else "mp4"}\033[0m')
    if modes[0]:
        print('\033[33;5m等待合成\033[0m',end='\r')
        with tempfile.NamedTemporaryFile(suffix='.m4s', delete=False) as at:
            at.write(ac)
            atp=at.name
        with tempfile.NamedTemporaryFile(suffix='.m4s', delete=False) as vt:
            vt.write(vc)
            vtp=vt.name
        cmd = [
                Path(home)/'ffmpeg',
                '-i', vtp,
                '-i', atp,
                '-c', 'copy',
                '-y',
                f"{save+'/'+title}.mp4"
            ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        os.unlink(vtp)
        os.unlink(atp)
        print(f"合成完成\n保存为\033[32m{title}.mp4\033[0m")
#多下载函数
def ton(url,bvid,p,modes,save):
    global head
    head=head.copy()
    head['referer']=f"https://www.bilibili.com/video/{bvid}/"
    gets=BeautifulSoup(req.get(url,headers=head).content,'html.parser')
    if gets.find('div',class_='pod-item video-pod__item simple')or gets.find('div',class_='simple-base-item video-pod__item active normal'):
        os.chdir(save)
        hide=gets.find('div',class_='simple-base-item video-pod__item normal')
        ftitle= clean(gets.find('h1',class_='video-title special-text-indent').text if hide else gets.find('a', {
                        'target': '_blank',
                        'class': ['title', 'jumpable']}))
        if ftitle not in os.listdir():
            os.mkdir(ftitle)
            os.chdir(ftitle)
            if hide:
                lib=gets.find_all('div',class_='simple-base-item video-pod__item normal')
                for num,i in enumerate(lib):
                    num+=1
                    print(f'[{num}/{len(lib)}]',end='')
                    try:
                        lot(f"https://www.bilibili.com/video/{i.get('data-key')}/?p={1}",
                    i.get('data-key'),1,modes,'.')
                    except Exception:
                        print('\033[31m出错!!  跳过此项\033[0m')
            else:
                lib=gets.find_all('div',class_='pod-item video-pod__item simple')
                for num,i in enumerate(lib):
                    num+=1
                    print(f'[{num}/{len(lib)}]',end='')
                    try:
                        lot(f"https://www.bilibili.com/video/{i.get('data-key')}/?p={1}",
                    i.get('data-key'),1,modes,'.')
                    except Exception:
                        print('\033[31m出错!!  跳过此项\033[0m')
        else:
            print('此项目已经完成 或 此文件夹已经存在!')
    else:
        print('无合集列表  自动转为单下载模式')
        lot(url,bvid,p,modes,save)
#投稿下载收藏夹下载函数
def uid(url,uid,modes,save):
    global head
    head=head.copy()
    head['referer'] = f"https://space.bilibili.com/list/{uid}/"
    url0 = "https://api.bilibili.com/x/space/arc/search"
    params = {
                    "mid": uid,        # 注意参数名是 mid
                    "pn": None,
                    "ps": 20,           # 每页最多 50，30 比较稳妥
                    "order": "pubdate"  # 按发布时间排序
                }
    os.chdir(save)
    ftitle="HL_"+str(uid)
    if ftitle not in os.listdir():
        os.mkdir(ftitle)
        os.chdir(ftitle)
        print(f'创建文件夹{ftitle}')
        page=1
        count=0
        got=0
        bvlib=[]
        can=True
        print('获取bv信息')
        while can:
            # 根据类型选择 API 和参数
            params['pn']=page
            resp = req.get(url0, headers=head, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data['code'] == 0:
                # 解析视频列表
                medias = data['data']['list']['vlist']
                if medias:
                    pagedata = data['data']['page']
                    count=pagedata['count']
                    bvlib.extend(medias)
                    # 判断是否还有下一页（根据总数和当前页数）
                    if pagedata['pn']*pagedata['ps'] >= count:
                        can=False
                    else:
                        page += 1
            elif data['code'] == -799:
                print(data['message'],end='\r')
                if len(bvlib)!=0:
                    for num,i in enumerate(bvlib):
                        print(f'[{num+1}/{len(bvlib)}|{num+1+got}/{count}]',end='')
                        print(i['bvid'])
                        try:
                            lot(f"https://www.bilibili.com/video/{i['bvid']}/?p={1}",
                                i['bvid'],1,modes,'.')
                        except Exception:
                            print('\033[31m出错!!  跳过此项\033[0m')
                    bvlib=[]
                    got+=20
            else:#!=0
                print(f"API错误: {data['message']}")
        if len(bvlib)!=0:
                    for num,i in enumerate(bvlib):
                        print(f'[{num+1}/{len(bvlib)}|{num+1+got}/{count}]',end='')
                        print(i['bvid'])
                        try:
                            lot(f"https://www.bilibili.com/video/{i['bvid']}/?p={1}",
                                i['bvid'],1,modes,'.')
                        except Exception:
                            print('\033[31m出错!!  跳过此项\033[0m')
                    bvlib=[]
                    got+=20
        print(f"加载完成({pagedata['pn']}*20),共{count}项")
    else:
                print('此项目已经完成 或 此文件夹已经存在!')
def mlid(url,mlid,modes,save):
    global head
    head=head.copy()
    head['referer'] = f"https://www.bilibili.com/list/{mlid}"
    url0 = "https://api.bilibili.com/x/v3/fav/resource/list"
    params = {
                    "media_id": mlid[2:],    # 收藏夹 ID
                    "pn": None,
                    "ps": 20,            # 收藏夹每页最多 20
                    "platform": "web"
                }
    os.chdir(save)
    ftitle="BK_"+str(mlid)[2:]
    if ftitle not in os.listdir():
        os.mkdir(ftitle)
        os.chdir(ftitle)
        print(f'创建文件夹{ftitle}')
        page=1
        count=0
        got=0
        bvlib=[]
        can=True
        print('获取bv信息')
        while can:
            # 根据类型选择 API 和参数
            params['pn']=page
            resp = req.get(url0, headers=head, params=params)
            resp.raise_for_status()
            data = resp.json()
            #print(data)
            if data['code'] == 0:
                # 解析视频列表
                medias = data['data']['medias']
                if medias:
                    count=data['data']['info']['media_count']
                    bvlib.extend(medias)
                    # 判断是否还有下一页（根据总数和当前页数）
                    if  not data['data']['has_more']:
                        can=False
                    else:
                        page += 1
            elif data['code'] == -799:
                print(len(bvlib))###
                print(data['message'],end='\r')
                '''
                if len(bvlib)==0:
                    print('等待0s')
                    sleep(0)
                '''
                if len(bvlib)!=0:
                    print(bvlib)
                    for num,i in enumerate(bvlib):
                        print(f'[{num+1}/{len(bvlib)}|{num+1+got}/{count}]',end='')
                        print(i['bvid'])
                        try:
                            lot(f"https://www.bilibili.com/video/{i['bvid']}/?p={1}",
                                i['bvid'],1,modes,'.')
                        except Exception:
                            print('\033[31m出错!!  跳过此项\033[0m')
                    bvlib=[]
                    got+=20
            else:#!=0
                print(f"API错误: {data['message']}")
            page+=1
        print(len(bvlib),'end')####
        if len(bvlib)!=0:
                    for num,i in enumerate(bvlib):
                        print(f'[{num+1}/{len(bvlib)}|{num+1+got}/{count}]',end='')
                        print(i['bvid'])
                        try:
                            lot(f"https://www.bilibili.com/video/{i['bvid']}/?p={1}",
                                i['bvid'],1,modes,'.')
                        except Exception:
                            print('\033[31m出错!!  跳过此项\033[0m')
                    bvlib=[]
                    got+=20
        print(f"加载完成({page}*20),共{count}项")
    else:
                print('此项目已经完成 或 此文件夹已经存在!')

#其他函数
def catch(text):
    #uid
    catch=re.search(r'/\d+', text)
    if catch:
        return 'uid',f"https://www.bilibili.com/list/{catch.group()[1:]}/",catch.group(),1
    #mlid
    catch=re.search(r'ml\d+', text)
    if catch:
        return 'mlid',f"https://www.bilibili.com/list/{catch.group()}",catch.group(),1
    #bvid&url
    catch=re.search(r'BV[a-zA-Z0-9]{10}', text)
    if catch:
        #p
        parsed = urlparse(text)
        query = parse_qs(parsed.query)
        p = int(query.get('p', [1])[0])
        return 'bvid',f"https://www.bilibili.com/video/{catch.group()}/?p={p}",catch.group(),p
def bv(text):
    """从文本中提取 BV 号（10位字母数字组合）"""
    match = re.search(r'BV[a-zA-Z0-9]{10}', text)
    return match.group() if match else None

def clean(s):
    """过滤文件名中的非法字符（Windows）"""
    return "".join(c for c in s if c not in r'\/:*?"<>|').strip()

#主下载函数
def main():
    global ffmpeg_path
    parser = argparse.ArgumentParser(description="BiliBili视频爬取工具(慎用)")
    #定义参数
    #目标参数
    parser.add_argument('target',help='目标BvID/Url/Uid(set)/Mlid(set)(请加引号)')
    #质量参数
    #parser.add_argument('-v','--videoQ',help='视频画质索引  (由高到低,默认为0)',type=int,default=0)
    #parser.add_argument('-a','--audioQ',help='音频音质索引  (由高到低,默认为0)',type=int,default=0)
    #选项参数
    parser.add_argument('-V','--videoFile',action='store_true',help='保存视频文件(纯画面)')
    parser.add_argument('-A','--audioFile',action='store_true',help='保存音频文件(纯声音)')
    parser.add_argument('-M','--mixFile',action='store_true',help='保存视频文件(合成)')
    #选项2
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument('-o','--one',action='store_true',help='下载单个')
    group2.add_argument('-s','--set',action='store_true',help='下载合集')
    #保存路径
    parser.add_argument('-f','--file',help='保存路径  (加引号 , 默认为上级路径)',default='..')
    #处理参数
    args=parser.parse_args()
    cought = catch(args.target)
    modes=[args.mixFile,args.videoFile,args.audioFile]
    match cought[0]:
        case 'uid':
            uid(cought[1],cought[2][1:],modes,args.file)
        case 'mlid':
            mlid(cought[1],cought[2],modes,args.file)
        case 'bvid': 
            if args.one:
                lot(cought[1],cought[2],cought[3],
                modes,args.file)
            else:
                ton(cought[1],cought[2],cought[3],
                modes,args.file)
        case _:
            print(f'无效输入:>{args.target}')
    print('下载结束')
#主逻辑
if __name__=="__main__":
    #常量定义(请求头等等)
    head = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
        "Origin": "https://www.bilibili.com",
        "Accept": "*/*",
        "Accept-Encoding": "identity",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }
    home=os.getcwd()
    if 'ffmpeg.exe' in os.listdir():
        main()
    else:
        print('请将ffmpeg.exe移动至此目录下')
