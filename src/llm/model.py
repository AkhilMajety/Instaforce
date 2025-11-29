# import os
# from typing import List, Dict, Any
# import openai

# from dotenv import load_dotenv
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# print(OPENAI_API_KEY)
# if not OPENAI_API_KEY:
#     raise EnvironmentError('Please set OPENAI_API_KEY env var')


# openai.api_key = OPENAI_API_KEY


# class LLMModel:
#     def __init__(self, model: str = 'gpt-4o-mini'):
#         self.model = model


#     def invoke(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
#     # messages is a list of dicts with 'role' and 'content'
#         resp = openai.ChatCompletion.create(
#         model=self.model,
#         messages=messages,
#         temperature=temperature,
#         max_tokens=1500
#         )
#         return resp.choices[0].essage['content']


# from langchain_openai import ChatOpenAI
# import os
# from dotenv import load_dotenv

# class LLMModel:
#     # def __init__(self):
#     #     load_dotenv()
#     #     self.openai_api_key = os.getenv("OPENAI_API_KEY")
#     #     if not self.openai_api_key:
#     #         raise EnvironmentError("Please set OPENAI_API_KEY in your environment variables or .env file.")

#     def invoke(self):
#         load_dotenv()
#         api_key = os.getenv("OPENAI_API_KEY")
#         try:
#             print(self.openai_api_key)
#             llm = ChatOpenAI(model="gpt-4o", openai_api_key=api_key)
            
#             return llm
#         except Exception as e:
#             raise ValueError(f"Error occurred with exception: {e}")


from langchain_openai import ChatOpenAI
import os 
from dotenv import load_dotenv

class LLMModel:
    def __init__(self):
        load_dotenv()


    def get_llm(self):
        try:
            os.environ["OPENAI_API_KEY"]=self.op_api_key=os.getenv("OPENAI_API_KEY")
            llm = ChatOpenAI(model="gpt-4o", openai_api_key=self.op_api_key)
            return llm
        except Exception as e:
            raise ValueError("Error occurred with exception : {e}")