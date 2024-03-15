"""调用bing copilot接口"""
import requests
import json
import websockets
import asyncio
import logging
import urllib
import random
import hashlib
#读取config.json文件
with open("./config.json", "r") as f:
    config = json.load(f)
def getAuth():
    target = "https://" + config['domain'] + "/turing/conversation/create?bundleVersion=1.1626.5"
    headers = {
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Cookie":config['cookie'],
    }
    try:
        #发起get请求
        response = requests.get(target, headers=headers)
        #判断请求是否成功
        if response.status_code == 200:
            #判断返回头中是否有X-Sydney-Conversationsignature
            if response.headers.get('X-Sydney-Conversationsignature'):
                #获取返回参数 此处应获取加密后的signature参数
                signature = response.headers['x-sydney-encryptedconversationsignature']
                #获取响应内容
                content = response.text
                #将响应内容转换成json格式
                content = json.loads(content)
                conversationId = content['conversationId']
                clientId = content['clientId']
                #返回dict
                return {
                    "signature": signature,
                    "conversationId": conversationId,
                    "clientId": clientId
                }
        else:
            print("请求失败")
            return None
    except Exception as e:
        print(e)
        return None



async def send_message(websocket, message):
    await websocket.send(json.dumps(message).encode() + b'\x1e')

async def bingChat(question):
    auth = getAuth()
    if auth == None:
        return "请求失败,请再试一次"
    uri = "wss://" + config['domain'] + "/sydney/ChatHub?sec_access_token="
    token = urllib.parse.quote(auth["signature"])
    uri += token
    try:
        async with websockets.connect(uri) as websocket:
            # Send initial messages
            await send_message(websocket, {"protocol":"json","version":1})
            await send_message(websocket, {"type":6})
            #生成随机数
            random_id = random.randint(1,1000000)
            #random_id md5加密
            md5 = hashlib.md5(str(random_id).encode()).hexdigest()
            # Send the data message
            data = {
                    "arguments": [{
                        "source": "cib",
                        "optionsSets": ["nlu_direct_response_filter", "deepleo", "disable_emoji_spoken_text", "responsible_ai_policy_235", "enablemm", "dv3sugg", "autosave", "iyxapbing", "iycapbing", "galileo", "saharagenconv5", "sunoupsell", "techinstgnd", "botthrottle", "dlimitationnc", "jb204cfct085", "elec2t", "elecgnd", "xapmon", "gndlogcf", "satrca", "vidtoppb"],
                        "allowedMessageTypes": ["ActionRequest", "Chat", "ConfirmationCard", "Context", "InternalSearchQuery", "InternalSearchResult", "Disengaged", "InternalLoaderMessage", "Progress", "RenderCardRequest", "RenderContentRequest", "AdsQuery", "SemanticSerp", "GenerateContentQuery", "SearchQuery", "GeneratedCode", "InternalTasksMessage"],
                        "sliceIds":[],
                        "traceId": md5,
                        "isStartOfSession": True,
                        "message": {
                            "locale": "zh-CN",
                            "market": "zh-CN",
                            "region": "SE",
                            "author": "user",
                            "inputMethod": "Keyboard",
                            "text": question,
                            "messageType": "Chat"
                        },
                        "tone": "Balanced",
                        "conversationId": auth["conversationId"],
                        "participant": {
                            "id": auth["clientId"],
                        }
                    }],
                    "invocationId": "1",
                    "target": "chat",
                    "type": 4
                }
                # Send the data message
            await send_message(websocket, data)
            #初始化回答
            answer = ""
            count = 0
            while True:
                message = await websocket.recv()
                #
                #去除message中及后面所有字符
                message = message.split('')[0]
                #将message转换成json格式
                message = json.loads(message)
                # print(message)
                #如果message中type存在
                if 'type' in message:
                    if message['type'] == 1  :
                        temp = message['arguments'][0]
                        #判断temp下是否存在messages
                        #print(temp)
                        if 'messages' in temp:
                            answer = temp['messages'][0]['text']
                    #此处有可能会提前收到type为6的消息 所以需要判断count是否大于2
                    if message['type'] == 6:
                        count += 1
                        if count >= 2:
                            #断开连接
                            await websocket.close()
                            break
                        
            return answer
    except websockets.ConnectionClosed as e:
        logging.error(f"Connection closed: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
if __name__ == "__main__":
    answer = asyncio.run(bingChat("你的问题"))
    print(answer)









        







