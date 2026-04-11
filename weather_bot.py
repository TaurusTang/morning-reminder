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
    # 3天预报接口（包含当日最高温和最低温）
    weather_url = f"https://devapi.qweather.com/v7/weather/3d?location={CITY_ID}&key={API_KEY}"
    # 实时空气质量接口
    air_url = f"https://devapi.qweather.com/v7/air/now?location={CITY_ID}&key={API_KEY}"
    
    try:
        wea_res = requests.get(weather_url).json()
        air_res = requests.get(air_url).json()
        
        if wea_res['code'] == '200' and air_res['code'] == '200':
            today = wea_res['daily'][0]
            return {
                "tempMax": int(today['tempMax']),
                "tempMin": int(today['tempMin']),
                "textDay": today['textDay'],
                "aqi": int(air_res['now']['aqi'])
            }
    except Exception as e:
        print(f"数据抓取请求失败: {e}")
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
        if "qq.com" in EMAIL_SENDER: smtp_server = "smtp.qq.com"
        elif "163.com" in EMAIL_SENDER: smtp_server = "smtp.163.com"
        
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
        print("无法获取天气数据，请检查 API_KEY 或网络。")
        return

    tips = []
    
    # 1. 监测温差 (最高温 - 最低温)
    temp_diff = data['tempMax'] - data['tempMin']
    if temp_diff >= 10:
        tips.append(f"🌡️ 温差预警：今日温差高达 {temp_diff}°C ({data['tempMin']}°C ~ {data['tempMax']}°C)，早晚记得添衣，谨防感冒。")

    # 2. 监测空气质量
    if data['aqi'] > 100:
        tips.append(f"😷 空气质量指数(AQI)为 {data['aqi']}，质量较差，出门建议佩戴口罩。")
    
    # 3. 监测雨雪
    if "雨" in data['textDay'] or "雪" in data['textDay']:
        tips.append(f"☔ 今日预报有 {data['textDay']}，出门别忘了带伞哦。")

    # 执行发送
    if tips:
        full_content = "Student Tang，你好！今日份的出行提醒：\n\n" + "\n".join(tips)
        print("准备发送提醒：\n", full_content)
        send_email(full_content)
    else:
        print("今天天气和空气质量都很棒，祝心情愉快！")

if __name__ == "__main__":
    main()
