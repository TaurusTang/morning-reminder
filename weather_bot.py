import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# --- 配置（从 GitHub Secrets 读取） ---
API_KEY = os.environ.get("QWEATHER_API_KEY")
CITY_ID = os.environ.get("CITY_ID")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

def get_weather_data():
    """获取今日天气预报和实时空气质量"""
    weather_url = f"https://devapi.qweather.com/v7/weather/3d?location={CITY_ID}&key={API_KEY}"
    air_url = f"https://devapi.qweather.com/v7/air/now?location={CITY_ID}&key={API_KEY}"
    
    try:
        wea_res = requests.get(weather_url).json()
        air_res = requests.get(air_url).json()
        
        # 增加打印调试信息，方便在 GitHub Logs 查看
        print(f"Weather API Response Code: {wea_res.get('code')}")
        print(f"Air API Response Code: {air_res.get('code')}")
        
        if wea_res['code'] == '200' and air_res['code'] == '200':
            today = wea_res['daily'][0]
            return {
                "tempMax": int(today['tempMax']),
                "tempMin": int(today['tempMin']),
                "textDay": today['textDay'],
                "aqi": int(air_res['now']['aqi'])
            }
        else:
            print(f"API调用异常: 天气{wea_res.get('code')}, 空气{air_res.get('code')}")
    except Exception as e:
        print(f"数据解析失败: {e}")
    return None

def send_email(content):
    """发送邮件逻辑"""
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header("天气生活助手", 'utf-8')
    message['To'] = Header("Student Tang", 'utf-8')
    message['Subject'] = Header("📢 今日出行贴心提醒", 'utf-8')

    try:
        # 自动识别常见 SMTP 服务器
        smtp_server = "smtp.gmail.com"
        if EMAIL_SENDER and "qq.com" in EMAIL_SENDER.lower(): 
            smtp_server = "smtp.qq.com"
        elif EMAIL_SENDER and "163.com" in EMAIL_SENDER.lower(): 
            smtp_server = "smtp.163.com"
        
        # 使用端口 465 (SSL)
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], message.as_string())
        server.quit()
        print("邮件推送成功！")
    except Exception as e:
        print(f"邮件推送失败，错误详情: {e}")

def main():
    data = get_weather_data()
    if not data:
        print("未能获取到完整数据，跳过本次提醒。")
        return

    # 打印当前获取到的数据，方便调试
    print(f"当前数据: AQI={data['aqi']}, 最高温={data['tempMax']}, 最低温={data['tempMin']}, 天气={data['textDay']}")

    tips = []
    
    # 1. 监测温差
    temp_diff = data['tempMax'] - data['tempMin']
    if temp_diff >= 10:
        tips.append(f"🌡️ 温差预警：今日温差高达 {temp_diff}°C ({data['tempMin']}°C ~ {data['tempMax']}°C)，早晚记得添衣。")

    # 2. 监测空气质量
    if data['aqi'] > 100:
        tips.append(f"😷 空气质量指数(AQI)为 {data['aqi']}，质量较差，出门建议佩戴口罩。")
    
    # 3. 监测雨雪
    if "雨" in data['textDay'] or "雪" in data['textDay']:
        tips.append(f"☔ 今日预报有 {data['textDay']}，出门别忘了带伞哦。")

    # 执行发送
    if tips:
        full_content = "Student Tang，你好！今日份的出行提醒：\n\n" + "\n".join(tips)
        send_email(full_content)
    else:
        # 如果你想在测试阶段无论如何都收到邮件，可以取消下面这一行的注释
        send_email("今天天气很好，无需戴口罩或带伞，温差也正常。祝心情愉快！")
        print("今日无异常提醒指标。")

if __name__ == "__main__":
    main()
