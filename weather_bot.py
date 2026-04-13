import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# --- 配置 ---
API_KEY = os.environ.get("QWEATHER_API_KEY")
CITY_ID = os.environ.get("CITY_ID")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# 使用标准开发域名，避免 403 域名限制
BASE_URL =  os.environ.get("BASE_URL")
print(BASE_URL)

def get_weather_data():
    """获取今日天气预报和生活指数（含空气相关建议）"""
    # 3天天气预报
    weather_url = f"{BASE_URL}/weather/3d?location={CITY_ID}&key={API_KEY}"
    # 生活指数：1-运动, 3-穿衣, 9-感冒, 10-空气污染扩散
    indices_url = f"{BASE_URL}/indices/1d?type=1,3,9,10&location={CITY_ID}&key={API_KEY}"
    print(weather_url)
    
    try:
        wea_res = requests.get(weather_url, timeout=10).json()
        ind_res = requests.get(indices_url, timeout=10).json()
        
        # 调试信息
        print(f"Weather API Code: {wea_res.get('code')}")
        print(f"Indices API Code: {ind_res.get('code')}")
        
        # 检查是否调用成功
        if wea_res.get('code') == '200' and ind_res.get('code') == '200':
            today = wea_res['daily'][0]
            indices = {item['type']: item for item in ind_res['daily']}
            
            return {
                "tempMax": int(today['tempMax']),
                "tempMin": int(today['tempMin']),
                "textDay": today['textDay'],
                "indices": indices  # 包含空气扩散、穿衣、感冒等数据
            }
        else:
            error_msg = f"API异常: 天气{wea_res.get('code')}, 指数{ind_res.get('code')}"
            print(error_msg)
            # 如果是403，通常是Key配置或域名问题
            if '403' in str(wea_res.get('code')) or '403' in str(ind_res.get('code')):
                send_email(f"🚨 警告：和风天气 API 返回 403 错误，请检查 GitHub Secrets 中的 API_KEY 是否有效。")
    except Exception as e:
        print(f"数据解析失败: {e}")
    return None

def send_email(content):
    message = MIMEText(content, 'plain', 'utf-8')
    
    # --- 修复核心：使用 formataddr 保证 RFC 兼容性 ---
    # 第一个参数是昵称（支持中文），第二个参数是完整的邮箱地址
    # 它会自动生成类似：=?utf-8?b?5aSp5rCU5Yqp5omL?= <xxx@qq.com> 的格式
    nickname = "天气助手"
    message['From'] = formataddr((Header(nickname, 'utf-8').encode(), EMAIL_SENDER))
    
    message['To'] = Header("汤同学", 'utf-8') # 或者也用 formataddr
    message['Subject'] = Header("📢 今日出行贴心提醒", 'utf-8')

    try:
        # ... 后续 SMTP 登录代码保持不变 ...
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], message.as_string())
        server.quit()
        print("邮件推送成功！")
    except Exception as e:
        print(f"邮件推送失败: {e}")

def main():
    data = get_weather_data()
    if not data:
        return

    tips = []
    
    # 1. 监测温差
    temp_diff = data['tempMax'] - data['tempMin']
    if temp_diff >= 10:
        tips.append(f"🌡️ 温差预警：今日温差达 {temp_diff}°C，早晚记得添衣。")

    # 2. 监测空气污染扩散条件 (Type 10)
    # 类别：1-优，2-良，3-中，4-较差，5-很差
    air_idx = data['indices'].get('10', {})
    if air_idx and int(air_idx.get('level', 0)) >= 3:
        tips.append(f"😷 空气提醒：今日{air_idx['name']}{air_idx['category']}。{air_idx['text']}")

    # 3. 监测感冒指数 (Type 9)
    cold_idx = data['indices'].get('9', {})
    if cold_idx and int(cold_idx.get('level', 0)) >= 3:
        tips.append(f"💊 健康预警：感冒风险{cold_idx['category']}。{cold_idx['text']}")
    
    # 4. 监测雨雪
    if "雨" in data['textDay'] or "雪" in data['textDay']:
        tips.append(f"☔ 天气提醒：今日预报有 {data['textDay']}，记得带伞。")

    # 执行发送
    if tips:
        full_content = "汤同学，你好！今日份的出行提醒：\n\n" + "\n".join(tips)
        send_email(full_content)
    else:
        # 调试用：如果没有异常也发一封信，确认脚本在跑
        # send_email("今天天气很好，空气清新，祝你心情愉快！")
        print("今日无异常指标。")

if __name__ == "__main__":
    main()
