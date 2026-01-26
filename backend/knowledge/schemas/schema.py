from pydantic import BaseModel


class UploadResponse(BaseModel):
    """
     文件上传的响应数据模型
    """
    status:str  # 响应状态
    message:str # 响应的消息内容
    file_name:str # 上传的文件名
    chunks_added:int # 上传文档切分之后的文档块数量


class QueryRequest(BaseModel):
    """
    知识库查询的请求数据模型
    """
    question: str  # 用户提出的问题


class QueryResponse(BaseModel):
    """
    知识库查询的响应数据模型
    """
    question: str  # 用户提出的问题
    answer: str  # 生成的答案


