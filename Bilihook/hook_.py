#导入模块
import argparse,os,json,shutil,tempfile,subprocess,re
import requests as req
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from time import sleep,localtime,strftime
'''
s时长stat-item duration
s名称title-txt
简介desc-info-text

try:

except Exception:
    n=f'unkown_{strftime("%Y_%m_%d_%H_%M_%S",localtime())}'
'''
#单下载函数
def lot(url,modes,savefile,need,hide):
    #print('Down','必要' if need else '不必','是的' if hide else'不知道')
    global head,ffmpeg_path,home
    head=head.copy()
    head['referer']=url.split('?')[0]
    gets=BeautifulSoup(req.get(url,headers=head).content,'html.parser')
    if hide or (need and gets.find('div',class_='simple-base-item video-pod__item normal')):
        title=gets.find_all('div',
                            class_='title-txt')[int(re.search(r'p=\d?',url).group()[2:]
                                                    if re.search(r'p=\d?',url) else '1')-1].text
    else:
        title=clean(gets.find('title').text)
    print(f':>\033[5m{title}\033[0m')
    getj=json.loads(gets.find_all('script')[3].text.replace('window.__playinfo__=', ''))
    getD=getj['data']
    getq=getD['dash']
    vd=dict(zip(getD["accept_quality"],getD["accept_description"]))
    vm=getq['video'][0]
    vurl=vm['baseUrl']
    am=getq['audio'][0]
    aurl=am['baseUrl']
    print('-'*5+f"分辨率:{vm['width']}*{vm['height']}px")
    print('-'*5+f"视频质量:{vd[vm['id']]}")
    print('-'*5+f"音频质量:{am['id']}")
    print('-'*5+f"时长:{getD['timelength']} ms")
    if modes[0] or modes[2]:
        print(':>\033[33;5m等待音频......\033[0m',end='\r')
        ac=req.get(aurl,headers=head, stream=True).content
        print('-'*5+f'音频大小:{len(ac)} B')#size
        if modes[2]:
            with open(f'{savefile+'/'+title}.mp3','wb') as af:
                af.write(ac)
            af.close()
            print(f"保存到\033[36m{savefile+'/'+title}.mp3\033[0m")
    if modes[0] or modes[1]:
        print(':>\033[33;5m等待视频......\033[0m',end='\r')
        vc=req.get(vurl,headers=head, stream=True).content
        print('-'*5+f'视频大小:{len(vc)} B')#size
        if modes[1]:
            with open(f'{savefile+"/"+title}.{"m4v"if modes[2] else "mp4"}','wb') as vf:
                vf.write(vc)
            vf.close()
            print(f'保存到\033[36m{savefile+"/"+title}.{"m4v"if modes[2] else "mp4"}\033[0m')
    if modes[0]:
        print(':>\033[33;5m等待合成......\033[0m',end='\r')
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
                f"{savefile+'/'+title}.mp4"
            ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        os.unlink(vtp)
        os.unlink(atp)
        print('-'*5,f"合成完成\n保存到\033[36m{savefile+'/'+title}.mp4\033[0m")
#多下载函数
def ton(url,modes,savefile,need):
        #print('Ton','必要' if need else '不要')
    global head
    head=head.copy()
    head['referer']=url.split('?')[0]
    gets=BeautifulSoup(req.get(url,headers=head).content,'html.parser')
    if gets.find('div',class_='pod-item video-pod__item simple')or gets.find('div',class_='simple-base-item video-pod__item active normal'):
        hide=bool(gets.find('div',class_='simple-base-item video-pod__item normal'))
        filetitle= clean(gets.find('h1',class_='video-title special-text-indent').text if hide else gets.find('a', {
                        'target': '_blank',
                        'class': ['title', 'jumpable']}))
        os.chdir(savefile)
        if filetitle not in os.listdir():
            try:
                os.mkdir(filetitle)
                os.chdir(filetitle)
                print('makedir:',filetitle)
            except Exception:
                n=f'unkown_{strftime("%Y_%m_%d_%H_%M_%S",localtime())}'
                os.mkdir(n)
                os.chdir(n)
                print('makedir:',n)
            if hide:
                lib=gets.find_all('div',class_='simple-base-item video-pod__item normal')
                for num,i in enumerate(lib):
                    print(f'[{num+1}/{len(lib)}]',end='')
                    lot(f"https://www.bilibili.com/video/{url.split('/')[4]}/?p={num+1}",
                         modes,'.',False,hide)
            else:
                lib=gets.find_all('div',class_='pod-item video-pod__item simple')
                for num,i in enumerate(lib):
                    print(f'[{num+1}/{len(lib)}]',end='')
                    lot(f"https://www.bilibili.com/video/{i.get('data-key')}/",
                         modes,'.',False,hide)
        else:
            print('此项目已经完成 或 此文件夹已经存在!')
    else:
        print('无合集列表  自动转为单下载模式')
        lot(urlmodes,save,True,False)


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
    parser = argparse.ArgumentParser(description="BiliBili视频爬取工具")
    #定义参数
    #目标参数
    parser.add_argument('target',help='目标BvID/Url(请加引号)')
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
    #match = re.search(r'BV[a-zA-Z0-9]{10}', text)
    modes=[args.mixFile,args.videoFile,args.audioFile]
    #bvid=match.group() if match else None
    if args.one:
        lot(args.target,modes,args.file,True,False)
    else:
        ton(args.target,modes,args.file,True)
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
