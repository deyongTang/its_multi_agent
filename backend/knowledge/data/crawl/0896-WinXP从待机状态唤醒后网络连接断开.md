# 知识库 896

## 标题
WinXP从待机状态唤醒后网络连接断开

## 问题描述
WinXP从待机状态唤醒后网络连接断开。

## 分类
主类别: 网络问题
子类别: 唤醒断网

## 关键词
待机, 唤醒, 网络, 断开

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**问题描述：**

WINXP从[待机](http://iknow.lenovo.com/knowledgeDetail.html?knowledgeId=17402)状态唤醒后网络会断开连接，如何解决？

**解决方案：**

禁用[网卡](http://iknow.lenovo.com/knowledgeDetail.html?knowledgeId=17366)的[电源管理](http://iknow.lenovo.com/knowledgeDetail.html?knowledgeId=17688)，具体操作如下：

1、在"我的电脑"上单击鼠标右键，选择"属性"；

2、选择"[硬件](http://iknow.lenovo.com/knowledgeDetail.html?knowledgeId=17962)" -> "[设备管理器](http://iknow.lenovo.com/knowledgeDetail.html?knowledgeId=17549)"；

3、在设备管理器中找到网卡并双击；

4、选择"电源管理",将"允许计算机关闭这个设备以节约电源"前的小钩取消；

5、单击"确定"。  
 

![1.bmp](/upload/image/20160306/1457258008837372.bmp "1457258008837372.bmp")

<!-- 文档主题：WinXP从待机状态唤醒后网络连接断开 (知识库库编号: 896) -->