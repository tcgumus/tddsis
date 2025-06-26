import openai
from eddie.weather import get_weather
from eddie.config import API_KEY


def chatgpt_cevap(metin):
    """Kullanıcının metnini alır, function calling yapar ve yanıt döndürür."""
    functions = [
        {
            "name": "get_weather",
            "description": "Şehir ve gün bilgisine göre hava durumu getirir",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Hava durumu alınacak şehir, örneğin 'Ankara'"
                    },
                    "day_offset": {
                        "type": "integer",
                        "description": "Kaç gün sonranın bilgisi isteniyor: 0 = bugün, 1 = yarın, 2 = 2 gün sonra"
                    }
                },
                "required": ["city", "day_offset"]
            }
        }
    ]
    
    client = openai.OpenAI(api_key=API_KEY)

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": metin}],
        functions=functions,
        function_call="auto"
    )

    choice = response.choices[0].message

    if choice.function_call:
        function_name = choice.function_call.name
        function_args = eval(choice.function_call.arguments)

        if function_name == "get_weather":
            city = function_args.get("city")
            day_offset = function_args.get("day_offset", 0)
            return get_weather(city, day_offset)

    elif choice.content:
        return choice.content

    return "ChatGPT'den geçerli bir yanıt alınamadı."

    
