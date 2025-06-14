from ErisPulse import sdk
import aiohttp
from typing import Optional, Dict, Any, Union


class Main:
    def __init__(self):
        self.WeatherConfig = sdk.env.get("Weather", {})
        self.sdk = sdk
        self.logger = sdk.logger
        # 定义开放的源列表
        allow_source = [
            "lolimi"
        ]
        # 读取配置
        self.source = self.WeatherConfig.get("source", None)
        self.adapter = self.WeatherConfig.get("adapter", None)
        self.text = self.WeatherConfig.get("text", None)
        self.type = self.WeatherConfig.get("type", "md")
        
        if not self.adapter or not self.text:
            self.logger.error("必要参数：adapter或text缺失")
            return
        
        if self.source is None:
            self.logger.warning("来源未设置，将使用默认源")
            self.source = "lolimi"
        elif self.source not in allow_source:
            self.logger.error(f"尚未适配的来源：{self.source}")
            return

    async def async_get(
        self, 
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        return_type: str = 'json'  # 'json', 'text', 'bytes'
    ) -> Union[Dict[str, Any], str, bytes]:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # 如果状态码不是200，抛出异常
                
                if return_type == 'json':
                    return await response.json()
                elif return_type == 'text':
                    return await response.text()
                elif return_type == 'bytes':
                    return await response.read()
                else:
                    raise ValueError(f"不支持的返回类型: {return_type}")

    async def get(self, city):
        if self.source == "lolimi":
            url = "https://api.lolimi.cn/API/weather/api.php"
            params = {"city": city}
        
        try:
            weather_json = await self.async_get(url, params=params, return_type='json')
        except Exception as e:
            self.logger.error(f"API请求错误：{e}")
            return None
        
        current_code = {
            "lolimi": 1
        }
        current_key = {
            "lolimi": "text"
        }
        
        if weather_json.get('code') != current_code.get(self.source, 1):
            error_msg = weather_json.get(current_key.get(self.source, "text"), "未知错误")
            self.logger.error(f"{self.source}的API响应出错：{error_msg}({weather_json.get('code')})")
            return None
        
        self.logger.info(f"成功获取{city}的天气信息")
        
        if self.type == "md":
            msg = f"""
#### 🌦️ {weather_json["data"]["current"]["city"]}当前天气 ({weather_json["data"]["current"]["date"]} {weather_json["data"]["current"]["time"]})

##### 基本信息
- **城市**: {weather_json["data"]["current"]["city"]} ({weather_json["data"]["current"]["cityEnglish"]})
- **天气状况**: {weather_json["data"]["current"]["weather"]} ({weather_json["data"]["current"]["weatherEnglish"]})
- **温度**: {weather_json["data"]["current"]["temp"]}°C ({weather_json["data"]["current"]["fahrenheit"]}°F)
- **空气质量**: PM2.5 {weather_json["data"]["current"]["air_pm25"]}

##### 环境指标
- **湿度**: {weather_json["data"]["current"]["humidity"]}
- **风速**: {weather_json["data"]["current"]["windSpeed"]} {weather_json["data"]["current"]["wind"]}
- **能见度**: {weather_json["data"]["current"]["visibility"]}

##### 生活指数
- **体感**: {next(item["tips"] for item in weather_json["data"]["living"] if item["name"] == "舒适度指数")}
- **穿衣建议**: {next(item["tips"] for item in weather_json["data"]["living"] if item["name"] == "穿衣指数")}
- **紫外线**: {next(item["tips"] for item in weather_json["data"]["living"] if item["name"] == "紫外线强度指数")}

> 最后更新时间: {weather_json["data"]["current"]["date"]} {weather_json["data"]["current"]["time"]}
            """
            return msg
        elif self.type == "text":
            msg = f"""
🌦 {weather_json["data"]["current"]["city"]}当前天气  
🕒 {weather_json["data"]["current"]["date"]} {weather_json["data"]["current"]["time"]}  

🌡️ 温度: {weather_json["data"]["current"]["temp"]}°C ({weather_json["data"]["current"]["fahrenheit"]}°F)  
☁️ 天气: {weather_json["data"]["current"]["weather"]}  
💧 湿度: {weather_json["data"]["current"]["humidity"]}  
🌬️ 风力: {weather_json["data"]["current"]["windSpeed"]} {weather_json["data"]["current"]["wind"]}  
👀 能见度: {weather_json["data"]["current"]["visibility"]}  
🍃 空气质量: PM2.5 {weather_json["data"]["current"]["air_pm25"]} (指数{weather_json["data"]["current"]["air"]})  

📌 生活提示:  
• {next(item["tips"] for item in weather_json["data"]["living"] if item["name"] == "穿衣指数")}  
• {next(item["tips"] for item in weather_json["data"]["living"] if item["name"] == "雨伞指数")}  
• {next(item["tips"] for item in weather_json["data"]["living"] if item["name"] == "紫外线强度指数")}  

⚠️ 预警信息: {weather_json["data"]["warning"]["warning"] if weather_json["data"].get("warning") else "暂无预警"}  

最后更新: {weather_json["data"]["current"]["time"]}  
            """
            return msg
        else:
            self.logger.error("参数传递错误：type仅能为md或text")
            return None
